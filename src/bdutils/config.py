from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class BdUtilsConfig:
    """Configuration for bdutils.

    Attributes:
        dbfs_root (Path): Root directory for local DBFS emulation.
        widget_env_prefix (str): Prefix for environment variables used as widgets.
        secret_env_prefix (str): Prefix for environment variables used as secrets.
        force_adapter (Optional[str]): Force usage of 'local' or 'databricks' adapter.
    """

    dbfs_root: Path = Path.home() / ".bd-utils" / "dbfs"
    widget_env_prefix: str = "DBX_WIDGET_"
    secret_env_prefix: str = "DBX_SECRET__"
    force_adapter: Optional[str] = None

    def widget_env_key(self, name: str) -> str:
        """Get the environment variable key for a widget.

        Args:
            name (str): Widget name.

        Returns:
            str: Environment variable key.
        """
        normalized = name.strip().upper().replace("-", "_")
        return f"{self.widget_env_prefix}{normalized}"

    def secret_env_key(self, scope: str, key: str) -> str:
        """Get the environment variable key for a secret.

        Args:
            scope (str): Secret scope.
            key (str): Secret key.

        Returns:
            str: Environment variable key.
        """
        return f"{self.secret_env_prefix}{scope}__{key}"
