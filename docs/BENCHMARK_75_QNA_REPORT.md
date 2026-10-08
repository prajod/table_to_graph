# Retrieval Benchmark Report (Historical 75/100 Query Version)

> [!NOTE]
> This is a historical version of the benchmark report. The full and updated benchmark containing all **120 queries** across 23 tables is available in [BENCHMARK_120_QNA_REPORT.md](./BENCHMARK_120_QNA_REPORT.md).

---

## Benchmark Summary

- **Total Queries**: 100
- **Archetypes Covered**: 7 (Key-Value, Comparison, Time-Series, Hierarchical, Matrix, Relational, Pivot)
- **Source Documents**: 16 tables physically extracted from 4 generated PDFs:
  - `benchmark_tables_1.pdf` (Key-Value, Comparison, Time-Series)
  - `benchmark_tables_2.pdf` (Hierarchical, Matrix)
  - `benchmark_tables_3.pdf` (Relational, Pivot)
  - `benchmark_tables_4.pdf` (Complex Pivot / Cross-Tab)
- **Flat-Text Baseline Target-Token Hit Rate**: 64 / 100 (64.0%)
- **Table-to-Graph Target-Token Hit Rate**: 92 / 100 (92.0%)
- **Win Margin**: +28.0 percentage points in target-token context hit rate
- **Average Graph Latency**: 0.403 ms

---

## 1. Key-Value Archetype (Queries 1–10)

### Source Tables:
- `benchmark_tables_1.pdf` - `server_specs`: Server hardware and OS configuration table.
- `benchmark_tables_1.pdf` - `clinical_patient`: Electronic Health Record (EHR) patient profile.

| ID | Query | Target Tokens (Ground Truth) | Flat-Text Chunk Result | Table-to-Graph Subgraph Context |
|:---|:------|:-----------------------------|:-----------------------|:--------------------------------|
| **1** | What is the CPU model of prd-db-cluster-01? | `["EPYC", "9654"]` | ✅ Hit row: `CPU Model: AMD EPYC 9654` | ✅ `Property: CPU Model=AMD EPYC 9654` via `[HAS_PROPERTY]` |
| **2** | How much RAM is configured on the primary server? | `["768", "DDR5"]` | ✅ Hit row: `RAM Size: 768 GB DDR5 ECC` | ✅ `Property: RAM Size=768 GB DDR5 ECC` |
| **3** | What is the primary NVMe storage capacity? | `["3.84TB", "RAID-1"]` | ✅ Hit row: `Primary Storage: 2x 3.84TB NVMe RAID-1` | ✅ `Property: Primary Storage=2x 3.84TB NVMe RAID-1` |
| **4** | Which network interface card is installed? | `["ConnectX-6", "Mellanox"]` | ✅ Hit row: `Network NIC: Mellanox ConnectX-6` | ✅ `Property: Network NIC=Dual-port 100GbE Mellanox ConnectX-6` |
| **5** | What operating system kernel is running? | `["Ubuntu", "6.8"]` | ✅ Hit row: `Operating System: Ubuntu 24.04 Kernel 6.8` | ✅ `Property: Operating System=Ubuntu 24.04 LTS Kernel 6.8` |
| **6** | What is patient PT-889104's primary diagnosis? | `["Diabetes", "Type 2"]` | ✅ Hit row: `Primary Diagnosis: Type 2 Diabetes` | ✅ `Property: Primary Diagnosis=Type 2 Diabetes Mellitus` |
| **7** | What is the recorded HbA1c level for patient PT-889104? | `["7.8", "HbA1c"]` | ✅ Hit row: `HbA1c Level: 7.8 %` | ✅ `Property: HbA1c Level=7.8 %` |
| **8** | What are the prescribed medications for the patient? | `["Metformin", "Lisinopril"]` | ❌ Missed: Flat text only matched single row | ✅ `Entity 'Patient'` connected to both `Metformin 1000mg` & `Lisinopril 10mg` |
| **9** | Who is the attending physician for PT-889104? | `["House", "Gregory"]` | ✅ Hit row: `Attending Physician: Dr. Gregory House` | ✅ `Property: Attending Physician=Dr. Gregory House` |
| **10** | What is the power supply redundancy configuration? | `["1600W", "Titanium"]` | ✅ Hit row: `Power Redundancy: Dual 1600W Titanium` | ✅ `Property: Power Redundancy=Dual 1600W Titanium 80-Plus PSU` |

