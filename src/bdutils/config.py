from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class BdUtilsConfig:
    dbfs_root: Path = Path.home() / ".bd-utils" / "dbfs"
    widget_env_prefix: str = "DBX_WIDGET_"
    secret_env_prefix: str = "DBX_SECRET__"
    force_adapter: Optional[str] = None

    def widget_env_key(self, name: str) -> str:
        normalized = name.strip().upper().replace("-", "_")
        return f"{self.widget_env_prefix}{normalized}"

    def secret_env_key(self, scope: str, key: str) -> str:
        return f"{self.secret_env_prefix}{scope}__{key}"
