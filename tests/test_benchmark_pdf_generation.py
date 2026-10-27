from benchmarks.generate_benchmark_pdfs import generate_all


def test_generate_all_reuses_existing_pdfs(tmp_path):
    expected_names = [
        "benchmark_tables_1.pdf",
        "benchmark_tables_2.pdf",
        "benchmark_tables_3.pdf",
        "benchmark_tables_4.pdf",
        "benchmark_tables_5.pdf",
        "benchmark_staggered_alloy_table.pdf",
    ]
    sentinel = b"existing benchmark fixture"
    for name in expected_names:
        (tmp_path / name).write_bytes(sentinel)

    paths = generate_all(tmp_path)

    assert [path.name for path in paths] == expected_names
    assert all(path.read_bytes() == sentinel for path in paths)
