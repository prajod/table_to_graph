# Comprehensive 120 Q&A Retrieval Benchmark Report

This document provides a verifiable breakdown of all **120 Benchmark Queries** evaluated in `benchmarks/benchmark_retrieval.py` and `benchmarks/long_tables.py`.

---

## Benchmark Corpus & Methodology

- **Total Queries**: 120 real-world information retrieval tasks
- **Corpus**: 23 diverse tables across all 7 structural archetypes
- **Source Documents**:
  - `benchmark_tables_1.pdf` (Key-Value, Comparison, Time-Series)
  - `benchmark_tables_2.pdf` (Hierarchical, Matrix)
  - `benchmark_tables_3.pdf` (Relational, Pivot)
  - `benchmark_tables_4.pdf` (Option A Multi-level Pivot Tables: Temperature, Tax Brackets, Shipping, Latency, Property)
  - `benchmark_tables_5.pdf` (Synthetic Scaled Tables >150 rows)
  - `benchmark_staggered_alloy_table.pdf` (Standalone specialized staggering: Dual 'from' / Shared 'to' Alloy Mix Matrix)
- **Evaluation Criteria**: target-token context hit rate, latency, and neighborhood graph completeness.

A query is counted as a hit when every expected target token appears in the retrieved context.
This regression benchmark does not measure false-positive precision or LLM-generated answer quality.

---

## 1. Key-Value Archetype (Queries 1–10, 111–112)

### Source Tables:

- `server_specs` (`benchmark_tables_1.pdf`): Server hardware & kernel spec table.
- `clinical_patient` (`benchmark_tables_1.pdf`): Electronic Health Record (EHR) patient profile.
- `long_server_specs` (`benchmarks/long_tables.py`): 150-row server hardware specification table.

| ID      | Query                                                   | Target Tokens (Ground Truth)  | Complexity         | Retrieval Mechanics                                         |
| :------ | :------------------------------------------------------ | :---------------------------- | :----------------- | :---------------------------------------------------------- |
| **1**   | What is the CPU model of prd-db-cluster-01?             | `["EPYC", "9654"]`            | Simple Lookup      | Matches Property node `CPU Model` via `[HAS_PROPERTY]`      |
| **2**   | How much RAM is configured on the primary server?       | `["768", "DDR5"]`             | Simple Lookup      | Matches Property node `RAM Size`                            |
| **3**   | What is the primary NVMe storage capacity?              | `["3.84TB", "RAID-1"]`        | Simple Lookup      | Matches Property node `Primary Storage`                     |
| **4**   | Which network interface card is installed?              | `["ConnectX-6", "Mellanox"]`  | Simple Lookup      | Matches Property node `Network NIC`                         |
| **5**   | What operating system kernel is running?                | `["Ubuntu", "6.8"]`           | Simple Lookup      | Matches Property node `Operating System`                    |
| **6**   | What is patient PT-889104's primary diagnosis?          | `["Diabetes", "Type 2"]`      | Simple Lookup      | Matches Property node `Primary Diagnosis`                   |
| **7**   | What is the recorded HbA1c level for patient PT-889104? | `["7.8", "HbA1c"]`            | Simple Lookup      | Matches Property node `HbA1c Level`                         |
| **8**   | What are the prescribed medications for the patient?    | `["Metformin", "Lisinopril"]` | Multi-Hop          | Central Entity node brings all `[HAS_PROPERTY]` medications |
| **9**   | Who is the attending physician for PT-889104?           | `["House", "Gregory"]`        | Simple Lookup      | Matches Property node `Attending Physician`                 |
| **10**  | What is the power supply redundancy configuration?      | `["1600W", "Titanium"]`       | Simple Lookup      | Matches Property node `Power Redundancy`                    |
| **111** | What is the configured value for Component_125?         | `["Value_125_XYZ"]`           | Large-scale Lookup | Resolves deep 150-row key-value table index                 |
| **112** | What is the configured value for Component_88?          | `["Value_88_XYZ"]`            | Large-scale Lookup | Resolves deep 150-row key-value table index                 |

---

## 2. Comparison Archetype (Queries 11–22)

### Source Tables:

- `cloud_comparison` (`benchmark_tables_1.pdf`): AWS vs GCP vs Azure multi-cloud feature matrix.
- `model_benchmarks` (`benchmark_tables_1.pdf`): Gemini 1.5 Pro vs Claude 3.5 Sonnet vs GPT-4o capabilities.

