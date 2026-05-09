import bdutils


def test_module_alias_drop_in_shape():
    assert hasattr(bdutils, "fs")
    assert hasattr(bdutils, "widgets")
    assert hasattr(bdutils, "secrets")
    assert hasattr(bdutils, "notebook")


def test_module_alias_calls_work():
    bdutils.widgets.text("country", "cz")
    assert bdutils.widgets.get("country") == "cz"
