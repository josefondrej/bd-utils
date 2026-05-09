from typing import Any, Optional


def resolve_live_dbutils() -> Optional[Any]:
    """Attempt to resolve the live dbutils object in a Databricks environment.

    Returns:
        Optional[Any]: The dbutils object if found, otherwise None.
    """
    try:
        import IPython
    except Exception:
        return None

    shell = IPython.get_ipython()
    if shell is None:
        return None
    try:
        return shell.ns_table["user_global"]["dbutils"]
    except Exception:
        return None