| ID     | Query                                                                    | Target Tokens (Ground Truth)           | Complexity                | Retrieval Mechanics                                         |
| :----- | :----------------------------------------------------------------------- | :------------------------------------- | :------------------------ | :---------------------------------------------------------- |
| **11** | Compare managed Kubernetes offerings between AWS and GCP                 | `["EKS", "GKE"]`                       | Comparative / Aggregation | Entity-Attribute bipartite graph retrieves comparison edges |
| **12** | What is Azure's serverless functions service called?                     | `["Azure Functions"]`                  | Comparative / Aggregation | Matches Attribute node `Serverless Functions` $\to$ `Azure` |
| **13** | Compare object storage service names across AWS, GCP, and Azure          | `["S3", "Cloud Storage", "Blob"]`      | Comparative / Aggregation | Attribute node connects to all 3 cloud provider entities    |
| **14** | Which cloud provider offers the highest single VM RAM?                   | `["24,576", "AWS"]`                    | Comparative / Aggregation | Attribute node `Max Single VM RAM` links to values          |
| **15** | What is the uptime SLA guarantee for Microsoft Azure?                    | `["99.95%"]`                           | Comparative / Aggregation | Matches `SLA Guarantee` edge for `Azure`                    |
| **16** | What are the primary LLM APIs on GCP and Azure?                          | `["Vertex", "Gemini", "Azure OpenAI"]` | Comparative / Aggregation | Matches LLM API comparison row                              |
| **17** | Compare HumanEval coding scores between Claude 3.5 Sonnet and GPT-4o     | `["92.0%", "90.2%"]`                   | Comparative / Aggregation | Bipartite link for `HumanEval` across models                |
| **18** | Which model has a 2 million token context window?                        | `["Gemini 1.5 Pro", "2,000,000"]`      | Comparative / Aggregation | Value lookup to `Gemini 1.5 Pro` entity                     |
| **19** | Compare MATH reasoning scores of Claude 3.5 Sonnet vs Gemini 1.5 Pro     | `["78.3%", "58.5%"]`                   | Comparative / Aggregation | Bipartite link for `MATH` across models                     |
| **20** | What is the output token pricing per 1M for GPT-4o?                      | `["$15.00"]`                           | Comparative / Aggregation | Pricing attribute node connected to `GPT-4o`                |
| **21** | Which model supports native 1 hour multimodal video input?               | `["Gemini 1.5 Pro"]`                   | Comparative / Aggregation | Multimodal Video feature attribute link                     |
| **22** | Compare input token pricing between Claude 3.5 Sonnet and Gemini 1.5 Pro | `["$3.00", "$3.50"]`                   | Comparative / Aggregation | Input price attribute link                                  |

---

## 3. Time-Series Archetype (Queries 23–34, 113–114)

### Source Tables:

- `quarterly_financials` (`benchmark_tables_1.pdf`): 6 quarters of revenue, profit, R&D, and cash flow.
- `server_telemetry` (`benchmark_tables_1.pdf`): 24-hour server resource time-series metrics.
- `long_sales_data` (`benchmarks/long_tables.py`): 150-product quarterly performance series.

