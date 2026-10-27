"""Comprehensive Retrieval Benchmark: table-to-graph vs Flat-Text Chunking.

Tests 70+ diverse queries across all 7 structural archetypes:
- Key-Value (Hardware specs, Patient profile, Vehicle configuration)
- Comparison (Cloud providers, Smartphones, LLM models)
- Time-Series (Quarterly financials, Server telemetry, Sales trends)
- Hierarchical (Org hierarchy, Product taxonomy, Financial accounts)
- Matrix (Routing distances, Asset correlation, Network latency)
- Relational (Employees & Projects, Orders & Customers, Supply Chain)
- Pivot / Cross-Tab (Regional Sales by Quarter, Survey demographics)

Evaluates:
- Retrieval Latency (Mean, Median, p95)
- Neighborhood Recall & Context Completeness
- Relational Structure Preservation
"""

from __future__ import annotations

import argparse
import logging
import time
from dataclasses import dataclass
from typing import Any

from tabulate import tabulate

from table_to_graph import build_graph
from table_to_graph.models import TableData
from table_to_graph.retrieval.context_serializer import ContextSerializer
from table_to_graph.retrieval.graph_store import GraphStore
from table_to_graph.retrieval.retriever import GraphRetriever

# ==============================================================================
# 1. BENCHMARK DATASET GENERATION (ALL 7 ARCHETYPES)
# ==============================================================================


