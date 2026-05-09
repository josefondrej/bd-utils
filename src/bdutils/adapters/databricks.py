from typing import Any, Optional


def resolve_live_dbutils() -> Optional[Any]:
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