| ID      | Query                                                                     | Target Tokens (Ground Truth) | Complexity         | Retrieval Mechanics                                  |
| :------ | :------------------------------------------------------------------------ | :--------------------------- | :----------------- | :--------------------------------------------------- |
| **23**  | What was the gross revenue in Q1 2024 vs Q2 2025?                         | `["$124.5", "$210.2"]`       | Temporal Reasoning | Follows `NEXT` temporal chain across quarters        |
| **24**  | How did Gross Profit change from Q3 2024 to Q4 2024?                      | `["$102.8", "$120.4"]`       | Temporal Reasoning | Traverses adjacent `AT_TIME` metric nodes            |
| **25**  | What was the Free Cash Flow in Q4 2024?                                   | `["$45.2"]`                  | Temporal Reasoning | Links metric `Free Cash Flow` to TimePoint `Q4 2024` |
| **26**  | Did R&D expenses increase in Q1 2025 compared to Q4 2024?                 | `["$39.0", "$36.5"]`         | Temporal Reasoning | Multi-hop over `NEXT` edge between quarters          |
| **27**  | What was the highest Net Profit Margin recorded in the financial periods? | `["30.5%"]`                  | Temporal Reasoning | Metric node linked to all quarterly instances        |
| **28**  | What was the CPU Utilization at peak hours 12:00 and 16:00?               | `["89.2%", "84.5%"]`         | Temporal Reasoning | Telemetry metric linked to timestamp nodes           |
| **29**  | What was the p99 response latency at 00:00 vs 12:00?                      | `["12ms", "125ms"]`          | Temporal Reasoning | Latency metric traversal across time points          |
| **30**  | What was the disk IOPS during the quietest hour at 04:00?                 | `["320"]`                    | Temporal Reasoning | IOPS metric linked to 04:00 node                     |
| **31**  | What was the maximum network outbound bandwidth at 12:00?                 | `["18.2"]`                   | Temporal Reasoning | Bandwidth metric linked to 12:00 node                |
| **32**  | How many active requests per second were handled at 12:00?                | `["32000"]`                  | Temporal Reasoning | Requests metric linked to 12:00 node                 |
| **33**  | What was the Cost of Goods Sold in Q2 2024?                               | `["$45.0"]`                  | Temporal Reasoning | COGS metric linked to Q2 2024 node                   |
| **34**  | What was the Free Cash Flow in Q1 2024?                                   | `["$25.1"]`                  | Temporal Reasoning | FCF metric linked to Q1 2024 node                    |
| **113** | What were the Q3 sales for Product_142?                                   | `["$2130"]`                  | Scaled Temporal    | Resolves deep 150-row time-series graph              |
| **114** | What were the Q4 sales for Product_73?                                    | `["$1314"]`                  | Scaled Temporal    | Resolves deep 150-row time-series graph              |

---

## 4. Hierarchical Archetype (Queries 35–46)

### Source Tables:

- `corporate_org_chart` (`benchmark_tables_2.pdf`): Multi-tier executive, director, and lead hierarchy.
- `ecommerce_taxonomy` (`benchmark_tables_2.pdf`): Nested multi-level product catalog and pricing.

| ID     | Query                                                               | Target Tokens (Ground Truth)          | Complexity           | Retrieval Mechanics                                          |
| :----- | :------------------------------------------------------------------ | :------------------------------------ | :------------------- | :----------------------------------------------------------- |
| **35** | Who is the Chief Executive Officer at the top of the organization?  | `["Elena Rostova"]`                   | Hierarchy Navigation | Identifies root Category node                                |
| **36** | Who reports directly under VP of Software Engineering Marcus Vance? | `["Sarah Chen", "Liam O'Connor"]`     | Hierarchy Navigation | 1-hop outgoing `PARENT_OF` edges retrieve all direct reports |
| **37** | What is the budget authority of AI Director Liam O'Connor?          | `["$10,000,000"]`                     | Hierarchy Navigation | Retrieves properties attached to node                        |
| **38** | Who is the Staff SRE Lead under Platform Director Sarah Chen?       | `["David Kumar"]`                     | Hierarchy Navigation | Traverses `PARENT_OF` edge down to SRE Lead                  |
| **39** | What is the title and division of Priya Sharma?                     | `["Staff ML Systems Eng", "Serving"]` | Hierarchy Navigation | Category property match                                      |
| **40** | What category path does Gaming Laptops belong to?                   | `["Computers", "Laptops"]`            | Hierarchy Navigation | Inverted traversal via `PARENT_OF` / `ANCESTOR_OF`           |
| **41** | What is the profit margin of Noise Cancelling Headphones?           | `["58%"]`                             | Hierarchy Navigation | Product node property lookup                                 |
| **42** | What is the target market for True Wireless Earbuds?                | `["Fitness & Daily Use"]`             | Hierarchy Navigation | Product node property lookup                                 |
| **43** | What is the SKU prefix for Desktops & Workstations?                 | `["CE-CMP-DSK"]`                      | Hierarchy Navigation | Category node property lookup                                |
| **44** | Which category has the highest profit margin in consumer audio?     | `["58%", "Headphones"]`               | Hierarchy Navigation | Sub-tree traversal under Consumer Audio                      |
| **45** | Who is the Group Product Manager under Product VP Chloe Dubois?     | `["James Wilson"]`                    | Hierarchy Navigation | `PARENT_OF` traversal under Product VP                       |
| **46** | What is the title of Principal Storage Eng Emily Watson?            | `["Principal Storage Eng"]`           | Hierarchy Navigation | Category node title property match                           |

