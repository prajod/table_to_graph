import pytest

from table_to_graph.models import PipelineConfig, TableData, TableMetadata


@pytest.fixture
def sample_metadata():
    return TableMetadata(
        source_file="test.pdf",
        page_number=1,
        table_index=0,
        bbox=(10.0, 20.0, 100.0, 200.0),
        extraction_method="test",
    )


@pytest.fixture
def sample_table_data(sample_metadata):
    return TableData(
        headers=[["Name", "Age", "City"]],
        rows=[["Alice", "30", "New York"], ["Bob", "25", "London"], ["Charlie", None, "Paris"]],
        metadata=sample_metadata,
    )


@pytest.fixture
def default_config():
    return PipelineConfig()
