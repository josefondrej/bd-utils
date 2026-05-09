import os
from typing import Any, Optional

from bdutils.adapters.databricks import resolve_live_dbutils
from bdutils.adapters.local import LocalDbutils
from bdutils.config import BdUtilsConfig


def _is_probably_databricks() -> bool:
    """Check if the current environment is likely Databricks.

    Returns:
        bool: True if Databricks runtime or dbutils are detected, False otherwise.
    """
    if os.environ.get("DATABRICKS_RUNTIME_VERSION"):
        return True
    return resolve_live_dbutils() is not None


def get_dbutils(
    config: Optional[BdUtilsConfig] = None,
    force_adapter: Optional[str] = None,
    databricks_dbutils: Optional[Any] = None,
):
    """Get the appropriate dbutils instance.

    Args:
        config (Optional[BdUtilsConfig]): Configuration object.
        force_adapter (Optional[str]): Explicitly choose 'local' or 'databricks'.
        databricks_dbutils (Optional[Any]): Existing databricks dbutils instance.

    Returns:
        The resolved dbutils-like object.

    Raises:
        ValueError: If force_adapter is invalid.
    """
    cfg = config or BdUtilsConfig()
    selected = force_adapter or cfg.force_adapter
    if selected is None:
        selected = "databricks" if _is_probably_databricks() else "local"

    if selected == "databricks":
        dbutils_obj = databricks_dbutils or resolve_live_dbutils()
        if dbutils_obj is None:
            return LocalDbutils(cfg)
        return dbutils_obj
    if selected == "local":
        return LocalDbutils(cfg)
    raise ValueError("force_adapter must be one of: local, databricks, or None")
