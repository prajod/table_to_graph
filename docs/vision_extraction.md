# Vision-Enhanced Extraction (`table-to-graph[vision]`)

By default, `table-to-graph` extracts tables from PDFs using **pdfplumber**, which reads
text layer primitives (lines, boxes, characters). This works for the vast majority of tables.

However, complex visual layouts — particularly **staggered multi-header tables** common in
engineering, manufacturing, and scientific documents — cannot be reconstructed from the raw
PDF text stream alone. For these tables, the library optionally uses Microsoft's
**Table Transformer (TATR)** model for structure-aware extraction.

---

## When Is Vision Mode Used?

Vision mode is a **silent fallback**, not the default. It activates automatically when:

1. `table-to-graph[vision]` is installed
2. pdfplumber detects a staggered header signal in a table:
   - The deepest header row has `"from"` or `"to"` in column 0, OR
   - More than 50% of data-column cells in the deepest header row are empty

When neither condition is met, pdfplumber extraction runs as normal with no overhead.

---

## Installation

### Standard (no vision model)
```bash
pip install table-to-graph
```

### With vision-enhanced extraction
```bash
pip install "table-to-graph[vision]"
```

This installs:
| Package | Purpose | Size |
|---|---|---|
| `torch` (CPU-only recommended) | TATR inference runtime | ~220 MB |
| `transformers` | HuggingFace model loader | ~5 MB |
| `PyMuPDF` | PDF page → image renderer (Windows-friendly) | ~15 MB |
| `Pillow` | Image processing | ~3 MB |

> **Windows note**: For CPU-only PyTorch (recommended unless you have a CUDA GPU), install
> with the CPU-only index to save ~1.5 GB of unnecessary CUDA libraries:
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> pip install "table-to-graph[vision]"
> ```

---

## HuggingFace Model Cache Configuration

The TATR model weights (~150 MB) are downloaded once on first use and cached locally.

Set these environment variables to control where models are stored:

```powershell
# Windows (PowerShell)
$env:HF_HOME = "D:\HuggingFace\HF_HOME"
$env:HUGGINGFACE_HUB_CACHE = "D:\HuggingFace\HF_CACHE"
```

```bash
# Linux / macOS
export HF_HOME=/path/to/hf_home
export HUGGINGFACE_HUB_CACHE=/path/to/hf_cache
```

**Or set them in code before importing table_to_graph:**
```python
import os
os.environ["HF_HOME"] = r"D:\HuggingFace\HF_HOME"
os.environ["HUGGINGFACE_HUB_CACHE"] = r"D:\HuggingFace\HF_CACHE"

from table_to_graph import extract_tables  # TATR will use the above paths
```

If these variables are not set, the default HuggingFace cache (`~/.cache/huggingface`) is used.

---

## Model Used

```
microsoft/table-transformer-structure-recognition-v1.1-all
```

- Architecture: DETR (Detection Transformer) fine-tuned on PubTables-1M
- Task: Table Structure Recognition (TSR) — detects rows, columns, and **spanning cells**
- Size: ~150 MB (downloaded once, cached)
- Inference: CPU: ~0.5–2 sec/table | GPU: ~50–100 ms/table

---

## Hardware Requirements

| Constraint | Requirement |
|---|---|
| RAM | ~800 MB at peak (well within 8 GB) |
| GPU | Not required (CPU inference supported) |
| OS | Windows, Linux, macOS — all supported |
| Python | ≥ 3.10 |

---

## How It Works

```
PDF → pdfplumber (text + bounding boxes)
         │
         ├─ Normal table? → Returns TableData directly
         │
         └─ Staggered header detected?
                  │
                  ├─ [vision] NOT installed → Returns pdfplumber result (best-effort)
                  │
                  └─ [vision] installed:
                       1. Render PDF page region → image (PyMuPDF, 150 DPI)
                       2. Run TATR TSR → rows, columns, spanning cells (bounding boxes)
                       3. Map pdfplumber words → TATR cells (coordinate overlap)
                       4. Reconstruct multi-level TableData with correct headers
                       5. Return refined TableData (extraction_method="tatr")
```

---

## What Is a Staggered Table?

A staggered table has two `"from"` axes sharing a single `"to"` axis, creating a
visual offset that standard PDF extractors cannot represent:

```
                    ← from (tin mix %) →
                from  36.5  50.0  60.0  70.0
            to        50.0  60.0  70.0  80.0
from  ↑  10   20       17.44  22.50  28.10  31.05
(Cu%) │  20   30       19.80  25.30  31.20  35.60
      │  30   40       22.10  28.40  34.50  40.10
      ↓  ...
                           For part creation
```

pdfplumber extracts this as a flat 10-column grid, losing the span structure.
TATR detects the visual merged cells and reconstructs the correct coordinate mapping.

---

## Usage — No Code Changes Required

Vision mode is transparent. The same `extract_tables()` API is used:

```python
import os
# Point to your local HuggingFace cache
os.environ["HF_HOME"] = r"D:\HuggingFace\HF_HOME"
os.environ["HUGGINGFACE_HUB_CACHE"] = r"D:\HuggingFace\HF_CACHE"

from table_to_graph import extract_tables

# Works the same whether [vision] is installed or not
# TATR activates automatically only for staggered tables
tables = extract_tables("engineering_specs.pdf", classify=True)
```

To check whether vision mode is active:
```python
from table_to_graph.extractors.tatr_extractor import HAS_VISION
print(f"Vision mode available: {HAS_VISION}")
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ImportError: table-to-graph[vision] dependencies not installed` | torch/transformers not installed | `pip install "table-to-graph[vision]"` |
| First run is slow (~30 sec) | TATR model downloading for the first time | Normal — subsequent runs are instant |
| TATR model re-downloading on every run | HF_HOME not set persistently | Set `HF_HOME` env var in your shell profile |
| GPU not being used | No CUDA-enabled GPU detected | Expected — CPU inference works fine |
| `extraction_method` still shows `"pdfplumber"` | Staggered heuristic not triggered | Table may not be staggered; check `is_staggered_extraction()` |