---

## 5. Matrix Archetype (Queries 47–56, 117–118)

### Source Tables:

- `flight_distances_costs` (`benchmark_tables_2.pdf`): Adjacency matrix of inter-city routes and flight costs.
- `asset_correlation_matrix` (`benchmark_tables_2.pdf`): Cross-asset portfolio correlation matrix.
- `long_flight_costs` (`benchmarks/long_tables.py`): 150-city weighted adjacency matrix.

| ID      | Query                                                        | Target Tokens (Ground Truth) | Complexity           | Retrieval Mechanics                            |
| :------ | :----------------------------------------------------------- | :--------------------------- | :------------------- | :--------------------------------------------- |
| **47**  | What is the flight cost from New York to Tokyo?              | `["980"]`                    | Weighted Edge        | Weighted edge between `New York` and `Tokyo`   |
| **48**  | What is the flight cost between London and Singapore?        | `["690"]`                    | Weighted Edge        | Weighted edge between `London` and `Singapore` |
| **49**  | What is the flight cost between Tokyo and Sydney?            | `["650"]`                    | Weighted Edge        | Weighted edge between `Tokyo` and `Sydney`     |
| **50**  | What is the flight cost between New York and London?         | `["450"]`                    | Weighted Edge        | Weighted edge between `New York` and `London`  |
| **51**  | What is the correlation between US Equities and Govt Bonds?  | `["-0.24"]`                  | Weighted Edge        | Symmetric weighted edge lookup                 |
| **52**  | What is the correlation between US Equities and Real Estate? | `["0.62"]`                   | Weighted Edge        | Symmetric weighted edge lookup                 |
| **53**  | What is the correlation between Gold and Govt Bonds?         | `["0.32"]`                   | Weighted Edge        | Symmetric weighted edge lookup                 |
| **54**  | What is the correlation between Crypto and US Equities?      | `["0.45"]`                   | Weighted Edge        | Symmetric weighted edge lookup                 |
| **55**  | What is the flight cost from Singapore to Tokyo?             | `["320"]`                    | Weighted Edge        | Weighted edge between `Singapore` and `Tokyo`  |
| **56**  | What is the correlation between Crypto and Govt Bonds?       | `["-0.15"]`                  | Weighted Edge        | Symmetric weighted edge lookup                 |
| **117** | What is the flight cost from City_115 to Dest_D?             | `["145"]`                    | Scaled Weighted Edge | Resolves deep 150-city matrix graph            |
| **118** | What is the flight cost from City_42 to Dest_B?              | `["52"]`                     | Scaled Weighted Edge | Resolves deep 150-city matrix graph            |

---

## 6. Relational Archetype (Queries 57–66, 115–116)

### Source Tables:

- `research_personnel` (`benchmark_tables_3.pdf`): Relational schema with Foreign Keys `ReportsTo` $\to$ `EmpID` and `ProjectCode`.
- `long_employee_list` (`benchmarks/long_tables.py`): 150-employee relational organization table.

| ID      | Query                                                       | Target Tokens (Ground Truth)              | Complexity        | Retrieval Mechanics                                              |
| :------ | :---------------------------------------------------------- | :---------------------------------------- | :---------------- | :--------------------------------------------------------------- |
| **57**  | Who does Ada Lovelace report to?                            | `["Alan Turing", "E101"]`                 | Foreign Key Join  | 1-hop BFS resolves `Ada Lovelace —[REFERENCES]→ Dr. Alan Turing` |
| **58**  | Which project code is assigned to Grace Hopper?             | `["PRJ-BETA"]`                            | Foreign Key Join  | Node property `ProjectCode`                                      |
| **59**  | What role and department does Claude Shannon have?          | `["Research Director", "Information"]`    | Foreign Key Join  | Node attributes `Role` and `Department`                          |
| **60**  | Who is the Mission Director for project PRJ-DELTA?          | `["Margaret Hamilton"]`                   | Foreign Key Join  | Node role match on `Mission Director`                            |
| **61**  | Who reports to Margaret Hamilton?                           | `["Barbara Liskov", "E107"]`              | Reverse FK Lookup | Incoming `REFERENCES` edge from Barbara Liskov                   |
| **62**  | Which employee is assigned to PRJ-ALPHA as Senior Fellow?   | `["John von Neumann"]`                    | Foreign Key Join  | Role and ProjectCode match                                       |
| **63**  | Who is the Director General at the top of the organization? | `["Vannevar Bush"]`                       | Foreign Key Join  | Root entity node lookup                                          |
| **64**  | What is Donald Knuth's title and who is his manager?        | `["Distinguished Eng", "Claude Shannon"]` | Foreign Key Join  | `REFERENCES` edge brings manager entity into context             |
| **65**  | What project is Barbara Liskov working on?                  | `["PRJ-BETA"]`                            | Foreign Key Join  | Node property `ProjectCode`                                      |
| **66**  | Which department does Alan Turing belong to?                | `["Computing"]`                           | Foreign Key Join  | Node property `Department`                                       |
| **115** | Which department is EMP-129 in?                             | `["Department 4"]`                        | Scaled FK Join    | Resolves deep 150-employee relational table                      |
| **116** | Who is the manager for Employee 67?                         | `["MGR-7"]`                               | Scaled FK Join    | Resolves deep 150-employee relational table                      |

