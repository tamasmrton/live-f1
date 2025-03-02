from unittest.mock import patch, mock_open, MagicMock
from typing import Dict, List
import pytest
from pathlib import Path
from reporting.query_registry import QueryRegistry


@pytest.fixture
def mock_sql_files() -> Dict[str, str]:
    # Mock SQL file contents
    files = {
        "query1.sql": "SELECT * FROM table1",
        "query2.sql": "SELECT * FROM table2",
    }
    return files


@pytest.fixture
def mock_path(mock_sql_files: Dict[str, str]) -> MagicMock:
    with patch("reporting.query_registry.Path") as mock_path_cls:
        # Create mock path instances for each file
        mock_files: List[MagicMock] = []
        for name in mock_sql_files.keys():
            mock_file = MagicMock(spec=Path)
            mock_file.name = name
            mock_file.open = mock_open(read_data=mock_sql_files[name])
            mock_files.append(mock_file)

        # Setup the path hierarchy
        mock_queries_path = MagicMock(spec=Path)
        mock_queries_path.glob.return_value = mock_files

        # Make Path().parent / "queries" return our mock queries path
        mock_path_cls.return_value.parent.__truediv__.return_value = mock_queries_path
        yield mock_queries_path


@pytest.fixture
def query_registry(mock_path: MagicMock) -> QueryRegistry:
    return QueryRegistry()


def test_fetch_queries(
    query_registry: QueryRegistry, mock_sql_files: Dict[str, str]
) -> None:
    """Test that queries are correctly fetched and stored"""
    assert len(query_registry.queries) == len(mock_sql_files)
    assert query_registry.queries["query1"] == "SELECT * FROM table1"
    assert query_registry.queries["query2"] == "SELECT * FROM table2"


def test_get_query(query_registry: QueryRegistry) -> None:
    """Test getting specific queries"""
    assert query_registry.get_query("query1") == "SELECT * FROM table1"
    assert query_registry.get_query("query2") == "SELECT * FROM table2"
    assert query_registry.get_query("nonexistent") is None


def test_list_queries(query_registry: QueryRegistry) -> None:
    """Test listing available queries"""
    query_list = query_registry.list_queries()
    assert isinstance(query_list, list)
    assert set(query_list) == {"query1", "query2"}


def test_init_creates_empty_queries_dict() -> None:
    """Test that initialization creates an empty queries dictionary"""
    with patch("reporting.query_registry.Path") as mock_path:
        mock_path.return_value.parent.__truediv__.return_value.glob.return_value = []
        registry = QueryRegistry()
        assert registry.queries == {}
