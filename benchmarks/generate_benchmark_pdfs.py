from pathlib import Path

from fpdf import FPDF

from benchmarks.benchmark_retrieval import create_benchmark_corpus
from table_to_graph.classifiers.heuristic_classifier import HeuristicTableClassifier
from table_to_graph.models import TableData


class BenchmarkPDF(FPDF):
    current_archetype: str = "Unknown"

    def header(self):
        self.set_font("helvetica", "B", 12)
        self.cell(
            0, 10, f"Table Type: {self.current_archetype}", align="C", new_x="LMARGIN", new_y="NEXT"
        )

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def render_table(pdf: FPDF, table: TableData, title: str, repeat_headers: bool = True):
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")

    def _draw_headers():
        pdf.set_fill_color(220, 220, 220)
        pdf.set_font("helvetica", "B", 9)
        if table.headers:
            for header_row in table.headers:
                width = pdf.epw / max(len(header_row), 1)
                for cell in header_row:
                    text = str(cell)[:40].encode("latin-1", "replace").decode("latin-1")
                    pdf.cell(width, 8, text, border=1, fill=True, align="C")
                pdf.ln()

    # Initial headers
    _draw_headers()

    # Render rows
    pdf.set_font("helvetica", "", 9)
    pdf.set_fill_color(255, 255, 255)
    row_height = 8

    for row in table.rows:
        # Check if row fits on current page (with margin buffer)
        if pdf.get_y() + row_height > pdf.page_break_trigger:
            pdf.add_page()
            if repeat_headers:
                _draw_headers()
                pdf.set_font("helvetica", "", 9)
                pdf.set_fill_color(255, 255, 255)

        width = pdf.epw / max(len(row), 1)
        for cell in row:
            text = str(cell)[:40].encode("latin-1", "replace").decode("latin-1")
            pdf.cell(width, row_height, text, border=1, fill=False, align="C")
        pdf.ln()
    pdf.ln(10)


def render_staggered_alloy_table(pdf: FPDF):
    """Renders the exact staggered alloy mix matrix from Excel with two 'from' and shared 'to'."""
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, "from row shows the copper mix", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "from column shows the tin mix", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # 10 columns
    grid = [
        ["", "", "from", "36.5", "50.0", "60.0", "70.0", "80.0", "90.0", "100.0"],
        ["", "to", "", "50.0", "60.0", "70.0", "80.0", "90.0", "100.0", "110.0"],
        ["from", "", "", "", "", "", "", "", "", ""],
        ["10", "20", "", "17.44", "22.50", "28.10", "31.05", "34.20", "37.50", "41.00"],
        ["20", "30", "", "19.80", "25.30", "31.20", "35.60", "39.10", "42.80", "46.50"],
        ["30", "40", "", "22.10", "28.40", "34.50", "40.10", "44.00", "48.10", "52.30"],
        ["40", "50", "", "24.50", "31.20", "37.80", "43.90", "48.20", "52.70", "57.40"],
        ["50", "60", "", "27.00", "34.10", "41.00", "47.50", "52.10", "56.80", "61.90"],
        ["60", "70", "", "29.80", "37.20", "44.50", "51.20", "56.30", "61.20", "66.50"],
    ]

    col_width = pdf.epw / len(grid[0])
    pdf.set_font("helvetica", "", 9)
    for r_idx, row in enumerate(grid):
        for c_idx, cell in enumerate(row):
            if cell in ("from", "to"):
                pdf.set_font("helvetica", "B", 9)
                pdf.set_fill_color(240, 240, 240)
                pdf.cell(col_width, 7, cell, border=1, fill=True, align="C")
                pdf.set_font("helvetica", "", 9)
            elif r_idx < 2 and cell or c_idx < 2 and cell:  # Column header numbers
                pdf.set_font("helvetica", "B", 9)
                pdf.set_fill_color(245, 245, 245)
                pdf.cell(col_width, 7, cell, border=1, fill=True, align="C")
                pdf.set_font("helvetica", "", 9)
            else:
                pdf.cell(col_width, 7, cell, border=1, fill=False, align="C")
        pdf.ln()

    pdf.ln(3)
    pdf.set_font("helvetica", "I", 10)
    pdf.cell(0, 6, "For part creation", new_x="LMARGIN", new_y="NEXT")


def generate_all(output_dir: Path | None = None, *, force: bool = False) -> list[Path]:
    """Return the benchmark PDF corpus, generating only missing files by default."""
    # Split into groups
    groups = [
        (
            "benchmark_tables_1.pdf",
            [
                "server_specs",
                "clinical_patient",
                "cloud_comparison",
                "model_benchmarks",
                "financial_quarters",
                "server_telemetry",
            ],
        ),
        (
            "benchmark_tables_2.pdf",
            ["org_chart", "product_taxonomy", "flight_costs", "asset_correlation"],
        ),
        ("benchmark_tables_3.pdf", ["employee_projects", "regional_sales_pivot"]),
        (
            "benchmark_tables_4.pdf",
            [
                "temperature_map_option_a",
                "income_tax_brackets_option_a",
                "logistics_shipping_option_a",
                "network_latency_sla_option_a",
                "regional_property_values_option_a",
                "chemical_yield_option_a",
            ],
        ),
        (
            "benchmark_tables_5.pdf",
            [
                "long_server_specs",
                "long_sales_data",
                "long_employee_list",
                "long_flight_costs",
                "long_regional_sales",
            ],
        ),
    ]

    out_dir = output_dir or Path(__file__).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    staggered_path = out_dir / "benchmark_staggered_alloy_table.pdf"
    expected_paths = [out_dir / filename for filename, _ in groups] + [staggered_path]

    if not force and all(path.exists() for path in expected_paths):
        for path in expected_paths:
            print(f"Reusing benchmark PDF: {path}")
        return expected_paths

    corpus = create_benchmark_corpus()
    generated_paths: list[Path] = []

    classifier = HeuristicTableClassifier()

    for filename, table_names in groups:
        out_path = out_dir / filename
        if out_path.exists() and not force:
            generated_paths.append(out_path)
            print(f"Reusing benchmark PDF: {out_path}")
            continue

        pdf = BenchmarkPDF()

        for name in table_names:
            if name in corpus:
                table_data = corpus[name]
                # Dynamically set the header to the classified archetype name
                pdf.current_archetype = classifier.classify(table_data).table_type

                pdf.add_page()
                repeat = filename != "benchmark_tables_5.pdf"
                render_table(pdf, table_data, name, repeat_headers=repeat)

        pdf.output(str(out_path))
        generated_paths.append(out_path)
        print(f"Created benchmark PDF: {out_path}")

    # Generate standalone benchmark PDF with the exact staggered alloy table
    if staggered_path.exists() and not force:
        generated_paths.append(staggered_path)
        print(f"Reusing benchmark PDF: {staggered_path}")
    else:
        staggered_pdf = BenchmarkPDF()
        staggered_pdf.current_archetype = "Matrix"
        staggered_pdf.add_page()
        staggered_pdf.set_font("helvetica", "B", 12)
        staggered_pdf.cell(
            0,
            8,
            "Staggered Alloy Mix Matrix (Dual 'from', Shared 'to')",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        staggered_pdf.ln(2)
        render_staggered_alloy_table(staggered_pdf)
        staggered_pdf.output(str(staggered_path))
        generated_paths.append(staggered_path)
        print(f"Created benchmark PDF: {staggered_path}")

    return generated_paths


if __name__ == "__main__":
    generate_all()
