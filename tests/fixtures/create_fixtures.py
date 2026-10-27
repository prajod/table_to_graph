import argparse
from collections.abc import Sequence
from pathlib import Path

from fpdf import FPDF


def ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


class CustomPDF(FPDF):
    def header(self):
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, "table-to-graph fixture corpus", align="R")
        self.ln(6)

    def footer(self):
        self.set_y(-12)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def draw_diagram_flowchart(self, x: float, y: float, title: str = "System Architecture Flow"):
        """Draw a vector diagram to simulate document layout with diagrams."""
        self.set_draw_color(70, 130, 180)
        self.set_fill_color(240, 248, 255)
        self.set_line_width(0.4)

        # Title
        self.set_font("helvetica", "B", 10)
        self.set_text_color(30, 30, 30)
        self.text(x, y - 3, title)

        # Box 1
        self.rect(x, y, 40, 15, "DF")
        self.set_font("helvetica", size=8)
        self.text(x + 5, y + 9, "Ingestion Service")

        # Arrow 1 -> 2
        self.line(x + 40, y + 7.5, x + 55, y + 7.5)
        self.line(x + 52, y + 5.5, x + 55, y + 7.5)
        self.line(x + 52, y + 9.5, x + 55, y + 7.5)

        # Box 2
        self.set_fill_color(255, 245, 238)
        self.rect(x + 55, y, 45, 15, "DF")
        self.text(x + 58, y + 9, "Classifier Engine")

        # Arrow 2 -> 3
        self.line(x + 100, y + 7.5, x + 115, y + 7.5)
        self.line(x + 112, y + 5.5, x + 115, y + 7.5)
        self.line(x + 112, y + 9.5, x + 115, y + 7.5)

        # Box 3
        self.set_fill_color(240, 255, 240)
        self.rect(x + 115, y, 40, 15, "DF")
        self.text(x + 120, y + 9, "Graph Constructor")

    def draw_diagram_network(self, x: float, y: float, title: str = "Knowledge Graph Topology"):
        """Draw a vector node-link graph diagram."""
        self.set_font("helvetica", "B", 10)
        self.set_text_color(30, 30, 30)
        self.text(x, y - 3, title)

        self.set_draw_color(100, 100, 100)
        self.set_line_width(0.3)

        # Central node
        cx, cy = x + 40, y + 18
        nodes = [
            (cx - 25, cy - 10),
            (cx + 25, cy - 10),
            (cx - 20, cy + 12),
            (cx + 20, cy + 12),
            (cx + 50, cy + 5),
        ]

        for nx, ny in nodes:
            self.line(cx, cy, nx, ny)

        # Draw circle nodes
        self.set_fill_color(135, 206, 250)
        self.circle(cx, cy, 6, "DF")
        self.set_font("helvetica", "B", 7)
        self.text(cx - 3, cy + 2, "Hub")

        for i, (nx, ny) in enumerate(nodes):
            self.set_fill_color(255, 182, 193)
            self.circle(nx, ny, 5, "DF")
            self.set_font("helvetica", size=6)
            self.text(nx - 2, ny + 1.5, f"N{i + 1}")


def render_table(
    pdf: FPDF,
    headers: list[list[str]],
    rows: list[list[str]],
    col_widths: Sequence[float] | None = None,
    title: str = "",
):
    """Helper to render a table with borders and styling."""
    if title:
        pdf.set_font("helvetica", "B", 11)
        pdf.set_text_color(40, 40, 80)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    num_cols = len(headers[0]) if headers else (len(rows[0]) if rows else 1)
    if col_widths is None:
        avail_width = 190.0
        w = avail_width / num_cols
        col_widths = [w] * num_cols

    # Headers
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(20, 20, 20)
    pdf.set_fill_color(230, 235, 245)

    for h_row in headers:
        for idx, h_text in enumerate(h_row):
            w = col_widths[idx] if idx < len(col_widths) else 30
            pdf.cell(w, 7, str(h_text), border=1, fill=True)
        pdf.ln()

    # Rows
    pdf.set_font("helvetica", size=8.5)
    pdf.set_text_color(30, 30, 30)

    for r_idx, row in enumerate(rows):
        # Alternate subtle shading
        if r_idx % 2 == 1:
            pdf.set_fill_color(248, 250, 252)
            fill = True
        else:
            pdf.set_fill_color(255, 255, 255)
            fill = False

        for c_idx, cell_val in enumerate(row):
            w = col_widths[c_idx] if c_idx < len(col_widths) else 30
            pdf.cell(w, 6, str(cell_val if cell_val is not None else ""), border=1, fill=fill)
        pdf.ln()

    pdf.ln(5)


# ==============================================================================
# 1. GENERATE 7 ARCHETYPE-SPECIFIC PDFS (10 TABLES EACH)
# ==============================================================================


