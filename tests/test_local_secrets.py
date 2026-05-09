import pytest

import bdutils
from bdutils.exceptions import SecretNotDefinedError


def test_secret_from_env(monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)
    monkeypatch.setenv("DBX_SECRET__scope__key", "abc123")
    assert bdutils.secrets.get("scope", "key") == "abc123"


def test_secret_missing_raises(monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)
    with pytest.raises(SecretNotDefinedError):
        bdutils.secrets.get("scope", "missing")


def test_secret_bytes_and_listing(monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)
    monkeypatch.setenv("DBX_SECRET__scope__key2", "hello")
    assert bdutils.secrets.getBytes("scope", "key2") == b"hello"
    assert any(m.key == "key2" for m in bdutils.secrets.list("scope"))
    assert any(s.name == "scope" for s in bdutils.secrets.listScopes())
