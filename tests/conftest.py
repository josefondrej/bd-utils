import pytest

import bdutils
from bdutils.config import BdUtilsConfig
from bdutils.core import get_dbutils


@pytest.fixture(scope="session")
def test_root(tmp_path_factory):
    """Create a root directory for all tests and clean it up after session."""
    root = tmp_path_factory.mktemp("bd-utils-tests")
    yield root
    # Optional: explicit cleanup if desired, though pytest handles tmp_path_factory
    # shutil.rmtree(root, ignore_errors=True)


@pytest.fixture(autouse=True)
def clean_dbutils(tmp_path, monkeypatch):
    """Ensure dbutils uses a temporary directory for each test and resets state."""
    # Create a fresh config pointing to a subdirectory of tmp_path
    dbfs_root = tmp_path / "dbfs"
    dbfs_root.mkdir(parents=True, exist_ok=True)
    config = BdUtilsConfig(dbfs_root=dbfs_root)

    # Get a fresh local dbutils instance
    local_dbutils = get_dbutils(config=config, force_adapter="local")

    # Mock the singleton in the bdutils module
    monkeypatch.setattr(bdutils, "dbutils", local_dbutils)

    yield local_dbutils