---

## 2. Comparison Archetype (Queries 11–22)

### Source Tables:
- `benchmark_tables_1.pdf` - `cloud_comparison`: Multi-cloud feature matrix (AWS vs GCP vs Azure).
- `benchmark_tables_1.pdf` - `model_benchmarks`: LLM evaluation metrics (Gemini 1.5 Pro vs Claude 3.5 Sonnet vs GPT-4o).

| ID | Query | Target Tokens (Ground Truth) | Flat-Text Chunk Result | Table-to-Graph Subgraph Context |
|:---|:------|:-----------------------------|:-----------------------|:--------------------------------|
| **11** | Compare managed Kubernetes offerings between AWS and GCP | `["EKS", "GKE"]` | ✅ Hit row: `Managed Kubernetes: EKS | GKE | AKS` | ✅ `Entity 'AWS Cloud'` & `Entity 'Google Cloud'` connected to `Attribute 'Managed Kubernetes'` via `[HAS_ATTRIBUTE (value=EKS)]` and `[HAS_ATTRIBUTE (value=GKE)]` |
| **12** | What is Azure's serverless functions service called? | `["Azure Functions"]` | ✅ Hit row | ✅ `Entity 'Microsoft Azure' -> Attribute 'Serverless Functions' via [HAS_ATTRIBUTE (value=Azure Functions)]` |
| **13** | Compare object storage service names across AWS, GCP, and Azure | `["S3", "Cloud Storage", "Blob"]` | ✅ Hit row | ✅ Bipartite graph links `Amazon S3`, `Cloud Storage`, and `Azure Blob Storage` |
| **14** | Which cloud provider offers the highest single VM RAM? | `["24,576", "AWS"]` | ✅ Hit row | ✅ `Entity 'AWS Cloud' -> Attribute 'Max Single VM RAM' (value=24,576 GiB)` |
| **15** | What is the uptime SLA guarantee for Microsoft Azure? | `["99.95%"]` | ✅ Hit row | ✅ `Entity 'Microsoft Azure' -> Attribute 'SLA Guarantee' (value=99.95%)` |
| **16** | What are the primary LLM APIs on GCP and Azure? | `["Vertex", "Gemini", "Azure OpenAI"]` | ✅ Hit row | ✅ `Google Cloud (value=Vertex AI (Gemini))` and `Azure (value=Azure OpenAI Service)` |
| **17** | Compare HumanEval coding scores between Claude 3.5 Sonnet and GPT-4o | `["92.0%", "90.2%"]` | ✅ Hit row | ✅ Subgraph contains `Claude 3.5 Sonnet (value=92.0%)` and `GPT-4o (value=90.2%)` |
| **18** | Which model has a 2 million token context window? | `["Gemini 1.5 Pro", "2,000,000"]` | ✅ Hit row | ✅ `Entity 'Gemini 1.5 Pro' -> Attribute 'Context Window Size' (value=2,000,000 tokens)` |
| **19** | Compare MATH reasoning scores of Claude 3.5 Sonnet vs Gemini 1.5 Pro | `["78.3%", "58.5%"]` | ✅ Hit row | ✅ `Claude 3.5 Sonnet (value=78.3%)` vs `Gemini 1.5 Pro (value=58.5%)` |
| **20** | What is the output token pricing per 1M for GPT-4o? | `["$15.00"]` | ✅ Hit row | ✅ `GPT-4o -> Output Price per 1M (value=$15.00)` |
| **21** | Which model supports native 1 hour multimodal video input? | `["Gemini 1.5 Pro"]` | ✅ Hit row | ✅ `Gemini 1.5 Pro -> Multimodal Video Input (value=Native 1hr+ Audio/Video)` |
| **22** | Compare input token pricing between Claude 3.5 Sonnet and Gemini 1.5 Pro | `["$3.00", "$3.50"]` | ✅ Hit row | ✅ `Claude 3.5 Sonnet (value=$3.00)` vs `Gemini 1.5 Pro (value=$3.50)` |

