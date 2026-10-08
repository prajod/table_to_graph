"""TATR (Table Transformer) extractor — vision-based PDF table extraction.

Uses Microsoft's table-transformer-structure-recognition model to detect
rows, columns, and spanning cells in rendered PDF page images. This enables
correct extraction of complex table layouts that confuse pdfplumber, such as
staggered "dual-from / shared-to" headers common in industrial and engineering
documents.

Installation:
    pip install "table-to-graph[vision]"

Custom HuggingFace cache (recommended to avoid re-downloading):
    Set environment variables before import:
        HF_HOME=D:\\HuggingFace\\HF_HOME
        HUGGINGFACE_HUB_CACHE=D:\\HuggingFace\\HF_CACHE

Model used:
    microsoft/table-transformer-structure-recognition-v1.1-all
    ~150 MB, downloaded once and cached.

Design:
    - Acts as a fallback extractor: only invoked when pdfplumber output is
      detected to be ambiguous (staggered headers heuristic).
    - Renders the PDF page to an image using PyMuPDF (fitz).
    - Crops the table region using pdfplumber's bounding box.
    - Runs TATR TSR to get rows, columns, and spanning cells.
    - Builds pdfplumber word-level text mapping via coordinate overlap.
    - Reconstructs a proper multi-level TableData with correct headers.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

from table_to_graph.models import TableData, TableMetadata

# ── HuggingFace cache path configuration ─────────────────────────────────────


def _configure_hf_cache() -> None:
    """Load HuggingFace cache paths from .env in the project root.

    Priority (highest to lowest):
        1. Already-set shell environment variables (e.g. CI / system-level)
        2. Values from .env file in the repository root
        3. HuggingFace default (~/.cache/huggingface)

    Uses python-dotenv if available; falls back to a minimal manual parser.
    The .env file is expected at the project root (two levels up from this file):
        <project_root>/.env
    """
    env_file = Path(__file__).resolve().parents[3] / ".env"
    if not env_file.exists():
        return

    # Try python-dotenv first (richer parsing, handles quotes / multiline)
    try:
        from dotenv import load_dotenv

        load_dotenv(
            dotenv_path=env_file, override=False
        )  # override=False: shell vars take priority
        return
    except ImportError:
        pass

    # Minimal fallback: parse KEY=VALUE lines manually
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # Only set if not already in environment (shell vars take priority)
            if key and key not in os.environ:
                os.environ[key] = value


_configure_hf_cache()


# ── Availability guard ────────────────────────────────────────────────────────


def _check_vision_dependencies() -> tuple[bool, str]:
    """Return (available, missing_packages_message)."""
    missing = []
    try:
        import torch  # noqa: F401
    except ImportError:
        missing.append("torch")
    try:
        import torchvision  # noqa: F401
    except ImportError:
        missing.append("torchvision")
    try:
        import transformers  # noqa: F401
    except ImportError:
        missing.append("transformers")
    try:
        import pypdfium2  # noqa: F401
    except ImportError:
        missing.append("pypdfium2")
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        missing.append("Pillow")

    if missing:
        return False, (
            f"table-to-graph[vision] dependencies not installed: {', '.join(missing)}.\n"
            'Install with:  pip install "table-to-graph[vision]"\n'
            "For CPU-only (recommended on Windows):\n"
            "  pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu\n"
            "  pip install transformers pypdfium2 Pillow"
        )
    return True, ""


HAS_VISION, _VISION_MISSING_MSG = _check_vision_dependencies()


# ── TATR Model constants ──────────────────────────────────────────────────────

_MODEL_ID = "microsoft/table-transformer-structure-recognition-v1.1-all"
_MODEL_REVISION = "7587a7ef111d9dcbf8ac695f1376ab7014340a0c"
_RENDER_DPI = 150  # Page render resolution (pixels per inch)
_SCORE_THRESHOLD = 0.5  # Minimum TATR confidence to accept a detected cell


# ── Lazy model loader ─────────────────────────────────────────────────────────

_model_cache: dict[str, Any] = {}


def _load_tatr_model() -> tuple[Any, Any]:
    """Load (and cache) the TATR model and feature extractor.

    Uses the HF_HOME / HUGGINGFACE_HUB_CACHE env vars for local caching.
    On first call: ~150 MB downloaded. Subsequent calls: instant from cache.

    Handles a compatibility issue with huggingface_hub >= 0.26 which enforces
    strict type validation: the TATR model's config.json has ``dilation: null``
    but the DetrConfig field expects ``bool``. We load the config as raw JSON,
    patch null → False, then pass the fixed config to from_pretrained.
    """
    if "model" not in _model_cache:
        import json

        import torch
        from huggingface_hub import hf_hub_download
        from transformers import AutoImageProcessor, DetrConfig, TableTransformerForObjectDetection

        processor = cast(Any, AutoImageProcessor).from_pretrained(
            _MODEL_ID, revision=_MODEL_REVISION
        )

        # Newer transformers requires size to have BOTH 'shortest_edge' AND 'longest_edge'.
        # The TATR preprocessor_config.json only sets 'longest_edge': 800, leaving
        # 'shortest_edge': None, which raises ValueError during image preprocessing.
        if hasattr(processor, "size") and isinstance(processor.size, dict):
            s = processor.size
            if s.get("longest_edge") is not None and s.get("shortest_edge") is None:
                processor.size = {
                    "shortest_edge": s["longest_edge"],
                    "longest_edge": s["longest_edge"],
                }

        # Load config.json as raw dict to patch null bool fields before
        # strict validation runs (huggingface_hub >= 0.26 regression)
        config_path = hf_hub_download(
            repo_id=_MODEL_ID, filename="config.json", revision=_MODEL_REVISION
        )
        with open(config_path, encoding="utf-8") as f:
            config_dict = json.load(f)

        # Patch any null fields that the config schema expects as bool
        _BOOL_FIELDS = ("dilation",)
        for field in _BOOL_FIELDS:
            if config_dict.get(field) is None:
                config_dict[field] = False

        config = DetrConfig(**config_dict)
        model: Any = cast(Any, TableTransformerForObjectDetection).from_pretrained(
            _MODEL_ID, config=config, revision=_MODEL_REVISION
        )
        model.eval()

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)

        _model_cache["processor"] = processor
        _model_cache["model"] = model
        _model_cache["device"] = device

    return _model_cache["model"], _model_cache["processor"]


# ── Coordinate utilities ─────────────────────────────────────────────────────


def _word_center_in_cell(cell_box: list[float], word: dict[str, Any]) -> bool:
    """Return True if the word's centre point lies inside the cell box.

    Using centre-point containment instead of IoU because table words are
    always much smaller than their cells, making IoU products systematically
    fall below any reasonable threshold.
    """
    cx = (word["x0"] + word["x1"]) / 2
    cy = (word["top"] + word["bottom"]) / 2
    return bool(cell_box[0] <= cx <= cell_box[2] and cell_box[1] <= cy <= cell_box[3])


# ── Staggered header detection heuristic ─────────────────────────────────────


def is_staggered_extraction(table: TableData) -> bool:
    """Return True if the pdfplumber extraction looks like a staggered table failure.

    Signals:
    - More than one header level exists
    - The deepest header row has >50% empty cells (excluding col 0)
    - OR col 0 of the deepest header contains "from" or "to"
    """
    if len(table.headers) < 2:
        return False

    deepest = table.headers[-1]
    if not deepest:
        return False

    # Col 0 sentinel
    col0_val = str(deepest[0]).strip().lower()
    if col0_val in ("from", "to"):
        return True

    # Empty ratio in data columns (skip col 0)
    data_cells = deepest[1:]
    if not data_cells:
        return False
    empty_count = sum(1 for c in data_cells if not str(c).strip())
    return (empty_count / len(data_cells)) > 0.5


# ── Core TATR extraction ──────────────────────────────────────────────────────


def _render_page_region(
    pdf_path: str, page_idx: int, bbox_pdf: tuple[float, float, float, float]
) -> Any:
    """Render a cropped region of a PDF page to a PIL Image using pypdfium2.

    Args:
        pdf_path: Path to the PDF file.
        page_idx: 0-indexed page number.
        bbox_pdf: pdfplumber bbox (x0, top, x1, bottom) in PDF points.

    Returns:
        PIL Image of the rendered table region.
    """
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(pdf_path)
    page = pdf[page_idx]

    # Render at _RENDER_DPI (PDF points are 1/72 of an inch)
    scale = _RENDER_DPI / 72.0
    bitmap = page.render(scale=scale)
    img = bitmap.to_pil()

    # Crop it based on the scaled bbox
    x0, top, x1, bottom = bbox_pdf

    crop_box = (int(x0 * scale), int(top * scale), int(x1 * scale), int(bottom * scale))

    return img.crop(crop_box)


def _run_tatr(image: Any) -> list[dict[str, Any]]:
    """Run TATR TSR on an image and return detected structure elements.

    Returns a list of dicts with keys: label, score, box (xyxy in pixels).
    """
    import torch

    model, processor = _load_tatr_model()
    device = _model_cache["device"]

    # Pass size explicitly — newer transformers requires both 'shortest_edge' AND
    # 'longest_edge', but the TATR preprocessor_config.json only sets 'longest_edge'.
    # Passing size here always overrides the stored SizeDict from the config file.
    inputs = processor(
        images=image,
        return_tensors="pt",
        size={"shortest_edge": 800, "longest_edge": 800},
    ).to(device)
    with torch.no_grad():
        outputs = model(**inputs)

    target_sizes = torch.tensor([image.size[::-1]])
    results = processor.post_process_object_detection(
        outputs, threshold=_SCORE_THRESHOLD, target_sizes=target_sizes
    )[0]

    id2label = model.config.id2label
    detections = []
    for score, label_id, box in zip(
        results["scores"].tolist(),
        results["labels"].tolist(),
        results["boxes"].tolist(),
    ):
        detections.append(
            {
                "label": id2label[label_id],
                "score": score,
                "box": box,  # [x0, y0, x1, y1] in image pixels
            }
        )
    return detections


def _build_table_from_tatr(
    detections: list[dict[str, Any]],
    pdfplumber_words: list[dict[str, Any]],
    image_w: int,
    image_h: int,
    pdf_bbox: tuple[float, float, float, float],
    source_name: str,
    page_number: int,
    table_idx: int,
) -> TableData | None:
    """Reconstruct a TableData from TATR detections and pdfplumber word positions.

    Strategy:
    1. Separate row/column/spanning-cell detections by label.
    2. Sort rows top-to-bottom, columns left-to-right.
    3. For each (row, col) grid cell, find pdfplumber words whose bbox overlaps.
    4. Use "table column header" labeled rows as headers, rest as data rows.
    """
    # Filter by label type
    rows_det = sorted(
        [d for d in detections if d["label"] == "table row"],
        key=lambda d: d["box"][1],  # top y
    )
    cols_det = sorted(
        [d for d in detections if d["label"] == "table column"],
        key=lambda d: d["box"][0],  # left x
    )
    header_rows_det = sorted(
        [d for d in detections if d["label"] == "table column header"],
        key=lambda d: d["box"][1],
    )

    if not rows_det or not cols_det:
        return None

    # Scale factor: image pixels → PDF point space
    pdf_x0, pdf_top, pdf_x1, pdf_bottom = pdf_bbox
    pdf_w = pdf_x1 - pdf_x0
    pdf_h = pdf_bottom - pdf_top
    scale_x = pdf_w / image_w
    scale_y = pdf_h / image_h

    def img_to_pdf_box(box: list[float]) -> list[float]:
        """Convert image pixel box to PDF point box (relative to page)."""
        return [
            pdf_x0 + box[0] * scale_x,
            pdf_top + box[1] * scale_y,
            pdf_x0 + box[2] * scale_x,
            pdf_top + box[3] * scale_y,
        ]

    # Build grid (use only 'table row' detections for the grid itself)
    all_row_dets = rows_det
    # rows_det is already sorted by top y

    # Assign words to grid cells
    grid: list[list[str]] = []
    for r_det in all_row_dets:
        row_pdf_box = img_to_pdf_box(r_det["box"])
        row_cells: list[str] = []
        for c_det in cols_det:
            col_pdf_box = img_to_pdf_box(c_det["box"])
            cell_box = [
                max(row_pdf_box[0], col_pdf_box[0]),
                max(row_pdf_box[1], col_pdf_box[1]),
                min(row_pdf_box[2], col_pdf_box[2]),
                min(row_pdf_box[3], col_pdf_box[3]),
            ]
            # Gather words whose centre point is inside this cell
            cell_words = []
            for w in pdfplumber_words:
                if _word_center_in_cell(cell_box, w):
                    cell_words.append(w["text"])
            row_cells.append(" ".join(cell_words).strip())
        grid.append(row_cells)

    if not grid:
        return None

    # Partition grid into headers vs data rows using 'table column header' bbox.
    # If a row's center y is inside any header bbox, it's a header row.
    headers = []
    data_rows = []

    # Precompute PDF bounding boxes for the header regions
    header_bboxes = [img_to_pdf_box(d["box"]) for d in header_rows_det]

    for r_det, row_cells in zip(all_row_dets, grid):
        row_pdf_box = img_to_pdf_box(r_det["box"])
        cy = (row_pdf_box[1] + row_pdf_box[3]) / 2

        is_header = False
        for h_box in header_bboxes:
            if h_box[1] <= cy <= h_box[3]:
                is_header = True
                break

        if is_header:
            headers.append(row_cells)
        else:
            data_rows.append(row_cells)

    if not headers:
        headers = [grid[0]] if grid else []
        data_rows = grid[1:] if grid else []

    return TableData(
        headers=headers,
        rows=data_rows,
        metadata=TableMetadata(
            source_file=source_name,
            page_number=page_number,
            table_index=table_idx,
            extraction_method="tatr",
        ),
    )


# ── Public API ────────────────────────────────────────────────────────────────


def extract_with_tatr(
    pdf_path: str,
    page_idx: int,
    table_bbox: tuple[float, float, float, float],
    pdfplumber_page: Any,
    table_idx: int,
) -> TableData | None:
    """Extract a single table using TATR structure recognition.

    Args:
        pdf_path: Path to the PDF file.
        page_idx: 0-indexed page number.
        table_bbox: pdfplumber bbox (x0, top, x1, bottom) for the table.
        pdfplumber_page: pdfplumber Page object (for word-level text extraction).
        table_idx: Table index on the page (for metadata).

    Returns:
        TableData with TATR-reconstructed headers, or None if detection failed.
    """
    if not HAS_VISION:
        raise ImportError(_VISION_MISSING_MSG)

    # Render the table region to an image
    image = _render_page_region(pdf_path, page_idx, table_bbox)
    image_w, image_h = image.size

    # Run TATR structure recognition
    detections = _run_tatr(image)

    # Get word-level text with coordinates from pdfplumber
    words = pdfplumber_page.extract_words(keep_blank_chars=False)

    # ── DEBUG: show word/detection alignment ──────────────────────────────────
    x0, top, _x1, _bottom = table_bbox
    pts_per_px = 72 / _RENDER_DPI
    print(
        f"  [TATR DEBUG] table_bbox={table_bbox}  image={image_w}x{image_h}px  "
        f"words={len(words)}  detections={len(detections)}"
    )
    if words:
        for w in words[:5]:
            print(
                f"    word '{w['text']}' @ ({w['x0']:.1f},{w['top']:.1f})-({w['x1']:.1f},{w['bottom']:.1f})"
            )
    else:
        print("    *** NO WORDS extracted by pdfplumber from this page!")
    rows_d = [d for d in detections if d["label"] == "table row"]
    cols_d = [d for d in detections if d["label"] == "table column"]
    if rows_d:
        rb = rows_d[0]["box"]
        print(
            f"    row[0] pixels=({rb[0]:.0f},{rb[1]:.0f})-({rb[2]:.0f},{rb[3]:.0f})  "
            f"-> pdf=({x0 + rb[0] * pts_per_px:.1f},{top + rb[1] * pts_per_px:.1f})-"
            f"({x0 + rb[2] * pts_per_px:.1f},{top + rb[3] * pts_per_px:.1f})"
        )
    if cols_d:
        cb = cols_d[0]["box"]
        print(
            f"    col[0] pixels=({cb[0]:.0f},{cb[1]:.0f})-({cb[2]:.0f},{cb[3]:.0f})  "
            f"-> pdf=({x0 + cb[0] * pts_per_px:.1f},{top + cb[1] * pts_per_px:.1f})-"
            f"({x0 + cb[2] * pts_per_px:.1f},{top + cb[3] * pts_per_px:.1f})"
        )
    # ─────────────────────────────────────────────────────────────────────────

    return _build_table_from_tatr(
        detections=detections,
        pdfplumber_words=words,
        image_w=image_w,
        image_h=image_h,
        pdf_bbox=table_bbox,
        source_name=pdf_path,
        page_number=page_idx + 1,
        table_idx=table_idx,
    )