def generate_key_value_pdf(filepath: Path):
    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(
        0,
        10,
        "Archetype 01: Key-Value / Specification Tables Corpus",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_font("helvetica", size=10)
    pdf.multi_cell(
        0,
        6,
        "This document contains 10 distinct Key-Value style tables representing hardware specifications, system configurations, employee cards, and network properties.",
    )
    pdf.ln(4)

    tables = [
        (
            "Table 1: Server Compute Hardware Specs",
            [["Property", "Value"]],
            [
                ["CPU Model:", "AMD EPYC 9654"],
                ["Cores / Threads:", "96C / 192T"],
                ["Base Clock:", "2.4 GHz"],
                ["Max Boost:", "3.7 GHz"],
                ["L3 Cache:", "384 MB"],
            ],
            [60, 100],
        ),
        (
            "Table 2: Memory & Storage Configuration",
            [["Attribute", "Specification"]],
            [
                ["RAM Capacity:", "512 GB DDR5"],
                ["RAM Speed:", "4800 MT/s ECC"],
                ["Primary Storage:", "2x 1.92TB NVMe Gen4 (RAID-1)"],
                ["Secondary Storage:", "4x 7.68TB NVMe U.2"],
            ],
            [60, 100],
        ),
        (
            "Table 3: Network Interface Parameters",
            [["Parameter", "Configured Value"]],
            [
                ["Host IP:", "192.168.10.45"],
                ["Subnet Mask:", "255.255.255.0"],
                ["Gateway:", "192.168.10.1"],
                ["DNS 1:", "1.1.1.1"],
                ["MTU:", "9000 (Jumbo Frames)"],
            ],
            [55, 95],
        ),
        (
            "Table 4: Cloud VM Instance Settings",
            [["Setting", "Value"]],
            [
                ["Instance Type:", "c6g.4xlarge"],
                ["Architecture:", "ARM64 Graviton3"],
                ["vCPUs:", "16"],
                ["Memory (GiB):", "32.0"],
                ["EBS Bandwidth:", "Up to 10 Gbps"],
            ],
            [55, 95],
        ),
        (
            "Table 5: Database Connection Properties",
            [["Connection Key", "Value Detail"]],
            [
                ["Engine:", "PostgreSQL 16.2"],
                ["Port:", "5432"],
                ["Max Connections:", "500"],
                ["SSL Mode:", "verify-full"],
                ["Connection Timeout:", "30s"],
            ],
            [60, 95],
        ),
        (
            "Table 6: TLS Security Certificate Record",
            [["Field", "Value"]],
            [
                ["Common Name:", "*.antigravity.internal"],
                ["Issuer:", "DigiCert Global Root G2"],
                ["Valid From:", "2025-01-01"],
                ["Valid To:", "2027-01-01"],
                ["Key Length:", "RSA 4096-bit"],
            ],
            [55, 100],
        ),
        (
            "Table 7: Thermal and Power Profiles",
            [["Thermal Sensor", "Reading"]],
            [
                ["CPU Core Temp:", "42.5 deg C"],
                ["GPU Die Temp:", "55.1 deg C"],
                ["PSU 1 Load:", "420 Watts"],
                ["PSU 2 Load:", "415 Watts"],
                ["Fan Speed 1:", "4500 RPM"],
            ],
            [60, 90],
        ),
        (
            "Table 8: Container Resource Quotas",
            [["Resource Spec", "Limit / Request"]],
            [
                ["cpu_limit:", "4000m"],
                ["cpu_request:", "2000m"],
                ["memory_limit:", "8Gi"],
                ["memory_request:", "4Gi"],
                ["ephemeral_storage:", "20Gi"],
            ],
            [60, 90],
        ),
        (
            "Table 9: Camera Optical Specifications (3-column KV layout)",
            [["Feature Key", "Value", "Notes"]],
            [
                ["Sensor Type:", "Full Frame BSI CMOS", "35.9 x 23.9 mm"],
                ["Effective Pixels:", "45.7 Megapixels", "8256 x 5504"],
                ["ISO Range:", "64 - 25,600", "Expandable 32-102,400"],
                ["Autofocus:", "493-point phase detect", "90% frame coverage"],
                ["Video Mode:", "8K 60p RAW", "Internal 12-bit N-RAW"],
            ],
            [45, 55, 70],
        ),
        (
            "Table 10: User Profile Metadata",
            [["Profile Field", "Assigned Value"]],
            [
                ["User ID:", "USR-99281"],
                ["Full Name:", "Dr. Eleanor Vance"],
                ["Department:", "Quantum Algorithms"],
                ["Clearance Level:", "Top Secret / SCI"],
                ["Station Location:", "Sector 7G - Lab 4"],
            ],
            [55, 95],
        ),
    ]

    for title, headers, rows, widths in tables:
        render_table(pdf, headers, rows, widths, title)

    pdf.output(str(filepath))


def generate_comparison_pdf(filepath: Path):
    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Archetype 02: Comparison Tables Corpus", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=10)
    pdf.multi_cell(
        0,
        6,
        "This document contains 10 comparison tables evaluating products, tiers, algorithms, protocols, and vehicle benchmarks across multiple feature columns.",
    )
    pdf.ln(4)

    tables = [
        (
            "Table 1: Cloud Storage Service Comparison",
            [["Feature", "AWS S3", "Google Cloud Storage", "Azure Blob Storage"]],
            [
                ["Standard Storage ($/GB)", "$0.023", "$0.020", "$0.018"],
                ["SLA Uptime", "99.99%", "99.95%", "99.90%"],
                ["Versioning Support", "Yes", "Yes", "Yes"],
                ["Object Locking", "Yes (WORM)", "Yes (Bucket Lock)", "Yes (Immutability)"],
            ],
            [45, 45, 45, 45],
        ),
        (
            "Table 2: LLM Framework Evaluation",
            [["Dimension", "LangChain", "LlamaIndex", "Haystack", "DSPy"]],
            [
                [
                    "Primary Focus",
                    "Agent Workflows",
                    "Data Indexing / RAG",
                    "Production NLP",
                    "Programmatic Prompts",
                ],
                ["Learning Curve", "Moderate", "Low-Moderate", "Moderate", "Steep"],
                [
                    "Graph Support",
                    "GraphQA / Cypher",
                    "Knowledge Graphs",
                    "Pipeline Graphs",
                    "Modular Chains",
                ],
                ["Active Community", "Very High", "High", "High", "Growing"],
            ],
            [35, 38, 38, 38, 38],
        ),
        (
            "Table 3: Vector Database Performance Benchmarks",
            [["Metric", "Pinecone", "Milvus", "Qdrant", "ChromaDB"]],
            [
                ["QPS (1M vectors, 768d)", "1,200", "2,450", "2,100", "450"],
                ["P99 Latency (ms)", "12.4", "8.1", "9.2", "34.0"],
                ["HNSW Indexing Time", "Managed", "14 mins", "11 mins", "35 mins"],
                ["Hybrid Search (Sparse+Dense)", "Yes", "Yes", "Yes", "Partial"],
            ],
            [45, 35, 35, 35, 35],
        ),
        (
            "Table 4: Subscription Plan Tiers",
            [["Plan Feature", "Free Starter", "Professional", "Enterprise Scale"]],
            [
                ["Monthly Price", "$0", "$49 / mo", "$499 / mo"],
                ["API Requests / day", "1,000", "100,000", "Unlimited"],
                ["Dedicated Support", "Community", "Email (24h)", "24/7 Phone & Slack SLA"],
                ["SSO / SAML", "No", "No", "Yes"],
            ],
            [45, 45, 45, 45],
        ),
        (
            "Table 5: Programming Language Concurrency Models",
            [["Language", "Concurrency Primitive", "Runtime Overhead", "Memory Safety Guarantee"]],
            [
                [
                    "Rust",
                    "Async/Await + OS Threads",
                    "Zero-cost Abstraction",
                    "Compile-time guaranteed",
                ],
                ["Go", "Goroutines + Channels", "Low (2KB stack)", "Garbage collected"],
                ["Python", "Asyncio / Threading / MP", "GIL Bottleneck", "Ref-counted GC"],
                ["Java", "Virtual Threads (Project Loom)", "Low Carrier Threading", "JVM Managed"],
            ],
            [30, 50, 45, 55],
        ),
        (
            "Table 6: Relational Database Feature Matrix",
            [["Capability", "PostgreSQL", "MySQL 8.0", "Oracle 21c", "SQL Server 2022"]],
            [
                [
                    "JSON Query Support",
                    "JSONB (GIN Index)",
                    "JSON Functions",
                    "JSON Datatype",
                    "JSON Path Functions",
                ],
                [
                    "Full Text Search",
                    "Built-in tsvector",
                    "InnoDB FTS",
                    "Oracle Text",
                    "Full-Text Engine",
                ],
                [
                    "Window Functions",
                    "Full SQL:2016",
                    "Standard Support",
                    "Advanced Analytic",
                    "Full Standard Support",
                ],
            ],
            [40, 36, 36, 36, 36],
        ),
        (
            "Table 7: Mobile Operating System Security Comparison",
            [["Security Control", "Apple iOS 18", "Google Android 15", "GrapheneOS"]],
            [
                [
                    "App Sandboxing",
                    "Strict Seatbelt profile",
                    "SELinux & UID sandbox",
                    "Hardened Sandbox + Exec Spawning",
                ],
                [
                    "Biometric Enclave",
                    "Secure Enclave (SEP)",
                    "Titan M2 / StrongBox",
                    "Hardware TrustZone / Titan M2",
                ],
                [
                    "Zero-Day Exploit Mitigation",
                    "BlastDoor / Lockdown Mode",
                    "Memory Tagging (MTE)",
                    "Hardened Malloc + Exploit Protections",
                ],
            ],
            [40, 45, 45, 50],
        ),
        (
            "Table 8: Electric Vehicle Model Specs Comparison",
            [
                [
                    "Specification",
                    "Tesla Model S Plaid",
                    "Porsche Taycan Turbo GT",
                    "Lucid Air Sapphire",
                ]
            ],
            [
                ["0-60 mph (sec)", "1.99 s", "2.1 s", "1.89 s"],
                ["Top Speed (mph)", "200 mph", "190 mph", "205 mph"],
                ["EPA Range (miles)", "359 mi", "280 mi", "427 mi"],
                ["Peak DC Charging (kW)", "250 kW", "320 kW", "300 kW"],
            ],
            [42, 45, 45, 45],
        ),
        (
            "Table 9: Message Broker Architecture Matrix",
            [
                [
                    "Broker",
                    "Architecture Type",
                    "Max Throughput",
                    "Ordering Guarantee",
                    "Storage Retention",
                ]
            ],
            [
                [
                    "Apache Kafka",
                    "Distributed Commit Log",
                    "> 1,000,000 msg/s",
                    "Strict Per-Partition",
                    "Time/Size Based Disk",
                ],
                [
                    "RabbitMQ",
                    "AMQP Smart Broker",
                    "50,000 msg/s",
                    "Strict Per-Queue FIFO",
                    "Transient / Queue ack",
                ],
                [
                    "Apache Pulsar",
                    "Tiered BookKeeper Log",
                    "> 800,000 msg/s",
                    "Per-Partition Key",
                    "Tiered S3 / Cloud Cold",
                ],
                [
                    "NATS JetStream",
                    "Raft-replicated Stream",
                    "> 5,000,000 msg/s",
                    "Per-Subject Stream",
                    "Configurable limits",
                ],
            ],
            [30, 40, 35, 40, 40],
        ),
        (
            "Table 10: Sorting Algorithm Complexity Comparison",
            [["Algorithm", "Best Time", "Average Time", "Worst Time", "Space Complexity"]],
            [
                ["Quicksort", "O(n log n)", "O(n log n)", "O(n^2)", "O(log n)"],
                ["Mergesort", "O(n log n)", "O(n log n)", "O(n log n)", "O(n)"],
                ["Heapsort", "O(n log n)", "O(n log n)", "O(n log n)", "O(1)"],
                ["Timsort", "O(n)", "O(n log n)", "O(n log n)", "O(n)"],
            ],
            [35, 35, 35, 35, 35],
        ),
    ]

    for title, headers, rows, widths in tables:
        render_table(pdf, headers, rows, widths, title)

    pdf.output(str(filepath))


def generate_time_series_pdf(filepath: Path):
    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Archetype 03: Time-Series Tables Corpus", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=10)
    pdf.multi_cell(
        0,
        6,
        "This document contains 10 time-series tables structured with temporal column headers (quarters, months, years, fiscal cycles) tracking financial metrics, server telemetries, and climate trends.",
    )
    pdf.ln(4)

    tables = [
        (
            "Table 1: Corporate Quarterly Revenue Breakdown ($M)",
            [["Segment", "Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]],
            [
                ["Enterprise Software", "1,240.5", "1,310.2", "1,395.0", "1,520.8"],
                ["Cloud Infrastructure", "2,150.0", "2,380.5", "2,610.2", "2,890.4"],
                ["Hardware Devices", "650.2", "580.4", "620.1", "810.5"],
                ["Professional Services", "310.0", "325.0", "340.5", "365.0"],
            ],
            [45, 35, 35, 35, 35],
        ),
        (
            "Table 2: Monthly Active Users (MAU in Millions)",
            [["Platform", "Jan 2024", "Feb 2024", "Mar 2024", "Apr 2024", "May 2024", "Jun 2024"]],
            [
                ["iOS App", "45.2", "46.1", "47.8", "49.0", "50.4", "52.1"],
                ["Android App", "88.5", "90.2", "92.4", "94.8", "97.1", "99.5"],
                ["Web Portal", "32.1", "31.8", "33.0", "33.5", "34.2", "35.0"],
            ],
            [35, 25, 25, 25, 25, 25, 25],
        ),
        (
            "Table 3: Multi-Year Macroeconomic Indicators",
            [["Indicator", "2020", "2021", "2022", "2023", "2024"]],
            [
                ["GDP Growth Rate (%)", "-2.8", "5.9", "2.1", "2.5", "2.8"],
                ["Headline CPI Inflation (%)", "1.4", "7.0", "6.5", "3.4", "2.9"],
                ["Unemployment Rate (%)", "8.1", "5.4", "3.6", "3.7", "4.0"],
                ["10-Year Treasury Yield (%)", "0.93", "1.52", "3.88", "3.88", "4.25"],
            ],
            [50, 27, 27, 27, 27, 27],
        ),
        (
            "Table 4: Datacenter Power Usage Effectiveness (PUE by Month)",
            [
                [
                    "Facility Location",
                    "Jul 2024",
                    "Aug 2024",
                    "Sep 2024",
                    "Oct 2024",
                    "Nov 2024",
                    "Dec 2024",
                ]
            ],
            [
                ["US-East (Virginia)", "1.18", "1.21", "1.16", "1.13", "1.11", "1.10"],
                ["US-West (Oregon)", "1.12", "1.14", "1.11", "1.09", "1.08", "1.08"],
                ["EU-Central (Frankfurt)", "1.22", "1.25", "1.19", "1.14", "1.12", "1.11"],
            ],
            [40, 25, 25, 25, 25, 25, 25],
        ),
        (
            "Table 5: Server Hourly Traffic & CPU Utilization",
            [["Server Role", "08:00", "10:00", "12:00", "14:00", "16:00", "18:00"]],
            [
                ["Web-Gateway-01", "28%", "64%", "89%", "82%", "75%", "52%"],
                ["Auth-Service-02", "15%", "42%", "68%", "61%", "54%", "38%"],
                ["Payment-Worker-01", "10%", "35%", "55%", "50%", "48%", "25%"],
            ],
            [40, 25, 25, 25, 25, 25, 25],
        ),
        (
            "Table 6: Fiscal Year CapEx Spending ($ Millions)",
            [["Business Unit", "FY21", "FY22", "FY23", "FY24", "FY25 (Proj)"]],
            [
                ["Data Center Expansion", "450", "680", "920", "1,250", "1,600"],
                ["R&D Silicon Labs", "120", "180", "240", "310", "400"],
                ["Office Facilities", "85", "40", "35", "50", "60"],
            ],
            [45, 28, 28, 28, 28, 28],
        ),
        (
            "Table 7: Global Temperature Anomalies (deg C relative to baseline)",
            [["Hemisphere", "2019", "2020", "2021", "2022", "2023", "2024"]],
            [
                ["Northern Hemisphere", "+1.21", "+1.34", "+1.18", "+1.24", "+1.48", "+1.56"],
                ["Southern Hemisphere", "+0.78", "+0.82", "+0.72", "+0.76", "+0.92", "+0.98"],
                ["Global Mean", "+0.99", "+1.08", "+0.95", "+1.00", "+1.20", "+1.27"],
            ],
            [40, 25, 25, 25, 25, 25, 25],
        ),
        (
            "Table 8: Stock Market Volatility Index (VIX Historical by Quarter)",
            [["Index / Metric", "Q1 2023", "Q2 2023", "Q3 2023", "Q4 2023", "Q1 2024"]],
            [
                ["CBOE VIX High", "30.8", "20.1", "18.8", "23.0", "16.4"],
                ["CBOE VIX Low", "17.1", "12.7", "12.6", "11.8", "12.3"],
                ["CBOE VIX Close", "18.7", "13.6", "17.5", "12.5", "13.0"],
            ],
            [40, 28, 28, 28, 28, 28],
        ),
        (
            "Table 9: E-Commerce Conversion Rates (%)",
            [["Traffic Channel", "Jan", "Feb", "Mar", "Apr", "May", "Jun"]],
            [
                ["Organic Search", "3.2%", "3.4%", "3.5%", "3.3%", "3.6%", "3.8%"],
                ["Paid Social", "1.8%", "1.9%", "2.1%", "2.0%", "2.2%", "2.4%"],
                ["Email Newsletter", "4.5%", "4.8%", "5.1%", "4.9%", "5.3%", "5.6%"],
                ["Direct Traffic", "2.8%", "2.9%", "3.0%", "3.0%", "3.1%", "3.2%"],
            ],
            [40, 25, 25, 25, 25, 25, 25],
        ),
        (
            "Table 10: Semiconductor Fab Capacity Utilization",
            [["Fab Location", "H1 2022", "H2 2022", "H1 2023", "H2 2023", "H1 2024"]],
            [
                ["Fab 12 (Tainan - 3nm)", "98%", "99%", "95%", "97%", "100%"],
                ["Fab 18 (Hsinchu - 5nm)", "96%", "95%", "90%", "92%", "96%"],
                ["Fab 20 (Kumamoto - 12nm)", "N/A", "N/A", "82%", "88%", "94%"],
            ],
            [45, 28, 28, 28, 28, 28],
        ),
    ]

    for title, headers, rows, widths in tables:
        render_table(pdf, headers, rows, widths, title)

    pdf.output(str(filepath))


def generate_hierarchical_pdf(filepath: Path):
    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(
        0, 10, "Archetype 04: Hierarchical & Nested Tables Corpus", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.set_font("helvetica", size=10)
    pdf.multi_cell(
        0,
        6,
        "This document contains 10 hierarchical tables featuring multi-level headers, parent-child nesting, indented category trees, and departmental budget breakdowns.",
    )
    pdf.ln(4)

    tables = [
        (
            "Table 1: Corporate Division Budget Breakdown (Multi-level header)",
            [
                [
                    "Division",
                    "Domestic Operations",
                    "Domestic Operations",
                    "International",
                    "International",
                ],
                ["", "Headcount", "Budget ($M)", "Headcount", "Budget ($M)"],
            ],
            [
                ["Engineering", "450", "65.2", "220", "28.4"],
                ["Sales & Mktg", "180", "42.0", "140", "31.5"],
                ["Operations", "90", "12.5", "60", "8.2"],
            ],
            [40, 35, 35, 35, 35],
        ),
        (
            "Table 2: Indented Category Account Ledger (Tree structure)",
            [["Account Code & Category", "Debit ($)", "Credit ($)"]],
            [
                ["1000 - Assets", "1,500,000", ""],
                ["  1100 - Current Assets", "800,000", ""],
                ["    1110 - Cash in Bank", "500,000", ""],
                ["    1120 - Accounts Receivable", "300,000", ""],
                ["  1200 - Fixed Assets", "700,000", ""],
                ["    1210 - Machinery & Hardware", "700,000", ""],
            ],
            [80, 50, 50],
        ),
        (
            "Table 3: Product Line Regional Performance",
            [
                ["Product Line", "North America", "North America", "EMEA", "EMEA"],
                ["", "Units Sold", "Revenue ($k)", "Units Sold", "Revenue ($k)"],
            ],
            [
                ["Compute Cluster Alpha", "120", "12,000", "85", "8,500"],
                ["Storage Pod Beta", "340", "6,800", "290", "5,800"],
                ["Edge Gateway Gamma", "1,200", "2,400", "950", "1,900"],
            ],
            [45, 35, 35, 35, 35],
        ),
        (
            "Table 4: Organizational Role Hierarchy with Indents",
            [["Position / Department", "Grade Level", "Direct Reports", "Location"]],
            [
                ["Chief Executive Officer", "E-10", "6", "Headquarters"],
                ["  Chief Technology Officer", "E-9", "4", "San Francisco"],
                ["    VP of AI Systems", "E-8", "5", "San Francisco"],
                ["      Principal Architect", "IC-7", "0", "Remote"],
                ["    VP of Infrastructure", "E-8", "6", "Austin"],
            ],
            [60, 30, 35, 55],
        ),
        (
            "Table 5: Academic Department Course Structure",
            [
                [
                    "Faculty & Department",
                    "UG Enrollment",
                    "UG Enrollment",
                    "PG Enrollment",
                    "PG Enrollment",
                ],
                ["", "Courses", "Students", "Courses", "Students"],
            ],
            [
                ["Computer Science", "24", "1,200", "12", "350"],
                ["Electrical Engg", "18", "850", "10", "220"],
                ["Mathematics", "30", "1,500", "8", "140"],
            ],
            [40, 35, 35, 35, 35],
        ),
        (
            "Table 6: Supply Chain Bill of Materials (BOM Hierarchy)",
            [["BOM Level & Part Name", "Part Number", "Qty Required", "Unit Cost ($)"]],
            [
                ["0 - High Performance Workstation", "SYS-001", "1", "4,500.00"],
                ["  1 - Motherboard Assembly", "MB-X99", "1", "650.00"],
                ["    2 - VRM Heatsink Module", "HS-220", "2", "45.00"],
                ["  1 - Power Supply Unit 1200W", "PSU-1200", "1", "280.00"],
                ["  1 - Cooling Subsystem", "COOL-AIO", "1", "180.00"],
            ],
            [65, 35, 35, 35],
        ),
        (
            "Table 7: Healthcare Clinical Trial Cohorts (Nested)",
            [
                [
                    "Trial Arm",
                    "Demographics",
                    "Demographics",
                    "Clinical Outcome",
                    "Clinical Outcome",
                ],
                ["", "Age < 50", "Age >= 50", "Responders", "Adverse Events"],
            ],
            [
                ["Treatment Group A (100mg)", "140", "160", "245 (81.6%)", "12 (4.0%)"],
                ["Treatment Group B (200mg)", "135", "165", "272 (90.6%)", "24 (8.0%)"],
                ["Control Placebo", "150", "150", "45 (15.0%)", "8 (2.6%)"],
            ],
            [45, 30, 30, 42, 38],
        ),
        (
            "Table 8: Geographic Sales Breakdown (3-level Nested Headers)",
            [
                ["Territory", "Q1 Revenue", "Q1 Revenue", "Q2 Revenue", "Q2 Revenue"],
                ["", "Direct", "Channel", "Direct", "Channel"],
            ],
            [
                ["West Coast", "450k", "210k", "520k", "240k"],
                ["East Coast", "380k", "190k", "410k", "200k"],
                ["Midwest", "220k", "110k", "250k", "130k"],
            ],
            [40, 35, 35, 35, 35],
        ),
        (
            "Table 9: Government Spending by Functional Category",
            [["Agency / Program", "Discretionary ($B)", "Mandatory ($B)"]],
            [
                ["Department of Defense", "840.5", "12.0"],
                ["  Military Personnel", "180.2", "0.0"],
                ["  Operations & Maintenance", "310.4", "0.0"],
                ["  Procurement & Weapon Systems", "170.0", "0.0"],
                ["Department of Energy", "45.2", "5.1"],
            ],
            [70, 50, 50],
        ),
        (
            "Table 10: Software Package Dependency Tree",
            [["Module Hierarchy", "License", "Security Vulnerabilities", "Version Constraint"]],
            [
                ["root-app", "MIT", "0 Known", "^2.1.0"],
                ["  express-server", "MIT", "0 Known", "^4.18.2"],
                ["    body-parser", "MIT", "0 Known", "~1.20.1"],
                ["    cookie-session", "MIT", "1 Low", "~2.0.0"],
                ["  postgres-client", "BSD-3", "0 Known", "^8.11.0"],
            ],
            [55, 30, 50, 45],
        ),
    ]

    for title, headers, rows, widths in tables:
        render_table(pdf, headers, rows, widths, title)

    pdf.output(str(filepath))


def generate_matrix_pdf(filepath: Path):
    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Archetype 05: Matrix & Adjacency Tables Corpus", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=10)
    pdf.multi_cell(
        0,
        6,
        "This document contains 10 matrix and adjacency tables including inter-city distance matrices, correlation coefficients, network hop latencies, transition probabilities, and similarity scores.",
    )
    pdf.ln(4)

    tables = [
        (
            "Table 1: Inter-City Highway Distances (Miles)",
            [["", "New York", "Chicago", "Houston", "San Francisco", "Seattle"]],
            [
                ["New York", "0", "790", "1,630", "2,900", "2,850"],
                ["Chicago", "790", "0", "1,080", "2,130", "2,060"],
                ["Houston", "1,630", "1,080", "0", "1,930", "2,310"],
                ["San Francisco", "2,900", "2,130", "1,930", "0", "810"],
                ["Seattle", "2,850", "2,060", "2,310", "810", "0"],
            ],
            [32, 28, 28, 28, 34, 28],
        ),
        (
            "Table 2: Asset Class Pearson Correlation Matrix",
            [["", "Equities", "Treasuries", "Real Estate", "Gold", "Crypto"]],
            [
                ["Equities", "1.00", "-0.32", "0.68", "0.15", "0.42"],
                ["Treasuries", "-0.32", "1.00", "-0.18", "0.28", "-0.12"],
                ["Real Estate", "0.68", "-0.18", "1.00", "0.22", "0.31"],
                ["Gold", "0.15", "0.28", "0.22", "1.00", "0.08"],
                ["Crypto", "0.42", "-0.12", "0.31", "0.08", "1.00"],
            ],
            [30, 28, 28, 28, 28, 28],
        ),
        (
            "Table 3: Datacenter Inter-Region Network Round-Trip Latency (ms)",
            [["", "us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1"]],
            [
                ["us-east-1", "0.4", "68.2", "74.1", "158.4"],
                ["us-west-2", "68.2", "0.3", "132.5", "98.7"],
                ["eu-west-1", "74.1", "132.5", "0.5", "215.0"],
                ["ap-northeast-1", "158.4", "98.7", "215.0", "0.6"],
            ],
            [35, 35, 35, 35, 38],
        ),
        (
            "Table 4: Markov Chain State Transition Probabilities",
            [["", "State S0", "State S1", "State S2", "State S3"]],
            [
                ["State S0", "0.70", "0.15", "0.10", "0.05"],
                ["State S1", "0.20", "0.60", "0.15", "0.05"],
                ["State S2", "0.05", "0.25", "0.55", "0.15"],
                ["State S3", "0.00", "0.10", "0.30", "0.60"],
            ],
            [35, 35, 35, 35, 35],
        ),
        (
            "Table 5: Cosine Similarity Matrix for Document Embeddings",
            [["", "Doc 1", "Doc 2", "Doc 3", "Doc 4"]],
            [
                ["Doc 1", "1.00", "0.84", "0.32", "0.12"],
                ["Doc 2", "0.84", "1.00", "0.41", "0.18"],
                ["Doc 3", "0.32", "0.41", "1.00", "0.76"],
                ["Doc 4", "0.12", "0.18", "0.76", "1.00"],
            ],
            [35, 35, 35, 35, 35],
        ),
        (
            "Table 6: Graph Adjacency Matrix (Directed Network)",
            [["", "Node A", "Node B", "Node C", "Node D", "Node E"]],
            [
                ["Node A", "0", "1", "1", "0", "0"],
                ["Node B", "0", "0", "1", "1", "0"],
                ["Node C", "0", "0", "0", "1", "1"],
                ["Node D", "1", "0", "0", "0", "1"],
                ["Node E", "0", "0", "0", "0", "0"],
            ],
            [30, 28, 28, 28, 28, 28],
        ),
        (
            "Table 7: Airline Flight Times Between Hubs (Hours:Minutes)",
            [["", "LHR (London)", "JFK (New York)", "HND (Tokyo)", "DXB (Dubai)"]],
            [
                ["LHR (London)", "0:00", "7:45", "11:30", "6:50"],
                ["JFK (New York)", "7:00", "0:00", "14:15", "12:30"],
                ["HND (Tokyo)", "12:15", "13:40", "0:00", "9:40"],
                ["DXB (Dubai)", "7:10", "14:00", "9:15", "0:00"],
            ],
            [35, 35, 35, 35, 35],
        ),
        (
            "Table 8: Gene Expression Correlation Coefficients",
            [["", "BRCA1", "TP53", "EGFR", "MYC"]],
            [
                ["BRCA1", "1.00", "0.72", "0.45", "-0.18"],
                ["TP53", "0.72", "1.00", "0.61", "-0.05"],
                ["EGFR", "0.45", "0.61", "1.00", "0.38"],
                ["MYC", "-0.18", "-0.05", "0.38", "1.00"],
            ],
            [35, 35, 35, 35, 35],
        ),
        (
            "Table 9: Game Theory Payoff Matrix (Player 1 / Player 2)",
            [["", "Cooperate", "Defect"]],
            [["Cooperate", "(3, 3)", "(0, 5)"], ["Defect", "(5, 0)", "(1, 1)"]],
            [40, 50, 50],
        ),
        (
            "Table 10: Communication Bus Signal Cross-Talk Matrix (dB)",
            [["", "Trace 1", "Trace 2", "Trace 3", "Trace 4"]],
            [
                ["Trace 1", "-0.0 dB", "-42.5 dB", "-58.1 dB", "-71.2 dB"],
                ["Trace 2", "-42.5 dB", "-0.0 dB", "-41.8 dB", "-59.0 dB"],
                ["Trace 3", "-58.1 dB", "-41.8 dB", "-0.0 dB", "-43.1 dB"],
                ["Trace 4", "-71.2 dB", "-59.0 dB", "-43.1 dB", "-0.0 dB"],
            ],
            [32, 35, 35, 35, 35],
        ),
    ]

    for title, headers, rows, widths in tables:
        render_table(pdf, headers, rows, widths, title)

    pdf.output(str(filepath))


def generate_relational_pdf(filepath: Path):
    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(
        0,
        10,
        "Archetype 06: Relational / Database Record Tables Corpus",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_font("helvetica", size=10)
    pdf.multi_cell(
        0,
        6,
        "This document contains 10 relational tables exhibiting standard database schemas with explicit primary and foreign key references (order_id, user_id, product_fk, invoice_id, etc.).",
    )
    pdf.ln(4)

    tables = [
        (
            "Table 1: Customer Order Transaction Records",
            [["order_id", "customer_fk", "order_date", "total_amount", "status"]],
            [
                ["ORD-1001", "CUST-8821", "2024-03-01", "$149.99", "Completed"],
                ["ORD-1002", "CUST-9014", "2024-03-02", "$89.50", "Shipped"],
                ["ORD-1003", "CUST-8821", "2024-03-04", "$1,240.00", "Completed"],
                ["ORD-1004", "CUST-3310", "2024-03-05", "$32.00", "Processing"],
            ],
            [30, 30, 35, 35, 35],
        ),
        (
            "Table 2: E-Commerce Order Line Items (Junction Table)",
            [["item_id", "order_fk", "product_fk", "quantity", "unit_price"]],
            [
                ["LINE-901", "ORD-1001", "PROD-A01", "2", "$49.99"],
                ["LINE-902", "ORD-1001", "PROD-B05", "1", "$50.01"],
                ["LINE-903", "ORD-1002", "PROD-C12", "1", "$89.50"],
                ["LINE-904", "ORD-1003", "PROD-A01", "10", "$49.99"],
            ],
            [30, 35, 35, 30, 35],
        ),
        (
            "Table 3: Employee Department Assignments",
            [["emp_id", "dept_fk", "job_title", "salary_band", "hire_date"]],
            [
                ["EMP-0101", "DEPT-ENG", "Staff Systems Engineer", "BAND-8", "2021-04-15"],
                ["EMP-0102", "DEPT-ENG", "Senior AI Researcher", "BAND-8", "2022-01-10"],
                ["EMP-0205", "DEPT-MKT", "Marketing Director", "BAND-7", "2019-11-01"],
                ["EMP-0310", "DEPT-OPS", "Site Reliability Eng", "BAND-6", "2023-08-20"],
            ],
            [30, 30, 48, 30, 35],
        ),
        (
            "Table 4: Financial Invoices and Billing Records",
            [["invoice_id", "account_fk", "due_date", "balance_due", "currency"]],
            [
                ["INV-2024-01", "ACC-7740", "2024-04-15", "14,500.00", "USD"],
                ["INV-2024-02", "ACC-1029", "2024-04-20", "2,840.50", "EUR"],
                ["INV-2024-03", "ACC-9931", "2024-04-30", "850.00", "GBP"],
                ["INV-2024-04", "ACC-7740", "2024-05-15", "12,200.00", "USD"],
            ],
            [35, 35, 35, 35, 30],
        ),
        (
            "Table 5: Warehouse Inventory Stocking Records",
            [["sku_id", "warehouse_fk", "bin_location", "stock_qty", "reorder_point"]],
            [
                ["SKU-00129", "WH-WEST-01", "Aisle 4, Bay 12", "450", "100"],
                ["SKU-00130", "WH-WEST-01", "Aisle 4, Bay 14", "82", "150"],
                ["SKU-00244", "WH-EAST-02", "Aisle 1, Bay 03", "1,200", "300"],
                ["SKU-00391", "WH-EU-01", "Aisle 9, Bay 22", "15", "50"],
            ],
            [32, 35, 45, 30, 35],
        ),
        (
            "Table 6: IT Helpdesk Support Tickets",
            [["ticket_id", "user_fk", "assigned_tech_fk", "priority", "created_at"]],
            [
                ["TICK-4401", "USR-99281", "TECH-04", "High", "2024-03-10 09:15"],
                ["TICK-4402", "USR-10294", "TECH-12", "Low", "2024-03-10 10:42"],
                ["TICK-4403", "USR-88102", "TECH-04", "Critical", "2024-03-11 08:00"],
                ["TICK-4404", "USR-99281", "TECH-09", "Medium", "2024-03-11 14:22"],
            ],
            [30, 30, 35, 25, 45],
        ),
        (
            "Table 7: Vehicle Fleet Maintenance Log",
            [["log_id", "vehicle_fk", "service_type", "cost", "odometer_miles"]],
            [
                ["MNT-881", "VEH-104", "Brake Replacement", "$450.00", "42,150"],
                ["MNT-882", "VEH-202", "Oil & Filter Change", "$85.00", "15,800"],
                ["MNT-883", "VEH-104", "Tire Rotation", "$60.00", "45,000"],
                ["MNT-884", "VEH-319", "Battery Pack Diagnostics", "$320.00", "68,900"],
            ],
            [30, 30, 45, 30, 38],
        ),
        (
            "Table 8: Flight Reservation Passenger Roster",
            [["booking_ref", "passenger_fk", "flight_fk", "seat_number", "meal_pref"]],
            [
                ["BK-9021", "PAX-118", "FL-AA100", "12A", "Vegetarian"],
                ["BK-9022", "PAX-409", "FL-AA100", "12B", "Standard"],
                ["BK-9023", "PAX-882", "FL-BA284", "04F", "Gluten-Free"],
                ["BK-9024", "PAX-901", "FL-LH450", "28C", "Standard"],
            ],
            [32, 35, 35, 30, 35],
        ),
        (
            "Table 9: Security Audit Access Events",
            [["event_id", "principal_fk", "resource_fk", "action", "ip_address"]],
            [
                ["EVT-001928", "USR-99281", "RES-S3-FINANCE", "GET_OBJECT", "10.0.4.15"],
                ["EVT-001929", "USR-10294", "RES-PG-PROD", "CONNECT", "10.0.4.88"],
                ["EVT-001930", "USR-99281", "RES-S3-FINANCE", "PUT_OBJECT", "10.0.4.15"],
                ["EVT-001931", "SVC-BACKUP", "RES-PG-PROD", "DUMP_DATABASE", "10.0.2.1"],
            ],
            [30, 32, 40, 35, 32],
        ),
        (
            "Table 10: Pharmacy Medication Prescription Fulfillments",
            [["rx_id", "patient_fk", "doctor_fk", "medication_code", "refills_left"]],
            [
                ["RX-55102", "PAT-9912", "DOC-401", "MED-AMOX-500", "2"],
                ["RX-55103", "PAT-4418", "DOC-102", "MED-LIPITOR-20", "5"],
                ["RX-55104", "PAT-9912", "DOC-401", "MED-ALBUTEROL", "1"],
                ["RX-55105", "PAT-2201", "DOC-889", "MED-METFORMIN-1K", "3"],
            ],
            [30, 30, 30, 42, 30],
        ),
    ]

    for title, headers, rows, widths in tables:
        render_table(pdf, headers, rows, widths, title)

    pdf.output(str(filepath))


def generate_pivot_pdf(filepath: Path):
    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(
        0, 10, "Archetype 07: Pivot / Cross-Tabulated Tables Corpus", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.set_font("helvetica", size=10)
    pdf.multi_cell(
        0,
        6,
        "This document contains 20 pivot and cross-tab tables featuring cross-dimensional metric aggregations, multi-year and regional quarterly matrices, category by channel breakdowns, and variable range grids (from/to in rows and columns).",
    )
    pdf.ln(4)

    tables = [
        (
            "Table 1: Regional Sales by Product Line Pivot",
            [["Product Category", "2023", "2023", "2024", "2024"], ["", "Q1", "Q2", "Q1", "Q2"]],
            [
                ["Enterprise Software", "1,200", "1,350", "1,480", "1,620"],
                ["Hardware Appliances", "850", "890", "920", "990"],
                ["Cloud Subscriptions", "2,100", "2,450", "2,900", "3,300"],
                ["Professional Consulting", "320", "340", "360", "390"],
            ],
            [45, 32, 32, 32, 32],
        ),
        (
            "Table 2: Marketing Channel Leads by Geography",
            [
                [
                    "Channel",
                    "North America",
                    "North America",
                    "Europe",
                    "Europe",
                    "Asia-Pacific",
                    "Asia-Pacific",
                ],
                ["", "Organic", "Paid", "Organic", "Paid", "Organic", "Paid"],
            ],
            [
                ["Direct Web", "45,000", "12,000", "38,000", "9,500", "29,000", "14,000"],
                ["Social Media", "18,500", "64,000", "14,200", "48,000", "22,000", "55,000"],
                ["Email Campaigns", "12,000", "8,500", "9,800", "6,200", "8,100", "5,400"],
            ],
            [35, 23, 23, 23, 23, 23, 23],
        ),
        (
            "Table 3: Workforce Headcount by Department & Office",
            [
                ["Department", "New York", "New York", "London", "London", "Tokyo", "Tokyo"],
                ["", "Full-Time", "Contract", "Full-Time", "Contract", "Full-Time", "Contract"],
            ],
            [
                ["Software Engineering", "180", "25", "120", "18", "95", "12"],
                ["Product Management", "35", "2", "22", "1", "15", "0"],
                ["Customer Success", "65", "10", "45", "8", "30", "5"],
            ],
            [40, 22, 22, 22, 22, 22, 22],
        ),
        (
            "Table 4: E-Commerce Returns by Reason & Product Tier",
            [
                ["Product Tier", "Defective Item", "Defective Item", "Wrong Size", "Wrong Size"],
                ["", "Count", "% Total", "Count", "% Total"],
            ],
            [
                ["Budget Basics", "1,240", "4.2%", "3,890", "13.1%"],
                ["Mid-Range Classic", "480", "1.8%", "1,620", "6.2%"],
                ["Premium Luxury", "95", "0.8%", "310", "2.6%"],
            ],
            [45, 30, 28, 30, 28],
        ),
        (
            "Table 5: Server Fleet Energy Consumption (kWh by Day & Shift)",
            [
                ["Server Rack Cluster", "Weekday", "Weekday", "Weekend", "Weekend"],
                ["", "Day Shift", "Night Shift", "Day Shift", "Night Shift"],
            ],
            [
                ["Cluster-Alpha (AI Training)", "4,800", "5,200", "4,600", "4,900"],
                ["Cluster-Beta (Inference API)", "3,200", "1,800", "2,900", "1,400"],
                ["Cluster-Gamma (Storage SAN)", "1,100", "1,050", "1,080", "1,020"],
            ],
            [45, 32, 32, 32, 32],
        ),
        (
            "Table 6: Hotel Occupancy Rates by Room Category & Season",
            [
                ["Room Type", "High Season", "High Season", "Low Season", "Low Season"],
                ["", "Occupancy %", "ADR ($)", "Occupancy %", "ADR ($)"],
            ],
            [
                ["Standard Queen", "94.5%", "$189", "62.0%", "$119"],
                ["Deluxe King Suite", "89.2%", "$299", "54.5%", "$199"],
                ["Presidential Penthouse", "78.0%", "$850", "38.0%", "$550"],
            ],
            [45, 32, 32, 32, 32],
        ),
        (
            "Table 7: Loan Portfolio Risk Default Matrix",
            [
                [
                    "Credit Score Tier",
                    "30-Day Past Due",
                    "30-Day Past Due",
                    "90-Day Default",
                    "90-Day Default",
                ],
                ["", "Loan Count", "Balance ($M)", "Loan Count", "Balance ($M)"],
            ],
            [
                ["Prime (750+)", "42", "1.2", "4", "0.1"],
                ["Near Prime (680-749)", "185", "4.8", "28", "0.9"],
                ["Subprime (<680)", "890", "18.4", "240", "6.2"],
            ],
            [45, 32, 32, 32, 32],
        ),
        (
            "Table 8: University Admissions by Major & Residency",
            [
                ["Major Discipline", "In-State", "In-State", "Out-of-State", "Out-of-State"],
                ["", "Applied", "Accepted", "Applied", "Accepted"],
            ],
            [
                ["Computer Science", "4,500", "650", "8,200", "520"],
                ["Mechanical Engg", "2,800", "580", "3,400", "480"],
                ["Biomedical Sciences", "3,100", "720", "4,100", "610"],
            ],
            [45, 30, 30, 30, 30],
        ),
        (
            "Table 9: Manufacturing Quality Defect Counts by Factory & Machine Type",
            [
                [
                    "Defect Category",
                    "Factory 1 (Austin)",
                    "Factory 1 (Austin)",
                    "Factory 2 (Dresden)",
                    "Factory 2 (Dresden)",
                ],
                ["", "CNC Mill", "Laser Weld", "CNC Mill", "Laser Weld"],
            ],
            [
                ["Dimensional Variance", "42", "8", "28", "5"],
                ["Surface Scratch / Blemish", "85", "14", "64", "11"],
                ["Weld Porosity", "0", "48", "0", "32"],
            ],
            [45, 32, 32, 32, 32],
        ),
        (
            "Table 10: SaaS Customer Retention Cohort Cross-Tab",
            [
                ["Signup Cohort", "Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6"],
                [
                    "",
                    "Retained %",
                    "Retained %",
                    "Retained %",
                    "Retained %",
                    "Retained %",
                    "Retained %",
                ],
            ],
            [
                ["Jan 2024 Cohort", "100%", "88%", "82%", "78%", "75%", "73%"],
                ["Feb 2024 Cohort", "100%", "89%", "84%", "80%", "77%", "N/A"],
                ["Mar 2024 Cohort", "100%", "91%", "86%", "82%", "N/A", "N/A"],
            ],
            [35, 23, 23, 23, 23, 23, 23],
        ),
        (
            "Table 11: Continental Temperature Map (Ranges in Rows/Cols)",
            [
                [
                    "Latitude",
                    "Latitude",
                    "Longitude (100W - 110W)",
                    "Longitude (100W - 110W)",
                    "Longitude (110W - 120W)",
                    "Longitude (110W - 120W)",
                ],
                ["From", "To", "From", "To", "From", "To"],
            ],
            [
                ["30N", "40N", "68 F", "74 F", "71 F", "78 F"],
                ["40N", "50N", "54 F", "60 F", "58 F", "63 F"],
                ["50N", "60N", "42 F", "48 F", "46 F", "51 F"],
            ],
            [28, 28, 33, 33, 33, 33],
        ),
        (
            "Table 12: Income Tax Brackets by Age and Earnings",
            [
                [
                    "Age Range",
                    "Age Range",
                    "Income ($0k - $50k)",
                    "Income ($0k - $50k)",
                    "Income ($50k - $100k)",
                    "Income ($50k - $100k)",
                ],
                ["From", "To", "From", "To", "From", "To"],
            ],
            [
                ["18", "30", "10.0%", "12.5%", "20.0%", "22.5%"],
                ["31", "55", "11.0%", "13.0%", "22.0%", "24.5%"],
                ["56", "75", "9.5%", "11.5%", "18.5%", "20.0%"],
            ],
            [28, 28, 33, 33, 33, 33],
        ),
        (
            "Table 13: Logistics Shipping Costs by Distance & Weight",
            [
                [
                    "Weight (kg)",
                    "Weight (kg)",
                    "Distance (0 - 500 mi)",
                    "Distance (0 - 500 mi)",
                    "Distance (500 - 1000 mi)",
                    "Distance (500 - 1000 mi)",
                ],
                ["From", "To", "From", "To", "From", "To"],
            ],
            [
                ["0.0", "5.0", "$5.50", "$8.25", "$9.00", "$14.50"],
                ["5.1", "20.0", "$12.00", "$18.50", "$24.00", "$32.00"],
                ["20.1", "50.0", "$28.00", "$45.00", "$52.00", "$75.00"],
            ],
            [28, 28, 33, 33, 33, 33],
        ),
        (
            "Table 14: Network Latency SLA by Packet Size & Bandwidth",
            [
                [
                    "Packet Size (bytes)",
                    "Packet Size (bytes)",
                    "Bandwidth (10-50 Mbps)",
                    "Bandwidth (10-50 Mbps)",
                    "Bandwidth (50-100 Mbps)",
                    "Bandwidth (50-100 Mbps)",
                ],
                ["From", "To", "From", "To", "From", "To"],
            ],
            [
                ["64", "512", "12 ms", "18 ms", "8 ms", "12 ms"],
                ["513", "1500", "22 ms", "35 ms", "15 ms", "22 ms"],
                ["1501", "9000", "45 ms", "68 ms", "32 ms", "48 ms"],
            ],
            [30, 30, 32, 32, 32, 32],
        ),
        (
            "Table 15: Regional Property Values by Lot Size & Year Built",
            [
                [
                    "Year Built",
                    "Year Built",
                    "Lot Size (0 - 0.5 Acres)",
                    "Lot Size (0 - 0.5 Acres)",
                    "Lot Size (0.5 - 1.0 Acres)",
                    "Lot Size (0.5 - 1.0 Acres)",
                ],
                ["From", "To", "From", "To", "From", "To"],
            ],
            [
                ["1950", "1980", "$120k", "$250k", "$180k", "$320k"],
                ["1981", "2005", "$180k", "$340k", "$260k", "$450k"],
                ["2006", "2024", "$290k", "$580k", "$420k", "$850k"],
            ],
            [28, 28, 33, 33, 33, 33],
        ),
        (
            "Table 11.2: Continental Temperature Map (Option A)",
            [
                ["Latitude", "Latitude", "Longitude", "Longitude", "Longitude", "Longitude"],
                ["From", "To", "From 100W", "From 110W", "From 120W", "From 130W"],
                ["", "", "To 110W", "To 120W", "To 130W", "To 140W"],
            ],
            [
                ["30N", "40N", "68 F", "71 F", "73 F", "75 F"],
                ["40N", "50N", "54 F", "58 F", "60 F", "62 F"],
                ["50N", "60N", "42 F", "46 F", "48 F", "50 F"],
            ],
            [28, 28, 33, 33, 33, 33],
        ),
        (
            "Table 12.2: Income Tax Brackets by Age and Earnings (Option A)",
            [
                ["Age", "Age", "Income", "Income", "Income", "Income"],
                ["From", "To", "From $0k", "From $50k", "From $100k", "From $200k"],
                ["", "", "To $50k", "To $100k", "To $200k", "To Max"],
            ],
            [
                ["18", "30", "10.0%", "20.0%", "30.0%", "35.0%"],
                ["31", "55", "11.0%", "22.0%", "32.0%", "37.0%"],
                ["56", "75", "9.5%", "18.5%", "28.0%", "33.0%"],
            ],
            [28, 28, 33, 33, 33, 33],
        ),
        (
            "Table 13.2: Logistics Shipping Costs by Distance & Weight (Option A)",
            [
                ["Weight", "Weight", "Distance", "Distance", "Distance", "Distance"],
                ["From", "To", "From 0mi", "From 500mi", "From 1000mi", "From 2000mi"],
                ["", "", "To 500mi", "To 1000mi", "To 2000mi", "To Max"],
            ],
            [
                ["0.0kg", "5.0kg", "$5.50", "$9.00", "$15.00", "$25.00"],
                ["5.1kg", "20.0kg", "$12.00", "$24.00", "$38.00", "$55.00"],
                ["20.1kg", "50.0kg", "$28.00", "$52.00", "$85.00", "$120.00"],
            ],
            [28, 28, 33, 33, 33, 33],
        ),
        (
            "Table 14.2: Network Latency SLA by Packet Size & Bandwidth (Option A)",
            [
                ["Packet Size", "Packet Size", "Bandwidth", "Bandwidth", "Bandwidth", "Bandwidth"],
                ["From", "To", "From 10M", "From 50M", "From 100M", "From 1G"],
                ["", "", "To 50M", "To 100M", "To 1G", "To 10G"],
            ],
            [
                ["64B", "512B", "12 ms", "8 ms", "4 ms", "2 ms"],
                ["513B", "1500B", "22 ms", "15 ms", "10 ms", "5 ms"],
                ["1501B", "9000B", "45 ms", "32 ms", "25 ms", "15 ms"],
            ],
            [30, 30, 32, 32, 32, 32],
        ),
        (
            "Table 15.2: Regional Property Values by Lot Size & Year Built (Option A)",
            [
                ["Year Built", "Year Built", "Lot Size", "Lot Size", "Lot Size", "Lot Size"],
                ["From", "To", "From 0ac", "From 0.5ac", "From 1.0ac", "From 5.0ac"],
                ["", "", "To 0.5ac", "To 1.0ac", "To 5.0ac", "To Max"],
            ],
            [
                ["1950", "1980", "$120k", "$180k", "$280k", "$450k"],
                ["1981", "2005", "$180k", "$260k", "$380k", "$600k"],
                ["2006", "2024", "$290k", "$420k", "$650k", "$950k"],
            ],
            [28, 28, 33, 33, 33, 33],
        ),
    ]

    for title, headers, rows, widths in tables:
        render_table(pdf, headers, rows, widths, title)

    pdf.output(str(filepath))


# ==============================================================================
# 2. GENERATE 2 COMPOSITE ALL-7-ARCHETYPES PDFS
# ==============================================================================


def generate_composite_suite(filepath: Path, suite_letter: str = "A"):
    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(
        0,
        10,
        f"Comprehensive Benchmark Suite {suite_letter}: All 7 Table Archetypes",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_font("helvetica", size=9.5)
    pdf.multi_cell(
        0,
        5.5,
        f"Benchmark test harness containing full representative samples of all seven structural table archetypes in a single reference PDF document (Suite {suite_letter}).",
    )
    pdf.ln(3)

    # 1. Key-Value
    render_table(
        pdf,
        [["Hardware Parameter", "Configured Setting"]],
        [
            ["Accelerator Type:", f"NVIDIA H100-{suite_letter}"],
            ["VRAM Memory:", "80GB HBM3"],
            ["Interconnect:", "NVLink 4.0 (900 GB/s)"],
            ["Power TDP:", "700 Watts"],
        ],
        [60, 100],
        f"1. [Key-Value] Deep Learning Accelerator Specs ({suite_letter})",
    )

    # 2. Comparison
    render_table(
        pdf,
        [
            [
                "Feature Metric",
                f"Engine {suite_letter}1",
                f"Engine {suite_letter}2",
                f"Engine {suite_letter}3",
            ]
        ],
        [
            ["Query Latency P95", "4.2 ms", "8.1 ms", "12.0 ms"],
            ["Throughput QPS", "18,500", "12,200", "8,900"],
            ["Cold Start Time", "120 ms", "450 ms", "900 ms"],
        ],
        [45, 45, 45, 45],
        f"2. [Comparison] Query Processing Engine Benchmark ({suite_letter})",
    )

    # 3. Time-Series
    render_table(
        pdf,
        [["Metric Stream", "Q1", "Q2", "Q3", "Q4"]],
        [
            ["API Call Volume (M)", "14.2", "18.5", "22.1", "28.9"],
            ["Error Rate (%)", "0.04%", "0.03%", "0.02%", "0.01%"],
            ["P99 Latency (ms)", "45", "42", "38", "35"],
        ],
        [45, 32, 32, 32, 32],
        f"3. [Time-Series] Quarterly Telemetry Stream ({suite_letter})",
    )

    pdf.add_page()

    # 4. Hierarchical
    render_table(
        pdf,
        [
            [
                "Organizational Unit",
                "Direct Headcount",
                "Direct Headcount",
                "Contractor",
                "Contractor",
            ],
            ["", "Tech", "Non-Tech", "Tech", "Non-Tech"],
        ],
        [
            ["Platform Systems", "140", "15", "25", "4"],
            ["AI Research Lab", "85", "8", "12", "1"],
            ["Data Governance", "35", "10", "8", "2"],
        ],
        [45, 32, 32, 32, 32],
        f"4. [Hierarchical] Staffing Architecture Tree ({suite_letter})",
    )

    # 5. Matrix
    render_table(
        pdf,
        [["", f"Cluster-{suite_letter}1", f"Cluster-{suite_letter}2", f"Cluster-{suite_letter}3"]],
        [
            [f"Cluster-{suite_letter}1", "0.0", "12.4", "45.1"],
            [f"Cluster-{suite_letter}2", "12.4", "0.0", "31.8"],
            [f"Cluster-{suite_letter}3", "45.1", "31.8", "0.0"],
        ],
        [40, 40, 40, 40],
        f"5. [Matrix] Inter-Cluster Latency Distance Matrix ({suite_letter})",
    )

    # 6. Relational
    render_table(
        pdf,
        [["audit_id", "user_fk", "role_fk", "auth_status", "timestamp"]],
        [
            [f"AUD-{suite_letter}01", "USR-99", "ROLE-ADMIN", "SUCCESS", "2024-03-01 12:00:00"],
            [f"AUD-{suite_letter}02", "USR-44", "ROLE-DEV", "SUCCESS", "2024-03-01 12:05:22"],
            [f"AUD-{suite_letter}03", "USR-12", "ROLE-GUEST", "DENIED", "2024-03-01 12:10:45"],
        ],
        [32, 32, 32, 32, 45],
        f"6. [Relational] Security Audit Database Log ({suite_letter})",
    )

    # 7. Pivot
    render_table(
        pdf,
        [
            ["Workload Type", "On-Demand", "On-Demand", "Spot Instances", "Spot Instances"],
            ["", "Cost ($)", "Hours", "Cost ($)", "Hours"],
        ],
        [
            ["Batch Training", "4,500", "1,200", "1,350", "1,150"],
            ["Online Serving", "8,900", "2,400", "0", "0"],
            ["CI/CD Testing", "850", "400", "220", "380"],
        ],
        [45, 32, 32, 32, 32],
        f"7. [Pivot] Cloud Compute Consumption Cross-Tab ({suite_letter})",
    )

    pdf.output(str(filepath))


# ==============================================================================
# 3. GENERATE 2 MIXED CONTENT PDFS (TEXT + DIAGRAMS + TABLES)
# ==============================================================================


def generate_mixed_part1_pdf(filepath: Path):
    """Part 1: Text, Flowchart Diagram, and 3 Table Types (Key-Value, Comparison, Time-Series)."""
    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title & Introduction text
    pdf.set_font("helvetica", "B", 15)
    pdf.set_text_color(20, 30, 60)
    pdf.cell(
        0,
        10,
        "Technical Evaluation Report: Ingestion & Inference Architecture",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.set_font("helvetica", size=9.5)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(
        0,
        5,
        "Executive Summary: This document details the infrastructure specifications, model evaluation matrix, and quarterly performance metrics for the unified multimodal ingestion pipeline. The system utilizes distributed GPU nodes with real-time vector indexing.",
    )
    pdf.ln(3)

    # Vector Flowchart Diagram
    pdf.draw_diagram_flowchart(20, 48, "Figure 1: Multimodal Ingestion Pipeline Flow")
    pdf.set_y(72)

    # 1. Key-Value Table
    render_table(
        pdf,
        [["System Parameter", "Configured Value"]],
        [
            ["Target Model Architecture:", "Llama-3.3-70B-Instruct"],
            ["Context Window Size:", "128,000 tokens"],
            ["Quantization Format:", "AWQ 4-bit"],
            ["Tensor Parallelism:", "4x NVIDIA H100"],
            ["KV Cache Allocation:", "32 GB PagedAttention"],
        ],
        [60, 100],
        "Table 1.1: Serving Node Hardware & Model Specifications (Key-Value)",
    )

    # Paragraph text
    pdf.set_font("helvetica", size=9)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(
        0,
        5,
        "Comparative Analysis: To determine the optimal inference engine, extensive load tests were conducted across vLLM, TensorRT-LLM, and TGI under simulated peak traffic of 10,000 concurrent user sessions.",
    )
    pdf.ln(2)

    # 2. Comparison Table
    render_table(
        pdf,
        [["Serving Metric", "vLLM 0.6", "TensorRT-LLM 0.12", "HuggingFace TGI 2.0"]],
        [
            ["TTFT (Time to First Token)", "18.2 ms", "14.5 ms", "22.4 ms"],
            ["Inter-token Latency (ITL)", "8.4 ms", "6.2 ms", "9.8 ms"],
            ["Throughput (tokens/sec)", "4,850 tok/s", "6,120 tok/s", "3,950 tok/s"],
            ["PagedAttention Support", "Native", "Optimized Kernel", "Standard Paged"],
        ],
        [45, 45, 45, 45],
        "Table 1.2: Inference Engine Benchmark Matrix (Comparison)",
    )

    pdf.add_page()

    # Paragraph text
    pdf.set_font("helvetica", size=9)
    pdf.multi_cell(
        0,
        5,
        "Temporal Trend Analysis: Production telemetries gathered over the preceding four fiscal quarters exhibit consistent token volume expansion alongside decreasing p99 latencies following kernel optimization deployments.",
    )
    pdf.ln(2)

    # 3. Time-Series Table
    render_table(
        pdf,
        [["Production Metric", "Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]],
        [
            ["Total Processed Tokens (B)", "142.5 B", "210.8 B", "340.2 B", "512.0 B"],
            ["Average P99 Latency (ms)", "84.2 ms", "72.5 ms", "54.1 ms", "42.0 ms"],
            ["Infrastructure Cost ($/M Tok)", "$0.45", "$0.38", "$0.29", "$0.22"],
            ["Service Availability Uptime", "99.92%", "99.96%", "99.98%", "99.99%"],
        ],
        [50, 32, 32, 32, 32],
        "Table 1.3: Historical Ingestion Throughput & Latency (Time-Series)",
    )

    pdf.output(str(filepath))


def generate_mixed_part2_pdf(filepath: Path):
    """Part 2: Text, Network Topology Diagram, and 4 Table Types (Hierarchical, Matrix, Relational, Pivot)."""
    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title & Text
    pdf.set_font("helvetica", "B", 15)
    pdf.set_text_color(20, 30, 60)
    pdf.cell(
        0,
        10,
        "Enterprise Knowledge Graph & Relational Operations Audit",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.set_font("helvetica", size=9.5)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(
        0,
        5,
        "Overview: This technical audit details the organizational taxonomy, inter-entity correlation matrices, database transactional schemas, and departmental budget pivot analyses for enterprise graph construction.",
    )
    pdf.ln(3)

    # Vector Topology Diagram
    pdf.draw_diagram_network(20, 48, "Figure 2: Knowledge Graph Node-Link Topology")
    pdf.set_y(78)

    # 1. Hierarchical Table
    render_table(
        pdf,
        [
            ["Ontology Branch", "Sub-Classes", "Sub-Classes", "Properties", "Properties"],
            ["", "Count", "Depth", "Required", "Optional"],
        ],
        [
            ["Entity.Organization", "14", "3", "8", "24"],
            ["Entity.FinancialInstrument", "22", "4", "15", "45"],
            ["Event.CorporateAction", "8", "2", "6", "18"],
        ],
        [45, 32, 32, 32, 32],
        "Table 2.1: Knowledge Graph Taxonomy Depth (Hierarchical)",
    )

    # 2. Matrix Table
    render_table(
        pdf,
        [["", "Entity.Org", "Entity.Person", "Entity.Security", "Event.Trade"]],
        [
            ["Entity.Org", "1.00", "0.85", "0.92", "0.64"],
            ["Entity.Person", "0.85", "1.00", "0.41", "0.78"],
            ["Entity.Security", "0.92", "0.41", "1.00", "0.95"],
            ["Event.Trade", "0.64", "0.78", "0.95", "1.00"],
        ],
        [38, 35, 35, 35, 35],
        "Table 2.2: Semantic Relationship Co-occurrence Matrix (Matrix)",
    )

    pdf.add_page()

    # Paragraph text
    pdf.set_font("helvetica", size=9)
    pdf.multi_cell(
        0,
        5,
        "Database Linkage Schema: Tabular entities are cross-referenced across internal relational stores using explicit foreign key mappings and transaction logs.",
    )
    pdf.ln(2)

    # 3. Relational Table
    render_table(
        pdf,
        [["tx_id", "entity_fk", "graph_node_fk", "tx_type", "amount_usd"]],
        [
            ["TX-9901", "ORG-771", "NODE-0012", "ACQUISITION", "1,200,000,000"],
            ["TX-9902", "ORG-882", "NODE-0045", "DIVIDEND", "45,000,000"],
            ["TX-9903", "ORG-771", "NODE-0089", "STOCK_BUYBACK", "250,000,000"],
        ],
        [30, 32, 35, 35, 42],
        "Table 2.3: Entity Transaction Ledger with Foreign Keys (Relational)",
    )

    # 4. Pivot Table
    render_table(
        pdf,
        [
            ["Corporate Sector", "2023 Actual", "2023 Actual", "2024 Budget", "2024 Budget"],
            ["", "Capex ($M)", "Opex ($M)", "Capex ($M)", "Opex ($M)"],
        ],
        [
            ["Information Technology", "450.0", "120.5", "580.0", "145.0"],
            ["Financial Services", "210.0", "340.0", "260.0", "390.0"],
            ["Healthcare Systems", "180.0", "95.0", "220.0", "110.0"],
        ],
        [45, 32, 32, 32, 32],
        "Table 2.4: Cross-Sector Budget Allocation Pivot (Pivot / Cross-tab)",
    )

    pdf.output(str(filepath))


# ==============================================================================
# 4. LEGACY / UNIT TEST FIXTURES
# ==============================================================================


def create_simple_pdf(path: Path) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.cell(40, 10, "Name", border=1)
    pdf.cell(40, 10, "Age", border=1)
    pdf.cell(40, 10, "City", border=1, new_x="LMARGIN", new_y="NEXT")

    data = [
        ("Alice", "30", "New York"),
        ("Bob", "25", "London"),
        ("Charlie", "35", "Paris"),
        ("Diana", "28", "Berlin"),
        ("Eve", "22", "Tokyo"),
    ]
    for row in data:
        pdf.cell(40, 10, row[0], border=1)
        pdf.cell(40, 10, row[1], border=1)
        pdf.cell(40, 10, row[2], border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(path))


def create_multipage_pdf(path: Path) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.cell(40, 10, "Name", border=1)
    pdf.cell(40, 10, "Age", border=1)
    pdf.cell(40, 10, "City", border=1, new_x="LMARGIN", new_y="NEXT")

    for i in range(1, 4):
        pdf.cell(40, 10, f"Person {i}", border=1)
        pdf.cell(40, 10, f"{20 + i}", border=1)
        pdf.cell(40, 10, "City A", border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.add_page()
    pdf.cell(40, 10, "Name", border=1)
    pdf.cell(40, 10, "Age", border=1)
    pdf.cell(40, 10, "City", border=1, new_x="LMARGIN", new_y="NEXT")

    for i in range(4, 7):
        pdf.cell(40, 10, f"Person {i}", border=1)
        pdf.cell(40, 10, f"{20 + i}", border=1)
        pdf.cell(40, 10, "City A", border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(path))


def create_no_tables_pdf(path: Path) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.multi_cell(0, 10, "This is a document with no tables.\nJust some text paragraphs.")
    pdf.output(str(path))


# ==============================================================================
# MAIN ORCHESTRATOR
# ==============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate PDF fixtures for table-to-graph testing."
    )
    parser.add_argument(
        "--archetype",
        type=int,
        choices=range(1, 8),
        help="Specific archetype to generate (1-7). If omitted, all are generated.",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    ensure_dir(base_dir)

    print("Generating archetype-specific PDF test fixtures...")
    if args.archetype is None or args.archetype == 1:
        generate_key_value_pdf(base_dir / "archetype_01_key_value_specs_and_configs_10_tables.pdf")
    if args.archetype is None or args.archetype == 2:
        generate_comparison_pdf(
            base_dir / "archetype_02_comparison_products_and_features_10_tables.pdf"
        )
    if args.archetype is None or args.archetype == 3:
        generate_time_series_pdf(
            base_dir / "archetype_03_time_series_financial_and_metrics_10_tables.pdf"
        )
    if args.archetype is None or args.archetype == 4:
        generate_hierarchical_pdf(
            base_dir / "archetype_04_hierarchical_org_and_nested_headers_10_tables.pdf"
        )
    if args.archetype is None or args.archetype == 5:
        generate_matrix_pdf(
            base_dir / "archetype_05_matrix_adjacency_and_correlations_10_tables.pdf"
        )
    if args.archetype is None or args.archetype == 6:
        generate_relational_pdf(
            base_dir / "archetype_06_relational_database_records_and_fks_10_tables.pdf"
        )
    if args.archetype is None or args.archetype == 7:
        generate_pivot_pdf(base_dir / "archetype_07_pivot_crosstab_and_breakdowns_20_tables.pdf")

    if args.archetype is None:
        print("Generating comprehensive composite test fixtures (all 7 archetypes)...")
        generate_composite_suite(
            base_dir / "composite_all_7_archetypes_benchmark_suite_a.pdf", suite_letter="A"
        )
        generate_composite_suite(
            base_dir / "composite_all_7_archetypes_benchmark_suite_b.pdf", suite_letter="B"
        )

        print("Generating mixed layout test fixtures (text + diagrams + tables)...")
        generate_mixed_part1_pdf(
            base_dir / "mixed_report_part1_text_diagrams_keyvalue_comparison_timeseries.pdf"
        )
        generate_mixed_part2_pdf(
            base_dir / "mixed_report_part2_text_diagrams_hierarchical_matrix_relational_pivot.pdf"
        )

        print("Generating base unit test fixtures...")
        create_simple_pdf(base_dir / "sample_simple.pdf")
        create_multipage_pdf(base_dir / "sample_multipage.pdf")
        create_no_tables_pdf(base_dir / "sample_no_tables.pdf")

        print("All fixture PDF files generated successfully!")
    else:
        print(f"Archetype {args.archetype} fixtures generated successfully!")


if __name__ == "__main__":
    main()