---

## 7. Pivot / Cross-Tab Archetype (Queries 67–110, 119–120)

### Source Tables:

- `regional_sales_pivot` (`benchmark_tables_3.pdf`): Multi-tier regional product sales cross-tab.
- `temperature_map_option_a` (`benchmark_tables_4.pdf`): 2D spatial latitude $\times$ longitude grid.
- `income_tax_brackets_option_a` (`benchmark_tables_4.pdf`): Age bracket $\times$ income tier tax matrix.
- `logistics_shipping_option_a` (`benchmark_tables_4.pdf`): Weight $\times$ distance tier rate card.
- `network_latency_sla_option_a` (`benchmark_tables_4.pdf`): Packet size $\times$ bandwidth SLA matrix.
- `regional_property_values_option_a` (`benchmark_tables_4.pdf`): Year built $\times$ lot size valuation table.
- `chemical_yield_option_a` (`benchmark_tables_4.pdf`): Pressure $\times$ temperature chemical reaction yield table.
- `alloy_mix_matrix_option_a` (`benchmark_staggered_alloy_table.pdf`): Copper % $\times$ Tin % metallurgy mix table with staggered headers.
- `long_regional_sales` (`benchmarks/long_tables.py`): 150-region multi-year pivot table.

| ID      | Query                                                                  | Target Tokens (Ground Truth) | Complexity             | Retrieval Mechanics                                      |
| :------ | :--------------------------------------------------------------------- | :--------------------------- | :--------------------- | :------------------------------------------------------- |
| **67**  | What was the Software revenue for AI Developer Tools in Asia Pacific?  | `["2650"]`                   | Multi-Dim Pivot        | Links `AI Developer Tools` and `Asia Pacific > Software` |
| **68**  | What was the Hardware revenue for Cybersecurity in North America?      | `["690"]`                    | Multi-Dim Pivot        | Links `Cybersecurity` and `North America > Hardware`     |
| **69**  | What was the Software revenue for Enterprise Suite in Europe?          | `["980"]`                    | Multi-Dim Pivot        | Links `Enterprise Suite` and `Europe > Software`         |
| **70**  | What was the Hardware revenue for Edge Computing in Asia Pacific?      | `["1350"]`                   | Multi-Dim Pivot        | Links `Edge Computing` and `Asia Pacific > Hardware`     |
| **71**  | What was the Software revenue for Cloud Analytics in North America?    | `["890"]`                    | Multi-Dim Pivot        | Links `Cloud Analytics` and `North America > Software`   |
| **72**  | What was the Hardware revenue for AI Developer Tools in Europe?        | `["680"]`                    | Multi-Dim Pivot        | Links `AI Developer Tools` and `Europe > Hardware`       |
| **73**  | What was the Software revenue for Cybersecurity in Asia Pacific?       | `["1890"]`                   | Multi-Dim Pivot        | Links `Cybersecurity` and `Asia Pacific > Software`      |
| **74**  | What was the Hardware revenue for Enterprise Suite in North America?   | `["420"]`                    | Multi-Dim Pivot        | Links `Enterprise Suite` and `North America > Hardware`  |
| **75**  | What was the Software revenue for Edge Computing in Europe?            | `["390"]`                    | Multi-Dim Pivot        | Links `Edge Computing` and `Europe > Software`           |
| **76**  | What is the temperature between Lat 30N to 40N and Long 110W to 120W?  | `["71 F"]`                   | Multi-Dim Pivot        | Intersects row interval `30N-40N` with col `110W-120W`   |
| **77**  | What is the temperature for Lat 40N to 50N and Long 130W to 140W?      | `["62 F"]`                   | Multi-Dim Pivot        | Intersects row interval `40N-50N` with col `130W-140W`   |
| **78**  | For Lat 50N to 60N, what is the temp at Long 100W to 110W?             | `["42 F"]`                   | Multi-Dim Pivot        | Intersects row interval `50N-60N` with col `100W-110W`   |
| **79**  | What is the temp between Lat 30N to 40N and Long 120W to 130W?         | `["73 F"]`                   | Multi-Dim Pivot        | Intersects row interval `30N-40N` with col `120W-130W`   |
| **80**  | For Lat 50N to 60N, what is the temp at Long 120W to 130W?             | `["48 F"]`                   | Multi-Dim Pivot        | Intersects row interval `50N-60N` with col `120W-130W`   |
| **81**  | What is the income tax for age 18 to 30 earning $50k to $100k?         | `["20.0%"]`                  | Multi-Dim Pivot        | Intersects age range with income band                    |
| **82**  | What is the income tax for age 31 to 55 earning $100k to $200k?        | `["32.0%"]`                  | Multi-Dim Pivot        | Intersects age range with income band                    |
| **83**  | What is the tax rate for someone age 56 to 75 earning $200k to Max?    | `["33.0%"]`                  | Multi-Dim Pivot        | Intersects age range with top tier income                |
| **84**  | What is the income tax for age 18 to 30 earning over $200k?            | `["35.0%"]`                  | Multi-Dim Pivot        | Intersects young age with top tier bracket               |
| **85**  | What is the tax rate for someone age 31 to 55 earning $0k to $50k?     | `["11.0%"]`                  | Multi-Dim Pivot        | Intersects mid-age with base income band                 |
| **86**  | What is shipping for 5.1kg to 20.0kg package sent 500mi to 1000mi?     | `["$24.00"]`                 | Multi-Dim Pivot        | Intersects weight tier with distance tier                |
| **87**  | What is the cost to ship a 20.1kg to 50.0kg package over 2000mi?       | `["$120.00"]`                | Multi-Dim Pivot        | Intersects heavy weight with max distance                |
| **88**  | How much to ship a 0.0kg to 5.0kg item 1000mi to 2000mi?               | `["$15.00"]`                 | Multi-Dim Pivot        | Intersects light weight with 1000-2000mi tier            |
| **89**  | What is shipping for 5.1kg to 20.0kg package sent 0mi to 500mi?        | `["$12.00"]`                 | Multi-Dim Pivot        | Intersects mid-weight with local tier                    |
| **90**  | What is the cost to ship a 20.1kg to 50.0kg package 500mi to 1000mi?   | `["$52.00"]`                 | Multi-Dim Pivot        | Intersects heavy weight with 500-1000mi tier             |
| **91**  | What is the latency SLA for 513B to 1500B packets on 50M to 100M?      | `["15 ms"]`                  | Multi-Dim Pivot        | Intersects packet size range with bandwidth              |
| **92**  | What is the latency SLA for 1501B to 9000B packets on 1G to 10G?       | `["15 ms"]`                  | Multi-Dim Pivot        | Intersects jumbo frames with 1G-10G pipe                 |
| **93**  | What is the latency for 64B to 512B packets on 100M to 1G?             | `["4 ms"]`                   | Multi-Dim Pivot        | Intersects small packet with high-speed pipe             |
| **94**  | What is the latency SLA for 513B to 1500B packets on 1G to 10G?        | `["5 ms"]`                   | Multi-Dim Pivot        | Intersects medium packet with high-speed pipe            |
| **95**  | What is the latency SLA for 1501B to 9000B packets on 10M to 50M?      | `["45 ms"]`                  | Multi-Dim Pivot        | Intersects jumbo frames with low-speed pipe              |
| **96**  | What is the value for house built 1981-2005 with 0.5ac-1.0ac lot?      | `["$260k"]`                  | Multi-Dim Pivot        | Intersects year built vintage with lot size              |
| **97**  | What is the value of property built 2006-2024 with 5.0ac+ lot?         | `["$950k"]`                  | Multi-Dim Pivot        | Intersects modern build with large lot                   |
| **98**  | What is the property value for house built 1950-1980 with 1.0ac-5.0ac? | `["$280k"]`                  | Multi-Dim Pivot        | Intersects older build with mid-large lot                |
| **99**  | What is the property value for house built 1981-2005 with 0-0.5ac lot? | `["$180k"]`                  | Multi-Dim Pivot        | Intersects vintage build with standard lot               |
| **100** | What is the value of property built 2006-2024 with 1.0ac-5.0ac lot?    | `["$650k"]`                  | Multi-Dim Pivot        | Intersects modern build with medium lot                  |
| **101** | What is the yield for 1atm-5atm at 100C-150C?                          | `["45.2%"]`                  | Multi-Dim Pivot        | Intersects pressure with low temperature                 |
| **102** | What is the part creation value for copper 10-20 and tin 36.5-50.0?    | `["17.44"]`                  | Multi-Dim Pivot        | Intersects copper ratio with tin ratio                   |
| **103** | What is the yield for 6atm-10atm at 200C-250C?                         | `["71.4%"]`                  | Multi-Dim Pivot        | Intersects mid pressure with high temp                   |
| **104** | What is the part creation value for copper 20-30 and tin 50.0-60.0?    | `["25.30"]`                  | Multi-Dim Pivot        | Intersects mid copper with mid tin                       |
| **105** | What is the yield for 11atm-15atm at 250C-300C?                        | `["88.5%"]`                  | Multi-Dim Pivot        | Intersects high pressure with high temp                  |
| **106** | What is the part creation value for copper 30-40 and tin 70.0-80.0?    | `["40.10"]`                  | Multi-Dim Pivot        | Intersects high copper with high tin                     |
| **107** | What is the yield for 1atm-5atm at 200C-250C?                          | `["60.1%"]`                  | Multi-Dim Pivot        | Intersects low pressure with high temp                   |
| **108** | What is the part creation value for copper 10-20 and tin 60.0-70.0?    | `["28.10"]`                  | Multi-Dim Pivot        | Intersects low copper with high tin                      |
| **109** | What is the yield for 11atm-15atm at 100C-150C?                        | `["62.5%"]`                  | Multi-Dim Pivot        | Intersects high pressure with low temp                   |
| **110** | What is the part creation value for copper 30-40 and tin 36.5-50.0?    | `["22.10"]`                  | Multi-Dim Pivot        | Intersects high copper with low tin                      |
| **119** | What were 2024 H1 sales for Region_133 in SubRegion_133?               | `["532"]`                    | Scaled Multi-Dim Pivot | Resolves deep 150-region pivot table                     |
| **120** | What were 2023 H2 sales for Region_56 in SubRegion_56?                 | `["168"]`                    | Scaled Multi-Dim Pivot | Resolves deep 150-region pivot table                     |