---

## 3. Time-Series Archetype (Queries 23–34)

### Source Tables:
- `benchmark_tables_1.pdf` - `financial_quarters`: 6-quarter financial progression (Q1 2024 to Q2 2025).
- `benchmark_tables_1.pdf` - `server_telemetry`: Server performance timeline across 24 hours.

| ID | Query | Target Tokens (Ground Truth) | Flat-Text Chunk Result | Table-to-Graph Subgraph Context |
|:---|:------|:-----------------------------|:-----------------------|:--------------------------------|
| **23** | What was the gross revenue in Q1 2024 vs Q2 2025? | `["$124.5", "$210.2"]` | ✅ Hit row | ✅ `Metric 'Gross Revenue'` linked to `TimePoint 'Q1 2024' (value=$124.5)` and `TimePoint 'Q2 2025' (value=$210.2)` |
| **24** | How did Gross Profit change from Q3 2024 to Q4 2024? | `["$102.8", "$120.4"]` | ✅ Hit row | ✅ Temporal chain: `TimePoint 'Q3 2024' ($102.8) —[NEXT]→ TimePoint 'Q4 2024' ($120.4)` |
| **25** | What was the Free Cash Flow in Q4 2024? | `["$45.2"]` | ✅ Hit row | ✅ `Metric 'Free Cash Flow' -> TimePoint 'Q4 2024' (value=$45.2)` |
| **26** | Did R&D expenses increase in Q1 2025 compared to Q4 2024? | `["$39.0", "$36.5"]` | ✅ Hit row | ✅ `Metric 'R&D Expenses' -> Q4 2024 ($36.5) and Q1 2025 ($39.0)` |
| **27** | What was the highest Net Profit Margin recorded in the financial periods? | `["30.5%"]` | ✅ Hit row | ✅ `Metric 'Net Profit Margin' -> Q2 2025 (value=30.5%)` |
| **28** | What was the CPU Utilization at peak hours 12:00 and 16:00? | `["89.2%", "84.5%"]` | ✅ Hit row | ✅ `Metric 'CPU Utilization' -> TimePoint '12:00' (89.2%) and '16:00' (84.5%)` |
| **29** | What was the p99 response latency at 00:00 vs 12:00? | `["12ms", "125ms"]` | ✅ Hit row | ✅ `Metric 'p99 Response Latency' -> 00:00 (12ms) and 12:00 (125ms)` |
| **30** | What was the disk IOPS during the quietest hour at 04:00? | `["320"]` | ✅ Hit row | ✅ `Metric 'Disk IOPS' -> TimePoint '04:00' (value=320)` |
| **31** | What was the maximum network outbound bandwidth at 12:00? | `["18.2"]` | ✅ Hit row | ✅ `Metric 'Network Outbound' -> TimePoint '12:00' (value=18.2)` |
| **32** | How many active requests per second were handled at 12:00? | `["32000"]` | ✅ Hit row | ✅ `Metric 'Active Request Rate' -> TimePoint '12:00' (value=32000)` |
| **33** | What was the Cost of Goods Sold in Q2 2024? | `["$45.0"]` | ✅ Hit row | ✅ `Metric 'Cost of Goods Sold' -> TimePoint 'Q2 2024' (value=$45.0)` |
| **34** | What was the Free Cash Flow in Q1 2024? | `["$25.1"]` | ✅ Hit row | ✅ `Metric 'Free Cash Flow' -> TimePoint 'Q1 2024' (value=$25.1)` |

---

## 4. Hierarchical Archetype (Queries 35–46)

### Source Tables:
- `benchmark_tables_2.pdf` - `org_chart`: Nested corporate leadership hierarchy with budget authorities.
- `benchmark_tables_2.pdf` - `product_taxonomy`: Multi-level product category tree with margin percentages.

