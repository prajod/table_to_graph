from benchmarks.benchmark_retrieval import BenchmarkQuery
from table_to_graph.models import TableData


def add_long_tables(corpus: dict[str, TableData]):
    # 1. Long Server Specs (Key-Value)
    rows_1 = []
    for i in range(1, 150):
        rows_1.append([f"Component_{i}", f"Value_{i}_XYZ"])
    corpus["long_server_specs"] = TableData(
        headers=[["Specification Field", "Configured Value"]], rows=rows_1
    )

    # 2. Long Sales Data (Time-Series)
    rows_2 = []
    for i in range(1, 150):
        rows_2.append([f"Product_{i}", f"${i * 10}", f"${i * 12}", f"${i * 15}", f"${i * 18}"])
    corpus["long_sales_data"] = TableData(
        headers=[["Product", "Q1", "Q2", "Q3", "Q4"]], rows=rows_2
    )

    # 3. Long Employee List (Relational)
    rows_3 = []
    for i in range(1, 150):
        rows_3.append([f"EMP-{i:03d}", f"Employee {i}", f"Department {i % 5}", f"MGR-{i % 10}"])
    corpus["long_employee_list"] = TableData(
        headers=[["Employee ID", "Name", "Department", "Manager ID"]], rows=rows_3
    )

    # 4. Long Matrix (Matrix Routing)
    rows_4 = []
    for i in range(1, 150):
        rows_4.append([f"City_{i}", str(i), str(i + 10), str(i + 20), str(i + 30), str(i + 40)])
    corpus["long_flight_costs"] = TableData(
        headers=[["Origin / Destination", "Dest_A", "Dest_B", "Dest_C", "Dest_D", "Dest_E"]],
        rows=rows_4,
    )

    # 5. Long Pivot (Multi-Dimensional Cross-Tab)
    rows_5 = []
    for i in range(1, 150):
        rows_5.append(
            [f"Region_{i}", f"SubRegion_{i}", str(i * 2), str(i * 3), str(i * 4), str(i * 5)]
        )
    corpus["long_regional_sales"] = TableData(
        headers=[
            ["Region", "SubRegion", "2023", "2023", "2024", "2024"],
            ["", "", "H1", "H2", "H1", "H2"],
        ],
        rows=rows_5,
    )


def add_long_queries(queries: list[BenchmarkQuery]):
    queries.extend(
        [
            BenchmarkQuery(
                111,
                "Key-Value",
                "Simple Lookup",
                "What is the configured value for Component_125?",
                ["Value_125_XYZ"],
            ),
            BenchmarkQuery(
                112,
                "Key-Value",
                "Simple Lookup",
                "What is the configured value for Component_88?",
                ["Value_88_XYZ"],
            ),
            BenchmarkQuery(
                113,
                "Time-Series",
                "Temporal Reasoning",
                "What were the Q3 sales for Product_142?",
                ["$2130"],
            ),
            BenchmarkQuery(
                114,
                "Time-Series",
                "Temporal Reasoning",
                "What were the Q4 sales for Product_73?",
                ["$1314"],
            ),
            BenchmarkQuery(
                115,
                "Relational",
                "Relational Foreign Key",
                "Which department is EMP-129 in?",
                ["Department 4"],
            ),
            BenchmarkQuery(
                116,
                "Relational",
                "Relational Foreign Key",
                "Who is the manager for Employee 67?",
                ["MGR-7"],
            ),
            BenchmarkQuery(
                117,
                "Matrix",
                "Matrix Routing / Weighted Edge",
                "What is the flight cost from City_115 to Dest_D?",
                ["145"],
            ),
            BenchmarkQuery(
                118,
                "Matrix",
                "Matrix Routing / Weighted Edge",
                "What is the flight cost from City_42 to Dest_B?",
                ["52"],
            ),
            BenchmarkQuery(
                119,
                "Pivot",
                "Multi-Dimensional Cross-Tab",
                "What were the 2024 H1 sales for Region_133 in SubRegion_133?",
                ["532"],
            ),
            BenchmarkQuery(
                120,
                "Pivot",
                "Multi-Dimensional Cross-Tab",
                "What were the 2023 H2 sales for Region_56 in SubRegion_56?",
                ["168"],
            ),
        ]
    )
