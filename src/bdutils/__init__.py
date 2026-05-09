from bdutils.config import BdUtilsConfig
from bdutils.core import get_dbutils

"""bdutils: A library for local Databricks-like dbutils.
"""

# Default singleton, mirroring Databricks notebook ergonomics.
dbutils = get_dbutils()


def __getattr__(name: str):
    # Allow direct module usage: import bdutils; bdutils.fs.ls(...)
    if hasattr(dbutils, name):
        return getattr(dbutils, name)
    raise AttributeError(name)


def __dir__():
    return sorted(set(globals().keys()) | set(dir(dbutils)))


__all__ = ["BdUtilsConfig", "get_dbutils", "dbutils"]