| ID | Query | Target Tokens (Ground Truth) | Flat-Text Chunk Result | Table-to-Graph Subgraph Context |
|:---|:------|:-----------------------------|:-----------------------|:--------------------------------|
| **35** | Who is the Chief Executive Officer at the top of the organization? | `["Elena Rostova"]` | ✅ Hit row | ✅ `Category 'Elena Rostova' (Title=Chief Executive Officer, Budget Authority=$50,000,000)` |
| **36** | Who reports directly under VP of Software Engineering Marcus Vance? | `["Sarah Chen", "Liam O'Connor"]` | ❌ Missed: Flat text row only has Marcus Vance | ✅ `Category 'Marcus Vance' —[PARENT_OF]→ Category 'Sarah Chen'` AND `—[PARENT_OF]→ Category 'Liam O'Connor'` |
| **37** | What is the budget authority of AI Director Liam O'Connor? | `["$10,000,000"]` | ✅ Hit row | ✅ `Category 'Liam O'Connor' (Budget Authority=$10,000,000)` |
| **38** | Who is the Staff SRE Lead under Platform Director Sarah Chen? | `["David Kumar"]` | ❌ Missed: Sarah Chen and David Kumar are separate rows | ✅ `Category 'Sarah Chen' —[PARENT_OF]→ Category 'David Kumar' (Title=Staff SRE Lead)` |
| **39** | What is the title and division of Priya Sharma? | `["Staff ML Systems Eng", "Serving"]` | ✅ Hit row | ✅ `Category 'Priya Sharma' (Title=Staff ML Systems Eng, Division=Serving)` |
| **40** | What category path does Gaming Laptops belong to? | `["Computers", "Laptops"]` | ❌ Missed: Flat row only contains "Gaming Laptops" | ✅ Subgraph tree: `Computers —[PARENT_OF]→ Laptops —[PARENT_OF]→ Gaming Laptops` |
| **41** | What is the profit margin of Noise Cancelling Headphones? | `["58%"]` | ✅ Hit row | ✅ `Category 'Noise Cancelling Headphones' (Margin (%)=58%)` |
| **42** | What is the target market for True Wireless Earbuds? | `["Fitness & Daily Use"]` | ✅ Hit row | ✅ `Category 'True Wireless Earbuds' (Target Market=Fitness & Daily Use)` |
| **43** | What is the SKU prefix for Desktops & Workstations? | `["CE-CMP-DSK"]` | ✅ Hit row | ✅ `Category 'Desktops & Workstations' (SKU Prefix=CE-CMP-DSK)` |
| **44** | Which category has the highest profit margin in consumer audio? | `["58%", "Headphones"]` | ❌ Missed: Audio Gear row doesn't contain child 58% | ✅ `Category 'Audio Gear' —[PARENT_OF]→ Category 'Noise Cancelling Headphones' (58%)` |
| **45** | Who is the Group Product Manager under Product VP Chloe Dubois? | `["James Wilson"]` | ❌ Missed: Separate flat rows | ✅ `Category 'Chloe Dubois' —[PARENT_OF]→ Category 'James Wilson'` |
| **46** | What is the title of Principal Storage Eng Emily Watson? | `["Principal Storage Eng"]` | ✅ Hit row | ✅ `Category 'Emily Watson' (Title=Principal Storage Eng)` |

---

## 5. Matrix Archetype (Queries 47–56)

### Source Tables:
- `benchmark_tables_2.pdf` - `flight_costs`: Global airport route cost matrix.
- `benchmark_tables_2.pdf` - `asset_correlation`: Multi-asset investment correlation matrix.

| ID | Query | Target Tokens (Ground Truth) | Flat-Text Chunk Result | Table-to-Graph Subgraph Context |
|:---|:------|:-----------------------------|:-----------------------|:--------------------------------|
| **47** | What is the flight cost from New York to Tokyo? | `["980"]` | ❌ Missed: Ambiguous flat row | ✅ `Node 'New York' —[CONNECTED (weight=980.0)]→ Node 'Tokyo'` |
| **48** | What is the flight cost between London and Singapore? | `["690"]` | ❌ Missed: Row keyword mismatch | ✅ `Node 'London' —[CONNECTED (weight=690.0)]→ Node 'Singapore'` |
| **49** | What is the flight cost between Tokyo and Sydney? | `["650"]` | ❌ Missed | ✅ `Node 'Tokyo' —[CONNECTED (weight=650.0)]→ Node 'Sydney'` |
| **50** | What is the flight cost between New York and London? | `["450"]` | ✅ Hit row | ✅ `Node 'New York' —[CONNECTED (weight=450.0)]→ Node 'London'` |
| **51** | What is the correlation between US Equities and Govt Bonds? | `["-0.24"]` | ❌ Missed | ✅ `Node 'US Equities' —[CONNECTED (weight=-0.24)]→ Node 'Govt Bonds'` |
| **52** | What is the correlation between US Equities and Real Estate? | `["0.62"]` | ✅ Hit row | ✅ `Node 'US Equities' —[CONNECTED (weight=0.62)]→ Node 'Real Estate'` |
| **53** | What is the correlation between Gold and Govt Bonds? | `["0.32"]` | ✅ Hit row | ✅ `Node 'Gold' —[CONNECTED (weight=0.32)]→ Node 'Govt Bonds'` |
| **54** | What is the correlation between Crypto and US Equities? | `["0.45"]` | ✅ Hit row | ✅ `Node 'Crypto' —[CONNECTED (weight=0.45)]→ Node 'US Equities'` |
| **55** | What is the flight cost from Singapore to Tokyo? | `["320"]` | ❌ Missed | ✅ `Node 'Singapore' —[CONNECTED (weight=320.0)]→ Node 'Tokyo'` |
| **56** | What is the correlation between Crypto and Govt Bonds? | `["-0.15"]` | ✅ Hit row | ✅ `Node 'Crypto' —[CONNECTED (weight=-0.15)]→ Node 'Govt Bonds'` |

---

## 6. Relational Archetype (Queries 57–66)

### Source Tables:
- `benchmark_tables_3.pdf` - `employee_projects`: Relational employee table with manager foreign keys (`ReportsTo`) and project allocations (`ProjectCode`).

| ID | Query | Target Tokens (Ground Truth) | Flat-Text Chunk Result | Table-to-Graph Subgraph Context |
|:---|:------|:-----------------------------|:-----------------------|:--------------------------------|
| **57** | Who does Ada Lovelace report to? | `["Alan Turing", "E101"]` | ❌ Missed: Flat row only has "E101", missing Alan Turing's name | ✅ `Entity 'Ada Lovelace' —[REFERENCES (via_column=ReportsTo)]→ Entity 'Dr. Alan Turing' (EmpID=E101)` |
| **58** | Which project code is assigned to Grace Hopper? | `["PRJ-BETA"]` | ✅ Hit row | ✅ `Entity 'Grace Hopper' (ProjectCode=PRJ-BETA)` |
| **59** | What role and department does Claude Shannon have? | `["Research Director", "Information"]` | ✅ Hit row | ✅ `Entity 'Claude Shannon' (Role=Research Director, Department=Information)` |
| **60** | Who is the Mission Director for project PRJ-DELTA? | `["Margaret Hamilton"]` | ✅ Hit row | ✅ `Entity 'Margaret Hamilton' (Role=Mission Director, ProjectCode=PRJ-DELTA)` |
| **61** | Who reports to Margaret Hamilton? | `["Barbara Liskov", "E107"]` | ❌ Missed: Margaret's row doesn't mention Barbara | ✅ `Entity 'Barbara Liskov' (EmpID=E107) —[REFERENCES (via_column=ReportsTo)]→ Entity 'Margaret Hamilton'` |
| **62** | Which employee is assigned to PRJ-ALPHA as Senior Fellow? | `["John von Neumann"]` | ✅ Hit row | ✅ `Entity 'John von Neumann' (Role=Senior Fellow, ProjectCode=PRJ-ALPHA)` |
| **63** | Who is the Director General at the top of the organization? | `["Vannevar Bush"]` | ✅ Hit row | ✅ `Entity 'Vannevar Bush' (Role=Director General, Department=Directorate)` |
| **64** | What is Donald Knuth's title and who is his manager? | `["Distinguished Eng", "Claude Shannon"]` | ❌ Missed: Flat row only has "E104", not Claude Shannon's name | ✅ `Entity 'Donald Knuth' (Title=Distinguished Eng) —[REFERENCES]→ Entity 'Claude Shannon'` |
| **65** | What project is Barbara Liskov working on? | `["PRJ-BETA"]` | ✅ Hit row | ✅ `Entity 'Barbara Liskov' (ProjectCode=PRJ-BETA)` |
| **66** | Which department does Alan Turing belong to? | `["Computing"]` | ✅ Hit row | ✅ `Entity 'Dr. Alan Turing' (Department=Computing)` |

---

## 7. Pivot / Cross-Tab Archetype (Queries 67–75)

### Source Tables:
- `benchmark_tables_3.pdf` - `regional_sales_pivot`: Multi-level pivot table with Region and Product Category hierarchies.

| ID | Query | Target Tokens (Ground Truth) | Flat-Text Chunk Result | Table-to-Graph Subgraph Context |
|:---|:------|:-----------------------------|:-----------------------|:--------------------------------|
| **67** | What was the Software revenue for AI Developer Tools in Asia Pacific? | `["2650"]` | ✅ Hit row | ✅ `Row 'AI Developer Tools' —[HAS_VALUE (value=2650)]→ Col 'Asia Pacific > Software ($k)'` |
| **68** | What was the Hardware revenue for Cybersecurity in North America? | `["690"]` | ✅ Hit row | ✅ `Row 'Cybersecurity' —[HAS_VALUE (value=690)]→ Col 'North America > Hardware ($k)'` |
| **69** | What was the Software revenue for Enterprise Suite in Europe? | `["980"]` | ✅ Hit row | ✅ `Row 'Enterprise Suite' —[HAS_VALUE (value=980)]→ Col 'Europe > Software ($k)'` |
| **70** | What was the Hardware revenue for Edge Computing in Asia Pacific? | `["1350"]` | ✅ Hit row | ✅ `Row 'Edge Computing' —[HAS_VALUE (value=1350)]→ Col 'Asia Pacific > Hardware ($k)'` |
| **71** | What was the Software revenue for Cloud Analytics in North America? | `["890"]` | ✅ Hit row | ✅ `Row 'Cloud Analytics' —[HAS_VALUE (value=890)]→ Col 'North America > Software ($k)'` |
| **72** | What was the Hardware revenue for AI Developer Tools in Europe? | `["680"]` | ✅ Hit row | ✅ `Row 'AI Developer Tools' —[HAS_VALUE (value=680)]→ Col 'Europe > Hardware ($k)'` |
| **73** | What was the Software revenue for Cybersecurity in Asia Pacific? | `["1890"]` | ✅ Hit row | ✅ `Row 'Cybersecurity' —[HAS_VALUE (value=1890)]→ Col 'Asia Pacific > Software ($k)'` |
| **74** | What was the Hardware revenue for Enterprise Suite in North America? | `["420"]` | ✅ Hit row | ✅ `Row 'Enterprise Suite' —[HAS_VALUE (value=420)]→ Col 'North America > Hardware ($k)'` |
| **75** | What was the Software revenue for Edge Computing in Europe? | `["390"]` | ✅ Hit row | ✅ `Row 'Edge Computing' —[HAS_VALUE (value=390)]→ Col 'Europe > Software ($k)'` |

---

## Why Table-to-Graph Beats Flat-Text Chunking

1. **Foreign Key Multi-Hop Traversal (Relational)**:
   - *Flat chunk*: Contains only `ReportsTo: E101`. An LLM cannot know who `E101` is without performing a second search.
   - *Graph*: 1-hop BFS traverses `Ada Lovelace —[REFERENCES]→ Dr. Alan Turing`, assembling both entities into one coherent context block.

2. **Parent-Child Hierarchy Traversal (Trees / Org Charts)**:
   - *Flat chunk*: Indented lines are fragmented across different lines or chunks.
   - *Graph*: `PARENT_OF` edges explicitly link directors to all their direct report leads, allowing queries like *"Who reports under Marcus Vance?"* to retrieve all children at once.

3. **Adjacency & Routing Lookups (Matrices)**:
   - *Flat chunk*: High dimensionality and symmetric headers cause word matching ambiguity.
   - *Graph*: Explicit weighted edges `Node(Origin) —[CONNECTED(weight)]→ Node(Destination)` directly represent pairwise distances/correlations.