---

## Architectural Advantages: Graph vs Flat-Text Chunks

1. **Foreign Key Multi-Hop Traversal (Relational)**:
   - _Flat chunk baseline_: Only contains local row tokens (e.g. `ReportsTo: E101`). An LLM has no access to the referenced employee's name without a second search.
   - _Table-to-Graph_: 1-hop BFS traverses `Ada Lovelace —[REFERENCES]→ Dr. Alan Turing`, returning both connected entities in a single synthesized context block.

2. **Parent-Child Hierarchy Traversal (Trees / Org Charts)**:
   - _Flat chunk baseline_: Indented lines are split across chunk boundaries or lose depth semantics.
   - _Table-to-Graph_: `PARENT_OF` and `ANCESTOR_OF` edges explicitly link directors to all child leads, allowing queries like _"Who reports under Marcus Vance?"_ to retrieve the complete sub-tree.

3. **Adjacency & Routing Lookups (Matrices)**:
   - _Flat chunk baseline_: High dimensionality and duplicate city names cause ambiguous token matching.
   - _Table-to-Graph_: Explicit weighted edges `Node(Origin) —[CONNECTED(weight)]→ Node(Destination)` directly represent pairwise relations.

4. **Multi-Dimensional Intersection (Pivot / Cross-Tabs)**:
   - _Flat chunk baseline_: Multi-level headers (e.g. _Region $\to$ Product Family $\to$ Metric_) are flattened into plain text, causing cell-to-header mapping errors.
   - _Table-to-Graph_: `Measure` nodes are connected to multidimensional `Dimension` nodes, preserving exact cell-coordinate provenance.