def create_benchmark_corpus() -> dict[str, TableData]:
    corpus: dict[str, TableData] = {}

    # --- Archetype 1: Key-Value ---
    corpus["server_specs"] = TableData(
        headers=[["Specification Field", "Configured Value"]],
        rows=[
            ["Hostname", "prd-db-cluster-01.us-east.internal"],
            ["CPU Model", "AMD EPYC 9654 (96 Cores, 192 Threads)"],
            ["Base Clock", "2.40 GHz"],
            ["Boost Clock", "3.70 GHz"],
            ["RAM Size", "768 GB DDR5 ECC"],
            ["Primary Storage", "2x 3.84TB NVMe RAID-1 (OS)"],
            ["Data Storage", "8x 15.36TB NVMe U.2 RAID-10 (Data)"],
            ["Network NIC", "Dual-port 100GbE Mellanox ConnectX-6"],
            ["Operating System", "Ubuntu 24.04 LTS Kernel 6.8"],
            ["Hypervisor", "KVM / Proxmox VE 8.1"],
            ["Power Redundancy", "Dual 1600W Titanium 80-Plus PSU"],
        ],
    )

    corpus["clinical_patient"] = TableData(
        headers=[["Patient Clinical Attribute", "Recorded Metric"]],
        rows=[
            ["Patient ID", "PT-889104"],
            ["Primary Diagnosis", "Type 2 Diabetes Mellitus"],
            ["Secondary Diagnosis", "Stage 1 Essential Hypertension"],
            ["HbA1c Level", "7.8 %"],
            ["Fasting Blood Glucose", "148 mg/dL"],
            ["Systolic Blood Pressure", "138 mmHg"],
            ["Diastolic Blood Pressure", "88 mmHg"],
            ["Prescribed Medication 1", "Metformin 1000mg BID"],
            ["Prescribed Medication 2", "Lisinopril 10mg QD"],
            ["Attending Physician", "Dr. Gregory House"],
            ["Next Followup Date", "2026-11-15"],
        ],
    )

    # --- Archetype 2: Comparison ---
    corpus["cloud_comparison"] = TableData(
        headers=[["Capability / Metric", "AWS Cloud", "Google Cloud (GCP)", "Microsoft Azure"]],
        rows=[
            ["Primary Compute Service", "EC2", "Compute Engine", "Virtual Machines"],
            ["Managed Kubernetes", "EKS", "GKE", "AKS"],
            ["Serverless Functions", "AWS Lambda", "Cloud Functions", "Azure Functions"],
            ["Object Storage", "Amazon S3", "Cloud Storage", "Azure Blob Storage"],
            [
                "Managed Relational DB",
                "Amazon RDS / Aurora",
                "Cloud SQL / Spanner",
                "Azure SQL Database",
            ],
            [
                "Primary AI / LLM API",
                "Amazon Bedrock",
                "Vertex AI (Gemini)",
                "Azure OpenAI Service",
            ],
            [
                "Global Private Backbone",
                "100 Gbps dedicated",
                "High throughput Andromeda",
                "Global ExpressRoute",
            ],
            [
                "Max Single VM vCPUs",
                "448 vCPUs (u-24tb1)",
                "448 vCPUs (m3-ultragpu)",
                "416 vCPUs (M-series)",
            ],
            ["Max Single VM RAM", "24,576 GiB", "11,520 GiB", "11,400 GiB"],
            ["SLA Guarantee (Uptime)", "99.99%", "99.99%", "99.95%"],
        ],
    )

    corpus["model_benchmarks"] = TableData(
        headers=[["Benchmark Metric", "Gemini 1.5 Pro", "Claude 3.5 Sonnet", "GPT-4o"]],
        rows=[
            ["MMLU (Knowledge)", "85.9%", "88.7%", "87.2%"],
            ["HumanEval (Coding)", "84.1%", "92.0%", "90.2%"],
            ["GSM8K (Math Reasoning)", "91.7%", "96.4%", "95.8%"],
            ["MATH (Hard Math)", "58.5%", "78.3%", "76.6%"],
            ["Context Window Size", "2,000,000 tokens", "200,000 tokens", "128,000 tokens"],
            ["Multimodal Video Input", "Native 1hr+ Audio/Video", "No video", "Native frames"],
            ["Input Price per 1M", "$3.50", "$3.00", "$5.00"],
            ["Output Price per 1M", "$10.50", "$15.00", "$15.00"],
        ],
    )

    # --- Archetype 3: Time-Series ---
    corpus["financial_quarters"] = TableData(
        headers=[
            ["Financial Metric", "Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025", "Q2 2025"]
        ],
        rows=[
            ["Gross Revenue M", "$124.5", "$138.2", "$152.0", "$178.4", "$185.0", "$210.2"],
            ["Cost of Goods Sold M", "$42.1", "$45.0", "$49.2", "$58.0", "$60.2", "$66.5"],
            ["Gross Profit M", "$82.4", "$93.2", "$102.8", "$120.4", "$124.8", "$143.7"],
            ["R&D Expenses M", "$28.0", "$31.5", "$33.0", "$36.5", "$39.0", "$44.0"],
            ["Sales and Marketing M", "$22.0", "$24.0", "$26.5", "$31.0", "$32.0", "$35.5"],
            ["Operating Income M", "$32.4", "$37.7", "$43.3", "$52.9", "$53.8", "$64.2"],
            ["Net Profit Margin Pct", "26.0%", "27.3%", "28.5%", "29.7%", "29.1%", "30.5%"],
            ["Free Cash Flow M", "$25.1", "$29.4", "$34.0", "$45.2", "$46.8", "$55.0"],
        ],
    )

    corpus["server_telemetry"] = TableData(
        headers=[["Metric ID", "00:00", "04:00", "08:00", "12:00", "16:00", "20:00"]],
        rows=[
            ["CPU Utilization (%)", "18.2%", "14.5%", "64.8%", "89.2%", "84.5%", "45.0%"],
            ["Memory Usage (%)", "45.1%", "44.8%", "68.2%", "82.4%", "81.0%", "58.3%"],
            ["Disk IOPS (read/s)", "450", "320", "4200", "8900", "7800", "2100"],
            ["Network Inbound (Gbps)", "0.8", "0.4", "5.2", "9.4", "8.7", "3.2"],
            ["Network Outbound (Gbps)", "1.2", "0.6", "8.4", "18.2", "16.5", "6.1"],
            ["Active Request Rate (rps)", "1200", "800", "14500", "32000", "28000", "9500"],
            ["p99 Response Latency (ms)", "12ms", "10ms", "45ms", "125ms", "98ms", "28ms"],
        ],
    )

    # --- Archetype 4: Hierarchical ---
    corpus["org_chart"] = TableData(
        headers=[["Organization Role", "Employee Name", "Title", "Division", "Budget Authority"]],
        rows=[
            [
                "Executive Leadership",
                "Elena Rostova",
                "Chief Executive Officer",
                "Corporate",
                "$50,000,000",
            ],
            [
                "  Engineering VP",
                "Marcus Vance",
                "VP of Software Engineering",
                "Engineering",
                "$18,000,000",
            ],
            [
                "    Platform Director",
                "Sarah Chen",
                "Director of Infrastructure",
                "Platform",
                "$8,000,000",
            ],
            ["      Kubernetes Lead", "David Kumar", "Staff SRE Lead", "Infra Core", "$2,000,000"],
            [
                "      Storage Architect",
                "Emily Watson",
                "Principal Storage Eng",
                "Infra Data",
                "$1,500,000",
            ],
            [
                "    AI Director",
                "Liam O'Connor",
                "Director of Foundation Models",
                "AI Research",
                "$10,000,000",
            ],
            [
                "      Pretraining Lead",
                "Zheng Wei",
                "Senior Staff Scientist",
                "LLM Core",
                "$4,000,000",
            ],
            [
                "      Inference Lead",
                "Priya Sharma",
                "Staff ML Systems Eng",
                "Serving",
                "$3,000,000",
            ],
            ["  Product VP", "Chloe Dubois", "VP of Product Strategy", "Product", "$12,000,000"],
            [
                "    Enterprise PM",
                "James Wilson",
                "Group Product Manager",
                "B2B SaaS",
                "$4,000,000",
            ],
        ],
    )

    corpus["product_taxonomy"] = TableData(
        headers=[["Category Path", "SKU Prefix", "Margin (%)", "Target Market"]],
        rows=[
            ["Consumer Electronics", "CE-000", "35%", "Global Retail"],
            ["  Computers", "CE-CMP-00", "28%", "Consumer / Prosumer"],
            ["    Laptops", "CE-CMP-LAP", "25%", "Students & Office"],
            ["      Gaming Laptops", "CE-CMP-GAM", "32%", "Gamers & Creators"],
            ["      Ultrabooks", "CE-CMP-ULT", "27%", "Business Travelers"],
            ["    Desktops & Workstations", "CE-CMP-DSK", "22%", "Enterprise & Studios"],
            ["  Audio Gear", "CE-AUD-00", "52%", "Audiophiles & Commuters"],
            ["    Noise Cancelling Headphones", "CE-AUD-NCH", "58%", "Premium Travelers"],
            ["    True Wireless Earbuds", "CE-AUD-TWE", "48%", "Fitness & Daily Use"],
        ],
    )

    # --- Archetype 5: Matrix ---
    corpus["flight_costs"] = TableData(
        headers=[["Origin / Destination", "New York", "London", "Tokyo", "Singapore", "Sydney"]],
        rows=[
            ["New York", "0", "450", "980", "1150", "1450"],
            ["London", "450", "0", "780", "690", "1100"],
            ["Tokyo", "980", "780", "0", "320", "650"],
            ["Singapore", "1150", "690", "320", "0", "480"],
            ["Sydney", "1450", "1100", "650", "480", "0"],
        ],
    )

    corpus["asset_correlation"] = TableData(
        headers=[
            [
                "Asset Class",
                "US Equities",
                "Intl Equities",
                "Govt Bonds",
                "Real Estate",
                "Gold",
                "Crypto",
            ]
        ],
        rows=[
            ["US Equities", "1.00", "0.78", "-0.24", "0.62", "0.12", "0.45"],
            ["Intl Equities", "0.78", "1.00", "-0.18", "0.58", "0.19", "0.41"],
            ["Govt Bonds", "-0.24", "-0.18", "1.00", "-0.05", "0.32", "-0.15"],
            ["Real Estate", "0.62", "0.58", "-0.05", "1.00", "0.22", "0.28"],
            ["Gold", "0.12", "0.19", "0.32", "0.22", "1.00", "0.08"],
            ["Crypto", "0.45", "0.41", "-0.15", "0.28", "0.08", "1.00"],
        ],
    )

    # --- Archetype 6: Relational ---
    corpus["employee_projects"] = TableData(
        headers=[["EmpID", "Employee Name", "Department", "Role", "ProjectCode", "ReportsTo"]],
        rows=[
            ["E101", "Dr. Alan Turing", "Computing", "Fellow", "PRJ-ALPHA", "E100"],
            ["E102", "Ada Lovelace", "Computing", "Chief Architect", "PRJ-ALPHA", "E101"],
            ["E103", "Grace Hopper", "Compilers", "Principal Lead", "PRJ-BETA", "E101"],
            ["E104", "Claude Shannon", "Information", "Research Director", "PRJ-GAMMA", "E100"],
            ["E105", "Margaret Hamilton", "Systems", "Mission Director", "PRJ-DELTA", "E100"],
            ["E106", "John von Neumann", "Architecture", "Senior Fellow", "PRJ-ALPHA", "E100"],
            ["E107", "Barbara Liskov", "Systems", "Staff Architect", "PRJ-BETA", "E105"],
            ["E108", "Donald Knuth", "Algorithms", "Distinguished Eng", "PRJ-GAMMA", "E104"],
            ["E100", "Vannevar Bush", "Directorate", "Director General", "PRJ-CORP", "NONE"],
        ],
    )

    # --- Archetype 7: Pivot / Cross-Tab ---
    corpus["regional_sales_pivot"] = TableData(
        headers=[
            [
                "Region",
                "North America",
                "North America",
                "Europe",
                "Europe",
                "Asia Pacific",
                "Asia Pacific",
            ],
            [
                "Product Family",
                "Software ($k)",
                "Hardware ($k)",
                "Software ($k)",
                "Hardware ($k)",
                "Software ($k)",
                "Hardware ($k)",
            ],
        ],
        rows=[
            ["Enterprise Suite", "1250", "420", "980", "310", "1450", "620"],
            ["Cloud Analytics", "890", "150", "720", "110", "1100", "280"],
            ["Cybersecurity", "1680", "690", "1340", "540", "1890", "810"],
            ["AI Developer Tools", "2100", "850", "1750", "680", "2650", "1120"],
            ["Edge Computing", "450", "890", "390", "780", "620", "1350"],
        ],
    )

    # Archetype 7: Pivot / Cross-Tab (Extended Option A tables)
    corpus["temperature_map_option_a"] = TableData(
        headers=[
            ["Latitude", "Latitude", "Longitude", "Longitude", "Longitude", "Longitude"],
            ["From", "To", "From 100W", "From 110W", "From 120W", "From 130W"],
            ["", "", "To 110W", "To 120W", "To 130W", "To 140W"],
        ],
        rows=[
            ["30N", "40N", "68 F", "71 F", "73 F", "75 F"],
            ["40N", "50N", "54 F", "58 F", "60 F", "62 F"],
            ["50N", "60N", "42 F", "46 F", "48 F", "50 F"],
        ],
    )
    corpus["income_tax_brackets_option_a"] = TableData(
        headers=[
            ["Age", "Age", "Income", "Income", "Income", "Income"],
            ["From", "To", "From $0k", "From $50k", "From $100k", "From $200k"],
            ["", "", "To $50k", "To $100k", "To $200k", "To Max"],
        ],
        rows=[
            ["18", "30", "10.0%", "20.0%", "30.0%", "35.0%"],
            ["31", "55", "11.0%", "22.0%", "32.0%", "37.0%"],
            ["56", "75", "9.5%", "18.5%", "28.0%", "33.0%"],
        ],
    )
    corpus["logistics_shipping_option_a"] = TableData(
        headers=[
            ["Weight", "Weight", "Distance", "Distance", "Distance", "Distance"],
            ["From", "To", "From 0mi", "From 500mi", "From 1000mi", "From 2000mi"],
            ["", "", "To 500mi", "To 1000mi", "To 2000mi", "To Max"],
        ],
        rows=[
            ["0.0kg", "5.0kg", "$5.50", "$9.00", "$15.00", "$25.00"],
            ["5.1kg", "20.0kg", "$12.00", "$24.00", "$38.00", "$55.00"],
            ["20.1kg", "50.0kg", "$28.00", "$52.00", "$85.00", "$120.00"],
        ],
    )
    corpus["network_latency_sla_option_a"] = TableData(
        headers=[
            ["Packet Size", "Packet Size", "Bandwidth", "Bandwidth", "Bandwidth", "Bandwidth"],
            ["From", "To", "From 10M", "From 50M", "From 100M", "From 1G"],
            ["", "", "To 50M", "To 100M", "To 1G", "To 10G"],
        ],
        rows=[
            ["64B", "512B", "12 ms", "8 ms", "4 ms", "2 ms"],
            ["513B", "1500B", "22 ms", "15 ms", "10 ms", "5 ms"],
            ["1501B", "9000B", "45 ms", "32 ms", "25 ms", "15 ms"],
        ],
    )
    corpus["regional_property_values_option_a"] = TableData(
        headers=[
            ["Year Built", "Year Built", "Lot Size", "Lot Size", "Lot Size", "Lot Size"],
            ["From", "To", "From 0ac", "From 0.5ac", "From 1.0ac", "From 5.0ac"],
            ["", "", "To 0.5ac", "To 1.0ac", "To 5.0ac", "To Max"],
        ],
        rows=[
            ["1950", "1980", "$120k", "$180k", "$280k", "$450k"],
            ["1981", "2005", "$180k", "$260k", "$380k", "$600k"],
            ["2006", "2024", "$290k", "$420k", "$650k", "$950k"],
        ],
    )
    corpus["alloy_mix_matrix_option_a"] = TableData(
        headers=[
            ["Copper Mix", "Copper Mix", "Tin Mix", "Tin Mix", "Tin Mix", "Tin Mix"],
            ["From", "To", "From 36.5", "From 50.0", "From 60.0", "From 70.0"],
            ["", "", "To 50.0", "To 60.0", "To 70.0", "To 80.0"],
        ],
        rows=[
            ["10", "20", "17.44", "22.50", "28.10", "31.05"],
            ["20", "30", "19.80", "25.30", "31.20", "35.60"],
            ["30", "40", "22.10", "28.40", "34.50", "40.10"],
        ],
    )

    corpus["chemical_yield_option_a"] = TableData(
        headers=[
            ["Pressure", "Pressure", "Temperature", "Temperature", "Temperature", "Temperature"],
            ["From", "To", "From 100C", "From 150C", "From 200C", "From 250C"],
            ["", "", "To 150C", "To 200C", "To 250C", "To 300C"],
        ],
        rows=[
            ["1atm", "5atm", "45.2%", "52.8%", "60.1%", "65.5%"],
            ["6atm", "10atm", "55.0%", "63.2%", "71.4%", "78.0%"],
            ["11atm", "15atm", "62.5%", "70.8%", "80.2%", "88.5%"],
        ],
    )

    from benchmarks.long_tables import add_long_tables

    add_long_tables(corpus)

    return corpus


