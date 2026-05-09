import pytest

import bdutils
from bdutils.exceptions import WidgetNotDefinedError


def test_widgets_text_and_get(monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)
    bdutils.widgets.removeAll()
    bdutils.widgets.text("country", "cz")
    assert bdutils.widgets.get("country") == "cz"


def test_widgets_get_from_env(monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)
    bdutils.widgets.removeAll()
    monkeypatch.setenv("DBX_WIDGET_COUNTRY", "sk")
    assert bdutils.widgets.get("country") == "sk"


def test_widgets_get_missing_raises(monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)
    bdutils.widgets.removeAll()
    with pytest.raises(WidgetNotDefinedError):
        bdutils.widgets.get("missing")


def test_widgets_shape_includes_databricks_commands(monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)
    assert hasattr(bdutils.widgets, "combobox")
    assert hasattr(bdutils.widgets, "dropdown")
    assert hasattr(bdutils.widgets, "multiselect")
    assert hasattr(bdutils.widgets, "getArgument")
