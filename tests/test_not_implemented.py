import pytest

import bdutils


def test_credentials_not_implemented():
    with pytest.raises(NotImplementedError) as excinfo:
        _ = bdutils.credentials
    assert "dbutils.credentials is not supported in local adapter yet." in str(excinfo.value)


def test_data_not_implemented():
    with pytest.raises(NotImplementedError) as excinfo:
        _ = bdutils.data
    assert "dbutils.data is not supported in local adapter yet." in str(excinfo.value)


def test_library_not_implemented():
    with pytest.raises(NotImplementedError) as excinfo:
        _ = bdutils.library
    assert "dbutils.library is not supported in local adapter yet." in str(excinfo.value)


def test_meta_not_implemented():
    with pytest.raises(NotImplementedError) as excinfo:
        _ = bdutils.meta
    assert "dbutils.meta is not supported in local adapter yet." in str(excinfo.value)


def test_preview_not_implemented():
    with pytest.raises(NotImplementedError) as excinfo:
        _ = bdutils.preview
    assert "dbutils.preview is not supported in local adapter yet." in str(excinfo.value)


def test_api_not_implemented():
    with pytest.raises(NotImplementedError) as excinfo:
        _ = bdutils.api
    assert "dbutils.api is not supported in local adapter yet." in str(excinfo.value)


def test_file_info_not_implemented():
    # Verify that dbutils.FileInfo (which exists in Databricks) raises NotImplementedError
    with pytest.raises(NotImplementedError) as excinfo:
        _ = bdutils.FileInfo
    assert "dbutils.FileInfo is not supported in local adapter yet." in str(excinfo.value)