# ==============================================================================
# 2. 75 COMPREHENSIVE BENCHMARK QUERIES ACROSS COMPLEXITIES
# ==============================================================================


@dataclass
class BenchmarkQuery:
    query_id: int
    archetype: str
    complexity: str  # "Simple Lookup", "Relational Join", "Multi-Hop / Graph Reason", "Comparative / Aggregation"
    query_text: str
    target_tokens: list[str]


def generate_benchmark_queries() -> list[BenchmarkQuery]:
    q_list = [
        # --- Key-Value Queries (1-10) ---
        BenchmarkQuery(
            1,
            "Key-Value",
            "Simple Lookup",
            "What is the CPU model of prd-db-cluster-01?",
            ["EPYC", "9654"],
        ),
        BenchmarkQuery(
            2,
            "Key-Value",
            "Simple Lookup",
            "How much RAM is configured on the primary server?",
            ["768", "DDR5"],
        ),
        BenchmarkQuery(
            3,
            "Key-Value",
            "Simple Lookup",
            "What is the primary NVMe storage capacity?",
            ["3.84TB", "RAID-1"],
        ),
        BenchmarkQuery(
            4,
            "Key-Value",
            "Simple Lookup",
            "Which network interface card is installed?",
            ["ConnectX-6", "Mellanox"],
        ),
        BenchmarkQuery(
            5,
            "Key-Value",
            "Simple Lookup",
            "What operating system kernel is running?",
            ["Ubuntu", "6.8"],
        ),
        BenchmarkQuery(
            6,
            "Key-Value",
            "Simple Lookup",
            "What is patient PT-889104's primary diagnosis?",
            ["Diabetes", "Type 2"],
        ),
        BenchmarkQuery(
            7,
            "Key-Value",
            "Simple Lookup",
            "What is the recorded HbA1c level for patient PT-889104?",
            ["7.8", "HbA1c"],
        ),
        BenchmarkQuery(
            8,
            "Key-Value",
            "Simple Lookup",
            "What are the prescribed medications for the patient?",
            ["Metformin", "Lisinopril"],
        ),
        BenchmarkQuery(
            9,
            "Key-Value",
            "Simple Lookup",
            "Who is the attending physician for PT-889104?",
            ["House", "Gregory"],
        ),
        BenchmarkQuery(
            10,
            "Key-Value",
            "Simple Lookup",
            "What is the power supply redundancy configuration?",
            ["1600W", "Titanium"],
        ),
        # --- Comparison Queries (11-22) ---
        BenchmarkQuery(
            11,
            "Comparison",
            "Comparative / Aggregation",
            "Compare managed Kubernetes offerings between AWS and GCP",
            ["EKS", "GKE"],
        ),
        BenchmarkQuery(
            12,
            "Comparison",
            "Comparative / Aggregation",
            "What is Azure's serverless functions service called?",
            ["Azure Functions"],
        ),
        BenchmarkQuery(
            13,
            "Comparison",
            "Comparative / Aggregation",
            "Compare object storage service names across AWS, GCP, and Azure",
            ["S3", "Cloud Storage", "Blob"],
        ),
        BenchmarkQuery(
            14,
            "Comparison",
            "Comparative / Aggregation",
            "Which cloud provider offers the highest single VM RAM?",
            ["24,576", "AWS"],
        ),
        BenchmarkQuery(
            15,
            "Comparison",
            "Comparative / Aggregation",
            "What is the uptime SLA guarantee for Microsoft Azure?",
            ["99.95%"],
        ),
        BenchmarkQuery(
            16,
            "Comparison",
            "Comparative / Aggregation",
            "What are the primary LLM APIs on GCP and Azure?",
            ["Vertex", "Gemini", "Azure OpenAI"],
        ),
        BenchmarkQuery(
            17,
            "Comparison",
            "Comparative / Aggregation",
            "Compare HumanEval coding scores between Claude 3.5 Sonnet and GPT-4o",
            ["92.0%", "90.2%"],
        ),
        BenchmarkQuery(
            18,
            "Comparison",
            "Comparative / Aggregation",
            "Which model has a 2 million token context window?",
            ["Gemini 1.5 Pro", "2,000,000"],
        ),
        BenchmarkQuery(
            19,
            "Comparison",
            "Comparative / Aggregation",
            "Compare MATH reasoning scores of Claude 3.5 Sonnet vs Gemini 1.5 Pro",
            ["78.3%", "58.5%"],
        ),
        BenchmarkQuery(
            20,
            "Comparison",
            "Comparative / Aggregation",
            "What is the output token pricing per 1M for GPT-4o?",
            ["$15.00"],
        ),
        BenchmarkQuery(
            21,
            "Comparison",
            "Comparative / Aggregation",
            "Which model supports native 1 hour multimodal video input?",
            ["Gemini 1.5 Pro"],
        ),
        BenchmarkQuery(
            22,
            "Comparison",
            "Comparative / Aggregation",
            "Compare input token pricing between Claude 3.5 Sonnet and Gemini 1.5 Pro",
            ["$3.00", "$3.50"],
        ),
        # --- Time-Series Queries (23-34) ---
        BenchmarkQuery(
            23,
            "Time-Series",
            "Temporal Reasoning",
            "What was the gross revenue in Q1 2024 vs Q2 2025?",
            ["$124.5", "$210.2"],
        ),
        BenchmarkQuery(
            24,
            "Time-Series",
            "Temporal Reasoning",
            "How did Gross Profit change from Q3 2024 to Q4 2024?",
            ["$102.8", "$120.4"],
        ),
        BenchmarkQuery(
            25,
            "Time-Series",
            "Temporal Reasoning",
            "What was the Free Cash Flow in Q4 2024?",
            ["$45.2"],
        ),
        BenchmarkQuery(
            26,
            "Time-Series",
            "Temporal Reasoning",
            "Did R&D expenses increase in Q1 2025 compared to Q4 2024?",
            ["$39.0", "$36.5"],
        ),
        BenchmarkQuery(
            27,
            "Time-Series",
            "Temporal Reasoning",
            "What was the highest Net Profit Margin recorded in the financial periods?",
            ["30.5%"],
        ),
        BenchmarkQuery(
            28,
            "Time-Series",
            "Temporal Reasoning",
            "What was the CPU Utilization at peak hours 12:00 and 16:00?",
            ["89.2%", "84.5%"],
        ),
        BenchmarkQuery(
            29,
            "Time-Series",
            "Temporal Reasoning",
            "What was the p99 response latency at 00:00 vs 12:00?",
            ["12ms", "125ms"],
        ),
        BenchmarkQuery(
            30,
            "Time-Series",
            "Temporal Reasoning",
            "What was the disk IOPS during the quietest hour at 04:00?",
            ["320"],
        ),
        BenchmarkQuery(
            31,
            "Time-Series",
            "Temporal Reasoning",
            "What was the maximum network outbound bandwidth at 12:00?",
            ["18.2"],
        ),
        BenchmarkQuery(
            32,
            "Time-Series",
            "Temporal Reasoning",
            "How many active requests per second were handled at 12:00?",
            ["32000"],
        ),
        BenchmarkQuery(
            33,
            "Time-Series",
            "Temporal Reasoning",
            "What was the Cost of Goods Sold in Q2 2024?",
            ["$45.0"],
        ),
        BenchmarkQuery(
            34,
            "Time-Series",
            "Temporal Reasoning",
            "What was the Free Cash Flow in Q1 2024?",
            ["$25.1"],
        ),
        # --- Hierarchical Queries (35-46) ---
        BenchmarkQuery(
            35,
            "Hierarchical",
            "Hierarchy Navigation",
            "Who is the Chief Executive Officer at the top of the organization?",
            ["Elena Rostova"],
        ),
        BenchmarkQuery(
            36,
            "Hierarchical",
            "Hierarchy Navigation",
            "Who reports directly under VP of Software Engineering Marcus Vance?",
            ["Sarah Chen", "Liam O'Connor"],
        ),
        BenchmarkQuery(
            37,
            "Hierarchical",
            "Hierarchy Navigation",
            "What is the budget authority of AI Director Liam O'Connor?",
            ["$10,000,000"],
        ),
        BenchmarkQuery(
            38,
            "Hierarchical",
            "Hierarchy Navigation",
            "Who is the Staff SRE Lead under Platform Director Sarah Chen?",
            ["David Kumar"],
        ),
        BenchmarkQuery(
            39,
            "Hierarchical",
            "Hierarchy Navigation",
            "What is the title and division of Priya Sharma?",
            ["Staff ML Systems Eng", "Serving"],
        ),
        BenchmarkQuery(
            40,
            "Hierarchical",
            "Hierarchy Navigation",
            "What category path does Gaming Laptops belong to?",
            ["Computers", "Laptops"],
        ),
        BenchmarkQuery(
            41,
            "Hierarchical",
            "Hierarchy Navigation",
            "What is the profit margin of Noise Cancelling Headphones?",
            ["58%"],
        ),
        BenchmarkQuery(
            42,
            "Hierarchical",
            "Hierarchy Navigation",
            "What is the target market for True Wireless Earbuds?",
            ["Fitness & Daily Use"],
        ),
        BenchmarkQuery(
            43,
            "Hierarchical",
            "Hierarchy Navigation",
            "What is the SKU prefix for Desktops & Workstations?",
            ["CE-CMP-DSK"],
        ),
        BenchmarkQuery(
            44,
            "Hierarchical",
            "Hierarchy Navigation",
            "Which category has the highest profit margin in consumer audio?",
            ["58%", "Headphones"],
        ),
        BenchmarkQuery(
            45,
            "Hierarchical",
            "Hierarchy Navigation",
            "Who is the Group Product Manager under Product VP Chloe Dubois?",
            ["James Wilson"],
        ),
        BenchmarkQuery(
            46,
            "Hierarchical",
            "Hierarchy Navigation",
            "What is the title of Principal Storage Eng Emily Watson?",
            ["Principal Storage Eng"],
        ),
        # --- Matrix Queries (47-56) ---
        BenchmarkQuery(
            47,
            "Matrix",
            "Matrix Routing / Weighted Edge",
            "What is the flight cost from New York to Tokyo?",
            ["980"],
        ),
        BenchmarkQuery(
            48,
            "Matrix",
            "Matrix Routing / Weighted Edge",
            "What is the flight cost between London and Singapore?",
            ["690"],
        ),
        BenchmarkQuery(
            49,
            "Matrix",
            "Matrix Routing / Weighted Edge",
            "What is the flight cost between Tokyo and Sydney?",
            ["650"],
        ),
        BenchmarkQuery(
            50,
            "Matrix",
            "Matrix Routing / Weighted Edge",
            "What is the flight cost between New York and London?",
            ["450"],
        ),
        BenchmarkQuery(
            51,
            "Matrix",
            "Matrix Routing / Weighted Edge",
            "What is the correlation between US Equities and Govt Bonds?",
            ["-0.24"],
        ),
        BenchmarkQuery(
            52,
            "Matrix",
            "Matrix Routing / Weighted Edge",
            "What is the correlation between US Equities and Real Estate?",
            ["0.62"],
        ),
        BenchmarkQuery(
            53,
            "Matrix",
            "Matrix Routing / Weighted Edge",
            "What is the correlation between Gold and Govt Bonds?",
            ["0.32"],
        ),
        BenchmarkQuery(
            54,
            "Matrix",
            "Matrix Routing / Weighted Edge",
            "What is the correlation between Crypto and US Equities?",
            ["0.45"],
        ),
        BenchmarkQuery(
            55,
            "Matrix",
            "Matrix Routing / Weighted Edge",
            "What is the flight cost from Singapore to Tokyo?",
            ["320"],
        ),
        BenchmarkQuery(
            56,
            "Matrix",
            "Matrix Routing / Weighted Edge",
            "What is the correlation between Crypto and Govt Bonds?",
            ["-0.15"],
        ),
        # --- Relational Queries (57-66) ---
        BenchmarkQuery(
            57,
            "Relational",
            "Relational Foreign Key",
            "Who does Ada Lovelace report to?",
            ["Alan Turing", "E101"],
        ),
        BenchmarkQuery(
            58,
            "Relational",
            "Relational Foreign Key",
            "Which project code is assigned to Grace Hopper?",
            ["PRJ-BETA"],
        ),
        BenchmarkQuery(
            59,
            "Relational",
            "Relational Foreign Key",
            "What role and department does Claude Shannon have?",
            ["Research Director", "Information"],
        ),
        BenchmarkQuery(
            60,
            "Relational",
            "Relational Foreign Key",
            "Who is the Mission Director for project PRJ-DELTA?",
            ["Margaret Hamilton"],
        ),
        BenchmarkQuery(
            61,
            "Relational",
            "Relational Foreign Key",
            "Who reports to Margaret Hamilton?",
            ["Barbara Liskov", "E107"],
        ),
        BenchmarkQuery(
            62,
            "Relational",
            "Relational Foreign Key",
            "Which employee is assigned to PRJ-ALPHA as Senior Fellow?",
            ["John von Neumann"],
        ),
        BenchmarkQuery(
            63,
            "Relational",
            "Relational Foreign Key",
            "Who is the Director General at the top of the organization?",
            ["Vannevar Bush"],
        ),
        BenchmarkQuery(
            64,
            "Relational",
            "Relational Foreign Key",
            "What is Donald Knuth's title and who is his manager?",
            ["Distinguished Eng", "Claude Shannon"],
        ),
        BenchmarkQuery(
            65,
            "Relational",
            "Relational Foreign Key",
            "What project is Barbara Liskov working on?",
            ["PRJ-BETA"],
        ),
        BenchmarkQuery(
            66,
            "Relational",
            "Relational Foreign Key",
            "Which department does Alan Turing belong to?",
            ["Computing"],
        ),
        # --- Pivot / Cross-Tab Queries (67-75) ---
        BenchmarkQuery(
            67,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What was the Software revenue for AI Developer Tools in Asia Pacific?",
            ["2650"],
        ),
        BenchmarkQuery(
            68,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What was the Hardware revenue for Cybersecurity in North America?",
            ["690"],
        ),
        BenchmarkQuery(
            69,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What was the Software revenue for Enterprise Suite in Europe?",
            ["980"],
        ),
        BenchmarkQuery(
            70,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What was the Hardware revenue for Edge Computing in Asia Pacific?",
            ["1350"],
        ),
        BenchmarkQuery(
            71,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What was the Software revenue for Cloud Analytics in North America?",
            ["890"],
        ),
        BenchmarkQuery(
            72,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What was the Hardware revenue for AI Developer Tools in Europe?",
            ["680"],
        ),
        BenchmarkQuery(
            73,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What was the Software revenue for Cybersecurity in Asia Pacific?",
            ["1890"],
        ),
        BenchmarkQuery(
            74,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What was the Hardware revenue for Enterprise Suite in North America?",
            ["420"],
        ),
        BenchmarkQuery(
            75,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What was the Software revenue for Edge Computing in Europe?",
            ["390"],
        ),
        # --- Complex Pivot Option A Queries (76-100) ---
        BenchmarkQuery(
            76,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the temperature between Latitude 30N to 40N and Longitude 110W to 120W?",
            ["71 F"],
        ),
        BenchmarkQuery(
            77,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the temperature for Latitude 40N to 50N and Longitude 130W to 140W?",
            ["62 F"],
        ),
        BenchmarkQuery(
            78,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "For Latitude 50N to 60N, what is the temperature at Longitude 100W to 110W?",
            ["42 F"],
        ),
        BenchmarkQuery(
            79,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the temperature between Latitude 30N to 40N and Longitude 120W to 130W?",
            ["73 F"],
        ),
        BenchmarkQuery(
            80,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "For Latitude 50N to 60N, what is the temperature at Longitude 120W to 130W?",
            ["48 F"],
        ),
        BenchmarkQuery(
            81,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the income tax for age 18 to 30 earning $50k to $100k?",
            ["20.0%"],
        ),
        BenchmarkQuery(
            82,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the income tax for age 31 to 55 earning $100k to $200k?",
            ["32.0%"],
        ),
        BenchmarkQuery(
            83,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the tax rate for someone age 56 to 75 earning $200k to Max?",
            ["33.0%"],
        ),
        BenchmarkQuery(
            84,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the income tax for age 18 to 30 earning over $200k?",
            ["35.0%"],
        ),
        BenchmarkQuery(
            85,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the tax rate for someone age 31 to 55 earning $0k to $50k?",
            ["11.0%"],
        ),
        BenchmarkQuery(
            86,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the shipping cost for a 5.1kg to 20.0kg package sent 500mi to 1000mi?",
            ["$24.00"],
        ),
        BenchmarkQuery(
            87,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the cost to ship a 20.1kg to 50.0kg package over 2000mi?",
            ["$120.00"],
        ),
        BenchmarkQuery(
            88,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "How much to ship a 0.0kg to 5.0kg item 1000mi to 2000mi?",
            ["$15.00"],
        ),
        BenchmarkQuery(
            89,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the shipping cost for a 5.1kg to 20.0kg package sent 0mi to 500mi?",
            ["$12.00"],
        ),
        BenchmarkQuery(
            90,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the cost to ship a 20.1kg to 50.0kg package 500mi to 1000mi?",
            ["$52.00"],
        ),
        BenchmarkQuery(
            91,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the latency SLA for 513B to 1500B packets on a 50M to 100M bandwidth?",
            ["15 ms"],
        ),
        BenchmarkQuery(
            92,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the latency SLA for 1501B to 9000B packets on a 1G to 10G connection?",
            ["15 ms"],
        ),
        BenchmarkQuery(
            93,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the latency for 64B to 512B packets on a 100M to 1G connection?",
            ["4 ms"],
        ),
        BenchmarkQuery(
            94,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the latency SLA for 513B to 1500B packets on a 1G to 10G connection?",
            ["5 ms"],
        ),
        BenchmarkQuery(
            95,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the latency SLA for 1501B to 9000B packets on a 10M to 50M bandwidth?",
            ["45 ms"],
        ),
        BenchmarkQuery(
            96,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the property value for a house built 1981 to 2005 with a 0.5ac to 1.0ac lot?",
            ["$260k"],
        ),
        BenchmarkQuery(
            97,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the value of a property built 2006 to 2024 with a 5.0ac to Max lot size?",
            ["$950k"],
        ),
        BenchmarkQuery(
            98,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the property value for a house built 1950 to 1980 with a 1.0ac to 5.0ac lot?",
            ["$280k"],
        ),
        BenchmarkQuery(
            99,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the property value for a house built 1981 to 2005 with a 0ac to 0.5ac lot size?",
            ["$180k"],
        ),
        BenchmarkQuery(
            100,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the value of a property built 2006 to 2024 with a 1.0ac to 5.0ac lot size?",
            ["$650k"],
        ),
        # --- Additional Complex Pivot Option A Queries (101-110) ---
        BenchmarkQuery(
            101,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the yield for a pressure of 1atm to 5atm at a temperature of 100C to 150C?",
            ["45.2%"],
        ),
        BenchmarkQuery(
            102,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the part creation value for a copper mix of 10 to 20 and a tin mix of 36.5 to 50.0?",
            ["17.44"],
        ),
        BenchmarkQuery(
            103,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the yield for a pressure of 6atm to 10atm at a temperature of 200C to 250C?",
            ["71.4%"],
        ),
        BenchmarkQuery(
            104,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the part creation value for a copper mix of 20 to 30 and a tin mix of 50.0 to 60.0?",
            ["25.30"],
        ),
        BenchmarkQuery(
            105,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the yield for a pressure of 11atm to 15atm at a temperature of 250C to 300C?",
            ["88.5%"],
        ),
        BenchmarkQuery(
            106,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the part creation value for a copper mix of 30 to 40 and a tin mix of 70.0 to 80.0?",
            ["40.10"],
        ),
        BenchmarkQuery(
            107,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the yield for a pressure of 1atm to 5atm at a temperature of 200C to 250C?",
            ["60.1%"],
        ),
        BenchmarkQuery(
            108,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the part creation value for a copper mix of 10 to 20 and a tin mix of 60.0 to 70.0?",
            ["28.10"],
        ),
        BenchmarkQuery(
            109,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the yield for a pressure of 11atm to 15atm at a temperature of 100C to 150C?",
            ["62.5%"],
        ),
        BenchmarkQuery(
            110,
            "Pivot",
            "Multi-Dimensional Cross-Tab",
            "What is the part creation value for a copper mix of 30 to 40 and a tin mix of 36.5 to 50.0?",
            ["22.10"],
        ),
    ]
    return q_list


