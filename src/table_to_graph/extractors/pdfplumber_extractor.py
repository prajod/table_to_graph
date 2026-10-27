import logging
from pathlib import Path
from typing import Any

import pdfplumber

from table_to_graph.extractors import extractor_registry
from table_to_graph.extractors.tatr_extractor import (
    HAS_VISION,
    extract_with_tatr,
    is_staggered_extraction,
)
from table_to_graph.models import TableData, TableMetadata

log = logging.getLogger(__name__)


@extractor_registry.decorator("pdfplumber")
class PdfPlumberExtractor:
    """Extractor for text-based PDFs using pdfplumber.
    Conforms to the TableExtractor Protocol.
    """

    def __init__(
        self,
        table_settings: dict[str, Any] | None = None,
        max_file_size_mb: int = 50,
        max_pages: int = 1000,
    ):
        self.table_settings = table_settings or {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
        }
        self.max_file_size_mb = max_file_size_mb
        self.max_pages = max_pages

    def can_handle(self, source: Any) -> bool:
        if isinstance(source, (str, Path)) and str(source).lower().endswith(".pdf"):
            return True
        return bool(hasattr(source, "pages") and hasattr(source, "extract_tables"))

    def extract(self, source: Any) -> list[TableData]:
        if not self.can_handle(source):
            raise ValueError("Unsupported source format for PdfPlumberExtractor")

        if isinstance(source, (str, Path)):
            import os

            file_size_mb = os.path.getsize(source) / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                raise ValueError(
                    f"File size {file_size_mb:.2f}MB exceeds the maximum allowed size of {self.max_file_size_mb}MB to prevent DoS."
                )

            with pdfplumber.open(source) as pdf:
                return self._extract_from_pdf(pdf, str(source))
        else:
            return self._extract_from_pdf(source, "pdf_object")

    def extract_from_pages(self, source: Any, pages: list[int]) -> list[TableData]:
        """Extract tables only from the specified page indices (0-indexed)."""
        if isinstance(source, (str, Path)):
            with pdfplumber.open(source) as pdf:
                return self._extract_from_pdf(pdf, str(source), page_indices=pages)
        else:
            return self._extract_from_pdf(source, "pdf_object", page_indices=pages)

    def _extract_from_pdf(
        self, pdf: Any, source_name: str, page_indices: list[int] | None = None
    ) -> list[TableData]:
        if len(pdf.pages) > self.max_pages:
            raise ValueError(
                f"PDF contains {len(pdf.pages)} pages, exceeding the maximum allowed {self.max_pages} pages to prevent memory exhaustion."
            )

        tables: list[TableData] = []

        for idx, page in enumerate(pdf.pages):
            if page_indices is not None and idx not in page_indices:
                continue

            page_tables = page.find_tables(self.table_settings)

            for table_idx, table_obj in enumerate(page_tables):
                raw_data = table_obj.extract()
                if not raw_data:
                    continue

                num_headers = self._detect_header_rows(raw_data)
                headers = raw_data[:num_headers]
                rows = raw_data[num_headers:]

                bbox = table_obj.bbox

                # Extract surrounding text (context) for this table
                context_text = ""
                page_words = page.extract_words()
                if page_words and bbox:
                    above_words = [w["text"] for w in page_words if w["bottom"] <= bbox[1]]
                    below_words = [w["text"] for w in page_words if w["top"] >= bbox[3]]

                    context_parts = []
                    if above_words:
                        context_parts.append(" ".join(above_words[-50:]))
                    if below_words:
                        context_parts.append(" ".join(below_words[:50]))

                    context_text = " | ".join(context_parts)

                metadata = TableMetadata(
                    source_file=source_name,
                    page_number=idx + 1,  # 1-indexed for users
                    table_index=table_idx,
                    bbox=bbox,
                    extraction_method="pdfplumber",
                    context=context_text,
                )

                table = TableData(headers=headers, rows=rows, metadata=metadata)

                # If staggered header pattern detected and vision is available,
                # re-extract using TATR for correct span reconstruction.
                # source_name is a real file path only when extract() was called
                # with a str/Path — "pdf_object" is the sentinel for in-memory PDFs.
                if source_name != "pdf_object" and Path(source_name).exists():
                    table = self._maybe_refine_with_tatr(table, source_name, idx, page, table_idx)

                tables.append(table)

        return self._merge_continuations(tables)

    def _maybe_refine_with_tatr(
        self,
        table: TableData,
        pdf_path: str,
        page_idx: int,
        pdfplumber_page: Any,
        table_idx: int,
    ) -> TableData:
        """Re-extract using TATR if pdfplumber output looks like a staggered failure.

        Falls back silently to the original pdfplumber result if:
        - table-to-graph[vision] is not installed
        - TATR returns no detections
        - Any exception occurs during inference
        """
        if not is_staggered_extraction(table):
            return table

        if not HAS_VISION:
            log.warning(
                "[TATR] Staggered header detected in %s (Table %s), but vision "
                "dependencies are missing. Falling back to pdfplumber.",
                pdf_path,
                table_idx,
            )
            return table

        if table.metadata.bbox is None:
            return table

        log.info(
            "[TATR] Staggered header detected in %s (Table %s). Running Table Transformer.",
            pdf_path,
            table_idx,
        )
        try:
            refined = extract_with_tatr(
                pdf_path=pdf_path,
                page_idx=page_idx,
                table_bbox=table.metadata.bbox,
                pdfplumber_page=pdfplumber_page,
                table_idx=table_idx,
            )
            if refined is not None and refined.rows:
                refined.metadata.source_file = table.metadata.source_file
                refined.metadata.page_number = table.metadata.page_number
                refined.metadata.bbox = table.metadata.bbox
                if hasattr(table.metadata, "context"):
                    refined.metadata.context = table.metadata.context
                log.info("[TATR] Successfully refined table structure.")
                return refined
            else:
                log.warning(
                    "[TATR] Vision extraction returned no rows. Falling back to pdfplumber."
                )
        except Exception as e:
            log.warning("[TATR] Vision extraction failed. Falling back to pdfplumber.")
            log.debug("[TATR] Exception detail: %s", e, exc_info=True)  # only shown with -vv

        return table

    def _merge_continuations(self, tables: list[TableData]) -> list[TableData]:
        if not tables:
            return tables

        merged: list[TableData] = [tables[0]]

        for curr in tables[1:]:
            prev = merged[-1]

            # Continuation criteria:
            # 1. On sequential pages
            # 2. Same number of columns
            is_sequential = (
                curr.metadata.page_number is not None
                and prev.metadata.page_number is not None
                and curr.metadata.page_number == prev.metadata.page_number + 1
            )

            num_cols_prev = (
                len(prev.headers[0]) if prev.headers else (len(prev.rows[0]) if prev.rows else 0)
            )
            num_cols_curr = (
                len(curr.headers[0]) if curr.headers else (len(curr.rows[0]) if curr.rows else 0)
            )

            same_cols = num_cols_prev == num_cols_curr and num_cols_prev > 0

            if is_sequential and same_cols:
                # Check if headers are repeated
                headers_match = prev.headers and curr.headers and prev.headers == curr.headers

                # Check if the previous table was physically cut off at the bottom of the page.
                # Standard A4/Letter page height is ~792-842 pts. If the bottom of the table
                # is > 700 pts, it was likely forced to break.
                was_cut_off = prev.metadata.bbox is not None and prev.metadata.bbox[3] > 700

                if headers_match:
                    # Append just the data rows
                    prev.rows.extend(curr.rows)
                    # Update metadata so the NEXT page in the chain can check `is_sequential` correctly
                    prev.metadata.page_number = curr.metadata.page_number
                    prev.metadata.bbox = curr.metadata.bbox
                elif was_cut_off:
                    # The table was cut off, and headers didn't match. This means the new page
                    # did NOT repeat the headers. Treat the top row(s) of `curr` as data.
                    prev.rows.extend(curr.headers)
                    prev.rows.extend(curr.rows)
                    # Update metadata so the NEXT page in the chain can check `is_sequential` correctly
                    prev.metadata.page_number = curr.metadata.page_number
                    prev.metadata.bbox = curr.metadata.bbox
                else:
                    # If headers don't match and the table wasn't cut off, they are distinct tables.
                    merged.append(curr)
            else:
                merged.append(curr)

        return merged

    @staticmethod
    def _detect_header_rows(table: list[list[str | None]]) -> int:
        """Heuristic to detect how many rows are headers.
        Supports multi-level headers by checking for empty leading cells or sub-header keywords.
        """
        if not table:
            return 0

        header_count = 1  # Always assume at least 1 header row

        # Check up to 3 rows (we rarely see >3 levels of headers)
        for i in range(1, min(4, len(table))):
            row = table[i]

            # If the row starts with an empty string, it's very likely a sub-header
            # E.g. [["Category", "2023", "2024"], ["", "Q1", "Q1"]]
            if not row or row[0] is None or str(row[0]).strip() == "":
                header_count += 1
                continue

            # If the row has "From" / "To" in the first cell, it's likely a sub-header (Option A)
            first_cell = str(row[0]).strip().lower()
            if first_cell in ("from", "to"):
                header_count += 1
                continue

            # Otherwise, it's a data row, stop looking for headers
            break

        return header_count