# ==============================================================================
# 3. BENCHMARK EXECUTION ENGINE
# ==============================================================================


def run_comprehensive_benchmark(verbose: bool = False):
    print("=" * 80)
    print("      TABLE-TO-GRAPH COMPREHENSIVE RAG RETRIEVAL BENCHMARK (120 QUERIES)      ")
    print("=" * 80)
    print("Corpus: 23 Diverse Tables across all 7 Structural Archetypes")
    print("Query Set: 120 Real-World Information Retrieval Tasks")
    print("Evaluating: target-token context hit rate, latency, and graph completeness\n")

    # Generate actual benchmark PDFs
    from benchmarks.generate_benchmark_pdfs import generate_all
    from table_to_graph import extract_tables

    print("Loading benchmark PDFs (generating only files that are missing)...")
    pdf_paths = generate_all()

    print("\nExtracting tables from PDFs...")
    corpus = {}
    for pdf_path in pdf_paths:
        pdf_name = pdf_path.name
        print(f"Extracting from {pdf_name}...")
        extracted_tables = extract_tables(str(pdf_path), classify=True)
        for idx, tbl in enumerate(extracted_tables):
            key = f"{pdf_name}_table_{idx}"
            corpus[key] = tbl
            method = getattr(tbl.metadata, "extraction_method", "pdfplumber")
            classification = getattr(tbl.metadata, "classification", None)
            table_type = classification.table_type if classification else "unclassified"
            if method == "tatr" or "staggered" in pdf_name:
                print(
                    f"  [{method}] {key}  type={table_type}  "
                    f"headers={len(tbl.headers)}  rows={len(tbl.rows)}"
                )
                if tbl.headers:
                    print(f"    Header[0]: {tbl.headers[0]}")
                if tbl.rows:
                    print(f"    Row[0]:    {tbl.rows[0]}")
    queries = generate_benchmark_queries()
    from benchmarks.long_tables import add_long_queries

    add_long_queries(queries)

    # Build Flat-Text Baseline Chunks
    flat_chunks: dict[str, list[str]] = {}
    for table_name, table in corpus.items():
        headers_str = " | ".join(str(h) for h in table.headers[0]) if table.headers else ""
        table_chunks = []
        for r_idx, row in enumerate(table.rows):
            row_str = " | ".join(str(c) for c in row)
            table_chunks.append(f"[{table_name} Row {r_idx}] {headers_str} => {row_str}")
        flat_chunks[table_name] = table_chunks

    # Build Graphs and GraphStore
    print("Building Typed Graph Knowledge Base...")
    t_start = time.perf_counter()
    graph_store = GraphStore()
    for name, table in corpus.items():
        # Handle cases where classification failed or table is garbage
        if (
            not hasattr(table.metadata, "classification")
            or table.metadata.classification.table_type == "unknown"
        ):
            print(f"  Skipping unclassified table: {name}")
            continue

        try:
            graph = build_graph(table)
            graph_store.add(graph)
        except KeyError:
            print(
                f"  Skipping table with unsupported archetype '{table.metadata.classification.table_type}': {name}"
            )
            continue

    t_graph_build = time.perf_counter() - t_start
    print(f"-> Indexed {len(graph_store)} graphs in {t_graph_build * 1000:.2f} ms\n")

    retriever = GraphRetriever(graph_store, top_k=10, k_hops=1)
    serializer = ContextSerializer(strategy="node-centric")

    # Execution tracking
    flat_latencies: list[float] = []
    graph_latencies: list[float] = []

    flat_hits = 0
    graph_hits = 0
    failed_queries: list[dict] = []

    complexity_stats: dict[str, dict[str, Any]] = {
        "Simple Lookup": {"count": 0, "flat_hits": 0, "graph_hits": 0, "graph_latencies": []},
        "Comparative / Aggregation": {
            "count": 0,
            "flat_hits": 0,
            "graph_hits": 0,
            "graph_latencies": [],
        },
        "Temporal Reasoning": {"count": 0, "flat_hits": 0, "graph_hits": 0, "graph_latencies": []},
        "Hierarchy Navigation": {
            "count": 0,
            "flat_hits": 0,
            "graph_hits": 0,
            "graph_latencies": [],
        },
        "Matrix Routing / Weighted Edge": {
            "count": 0,
            "flat_hits": 0,
            "graph_hits": 0,
            "graph_latencies": [],
        },
        "Relational Foreign Key": {
            "count": 0,
            "flat_hits": 0,
            "graph_hits": 0,
            "graph_latencies": [],
        },
        "Multi-Dimensional Cross-Tab": {
            "count": 0,
            "flat_hits": 0,
            "graph_hits": 0,
            "graph_latencies": [],
        },
    }

    # Execute all 75 queries
    for q in queries:
        # 1. Flat-Text Keyword Retrieval
        t0 = time.perf_counter()
        query_words = set(
            q.query_text.lower().replace("?", "").replace("'", "").replace(",", "").split()
        )
        best_flat_chunk = ""
        best_score = -1

        for chunks in flat_chunks.values():
            for chunk in chunks:
                chunk_lower = chunk.lower()
                score = sum(1 for w in query_words if w in chunk_lower)
                if score > best_score:
                    best_score = score
                    best_flat_chunk = chunk
        t_flat = time.perf_counter() - t0
        flat_latencies.append(t_flat)

        # Check if flat retrieved target tokens
        flat_has_all = all(target.lower() in best_flat_chunk.lower() for target in q.target_tokens)
        if flat_has_all:
            flat_hits += 1

        # 2. Table-to-Graph Subgraph Retrieval
        t0 = time.perf_counter()
        res = retriever.retrieve(q.query_text)
        graph_context = serializer.serialize(res)
        t_graph = time.perf_counter() - t0
        graph_latencies.append(t_graph)

        # Check if graph retrieved target tokens
        graph_has_all = all(target.lower() in graph_context.lower() for target in q.target_tokens)
        if graph_has_all:
            graph_hits += 1

        # Track failures for diagnostics
        if not graph_has_all:
            missing = [t for t in q.target_tokens if t.lower() not in graph_context.lower()]

            # Dump edge values from subgraph for this query
            edge_values = []
            for u, v, edata in res.subgraph.edges(data=True):
                val = edata.get("value", edata.get("weight", ""))
                if val:
                    edge_values.append(str(val))

            failed_queries.append(
                {
                    "id": q.query_id,
                    "complexity": q.complexity,
                    "query": q.query_text,
                    "target_tokens": q.target_tokens,
                    "missing_tokens": missing,
                    "seed_count": len(res.seed_nodes),
                    "seed_ids": res.seed_nodes[:5],
                    "subgraph_nodes": res.subgraph.number_of_nodes(),
                    "subgraph_edges": res.subgraph.number_of_edges(),
                    "edge_values_sample": edge_values[:20],
                    "context_snippet": graph_context[:600],
                }
            )

        # Update complexity breakdown
        comp = q.complexity
        if comp in complexity_stats:
            complexity_stats[comp]["count"] += 1
            if flat_has_all:
                complexity_stats[comp]["flat_hits"] += 1
            if graph_has_all:
                complexity_stats[comp]["graph_hits"] += 1
            complexity_stats[comp]["graph_latencies"].append(t_graph)

    # ==============================================================================
    # 4. REPORTING & SUMMARY METRICS
    # ==============================================================================

    total_q = len(queries)
    flat_acc = (flat_hits / total_q) * 100
    graph_acc = (graph_hits / total_q) * 100

    flat_latencies.sort()
    graph_latencies.sort()

    def p95(arr: list[float]) -> float:
        return arr[int(len(arr) * 0.95)]

    def median(arr: list[float]) -> float:
        return arr[len(arr) // 2]

    # Overall Summary Table
    overall_data = [
        ["Total Queries Evaluated", f"{total_q} Queries across 7 Archetypes"],
        ["Flat-Text Target-Token Hit Rate", f"{flat_hits}/{total_q} ({flat_acc:.1f}%)"],
        ["Table-to-Graph Target-Token Hit Rate", f"{graph_hits}/{total_q} ({graph_acc:.1f}%)"],
        ["Hit-Rate Improvement", f"+{graph_acc - flat_acc:.1f}% vs Baseline"],
        [
            "Table-to-Graph Mean Latency",
            f"{sum(graph_latencies) / len(graph_latencies) * 1000:.3f} ms",
        ],
        ["Table-to-Graph Median Latency", f"{median(graph_latencies) * 1000:.3f} ms"],
        ["Table-to-Graph p95 Latency", f"{p95(graph_latencies) * 1000:.3f} ms"],
    ]

    print("--- OVERALL BENCHMARK PERFORMANCE ---")
    print(tabulate(overall_data, headers=["Metric", "Result"], tablefmt="github"))
    print("\n")

    # Breakdown by Query Complexity Table
    breakdown_data = []
    for comp, stats in complexity_stats.items():
        cnt = stats["count"]
        if cnt == 0:
            continue
        f_p = (stats["flat_hits"] / cnt) * 100
        g_p = (stats["graph_hits"] / cnt) * 100
        avg_lat = (sum(stats["graph_latencies"]) / cnt) * 1000
        breakdown_data.append(
            [
                comp,
                cnt,
                f"{f_p:.1f}%",
                f"{g_p:.1f}%",
                f"+{g_p - f_p:.1f}%",
                f"{avg_lat:.2f} ms",
            ]
        )

    print("--- TARGET-TOKEN HIT-RATE BREAKDOWN BY STRUCTURAL COMPLEXITY ---")
    print(
        tabulate(
            breakdown_data,
            headers=[
                "Query Complexity Category",
                "Count",
                "Flat Baseline",
                "Table-to-Graph",
                "Win Margin",
                "Avg Latency",
            ],
            tablefmt="github",
        )
    )

    # Failure diagnostics
    if failed_queries:
        # Always print the one-line summary
        print(f"\n\n--- FAILED QUERY DIAGNOSTICS ({len(failed_queries)} failures) ---")
        if verbose:
            for fq in failed_queries:
                print(f"  Q{fq['id']:3d} [{fq['complexity']}]")
                print(f"       Query: {fq['query']}")
                print(f"       Expected: {fq['target_tokens']}")
                print(f"       Missing:  {fq['missing_tokens']}")
                print(f"       Seeds: {fq['seed_count']} | IDs: {fq['seed_ids']}")
                print(
                    f"       Subgraph: {fq['subgraph_nodes']} nodes, {fq['subgraph_edges']} edges"
                )
                print(f"       Edge values in subgraph: {fq['edge_values_sample']}")
                print("       Context (first 600 chars):")
                print(f"       {fq['context_snippet']}")
                print()
        else:
            for fq in failed_queries:
                print(f"  Q{fq['id']:3d} [{fq['complexity']}]  {fq['query']}")
            print("\n  Run with -v to see full diagnostics for each failure.")

    print("=" * 80)

    # Dynamic conclusion based on actual results
    perfect_cats = []
    best_margin_cat = ""
    best_margin_val = 0.0
    weak_cats = []

    for comp, stats in complexity_stats.items():
        cnt = stats["count"]
        if cnt == 0:
            continue
        g_p = (stats["graph_hits"] / cnt) * 100
        f_p = (stats["flat_hits"] / cnt) * 100
        margin = g_p - f_p

        if g_p == 100.0:
            perfect_cats.append(comp)
        elif g_p < 90.0:
            weak_cats.append((comp, g_p))

        if margin > best_margin_val:
            best_margin_val = margin
            best_margin_cat = comp

    conclusion = (
        f"CONCLUSION: table-to-graph achieves a {graph_acc:.1f}% target-token context "
        f"hit rate (+{graph_acc - flat_acc:.1f}% over the flat-text baseline)."
    )
    conclusion_parts = [conclusion]

    if perfect_cats:
        conclusion_parts.append(
            f"  100% target-token context hit rate on: {', '.join(perfect_cats)}."
        )

    if best_margin_cat:
        conclusion_parts.append(
            f"  Largest win margin: +{best_margin_val:.1f}% in {best_margin_cat}."
        )

    if weak_cats:
        weak_str = ", ".join(f"{cat} ({acc:.1f}%)" for cat, acc in weak_cats)
        conclusion_parts.append(f"  Areas for improvement: {weak_str}.")

    for line in conclusion_parts:
        print(line)

    print("=" * 80 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="table-to-graph RAG retrieval benchmark (120 queries)"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show full failed-query diagnostics (seeds, subgraph, context snippet)",
    )
    parser.add_argument(
        "-vv",
        "--debug",
        action="store_true",
        help="Show TATR exception tracebacks (DEBUG level, scoped to table_to_graph only)",
    )
    args = parser.parse_args()

    # Always silence noisy third-party loggers (pdfminer, huggingface, etc.)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s  %(name)s  %(message)s")

    if args.debug:
        # Only elevate OUR logger — never root
        logging.getLogger("table_to_graph").setLevel(logging.DEBUG)

    run_comprehensive_benchmark(verbose=args.verbose or args.debug)
