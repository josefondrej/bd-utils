import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from bdutils.config import BdUtilsConfig
from bdutils.exceptions import NotebookExit, SecretNotDefinedError, WidgetNotDefinedError
from bdutils.types import FileInfo, MountInfo, SecretMetadata, SecretScope


class _HelpMixin:
    _COMMANDS: Dict[str, str] = {}

    def help(self, command: Optional[str] = None) -> str:
        if command:
            if command not in self._COMMANDS:
                raise ValueError(f"Unknown command: {command}")
            return f"{command}: {self._COMMANDS[command]}"
        return "\n".join(f"{k}: {v}" for k, v in self._COMMANDS.items())


class LocalWidgets(_HelpMixin):
    _COMMANDS = {
        "combobox": "Creates a combobox input widget.",
        "dropdown": "Creates a dropdown input widget.",
        "get": "Retrieves current value of an input widget.",
        "getAll": "Retrieves a map of all widget names and values.",
        "getArgument": "Deprecated. Equivalent to get.",
        "multiselect": "Creates a multiselect input widget.",
        "remove": "Removes an input widget.",
        "removeAll": "Removes all input widgets.",
        "text": "Creates a text input widget.",
    }

    def __init__(self, config: BdUtilsConfig):
        self._config = config
        self._values: Dict[str, str] = {}

    def text(self, name: str, defaultValue: str, label: str = "") -> None:
        del label
        self._values[name] = defaultValue

    def dropdown(self, name: str, defaultValue: str, choices: List[str], label: str = "") -> None:
        del label
        if defaultValue not in choices:
            raise ValueError("defaultValue must be one of choices")
        self._values[name] = defaultValue

    def combobox(self, name: str, defaultValue: str, choices: List[str], label: str = "") -> None:
        del label, choices
        self._values[name] = defaultValue

    def multiselect(self, name: str, defaultValue: str, choices: List[str], label: str = "") -> None:
        del label
        chosen = [v.strip() for v in defaultValue.split(",") if v.strip()]
        invalid = [v for v in chosen if v not in choices]
        if invalid:
            raise ValueError(f"invalid choices for multiselect: {invalid}")
        self._values[name] = defaultValue

    def get(self, name: str) -> str:
        if name in self._values:
            return self._values[name]
        env_key = self._config.widget_env_key(name)
        value = os.environ.get(env_key)
        if value is None:
            raise WidgetNotDefinedError(
                f"Widget '{name}' is not defined. Expected env var '{env_key}' for local execution."
            )
        return value

    def getAll(self) -> Dict[str, str]:
        result = dict(self._values)
        prefix = self._config.widget_env_prefix
        for key, value in os.environ.items():
            if key.startswith(prefix):
                widget_name = key[len(prefix) :].lower()
                result.setdefault(widget_name, value)
        return result

    def getArgument(self, name: str, optional: str = "") -> str:
        try:
            return self.get(name)
        except WidgetNotDefinedError:
            return optional

    def remove(self, name: str) -> None:
        self._values.pop(name, None)

    def removeAll(self) -> None:
        self._values.clear()


class LocalSecrets(_HelpMixin):
    _COMMANDS = {
        "get": "Gets the string representation of a secret value with scope and key.",
        "getBytes": "Gets the bytes representation of a secret value with scope and key.",
        "list": "Lists secret metadata for secrets within a scope.",
        "listScopes": "Lists secret scopes.",
    }

    def __init__(self, config: BdUtilsConfig):
        self._config = config

    def get(self, scope: str, key: str) -> str:
        env_key = self._config.secret_env_key(scope, key)
        value = os.environ.get(env_key)
        if value is None:
            raise SecretNotDefinedError(
                f"Secret '{scope}/{key}' is not defined. Expected env var '{env_key}'."
            )
        return value

    def getBytes(self, scope: str, key: str) -> bytes:
        return self.get(scope, key).encode("utf-8")

    def list(self, scope: str) -> List[SecretMetadata]:
        prefix = f"{self._config.secret_env_prefix}{scope}__"
        out: List[SecretMetadata] = []
        for env_key in os.environ:
            if env_key.startswith(prefix):
                out.append(SecretMetadata(key=env_key[len(prefix) :]))
        return out

    def listScopes(self) -> List[SecretScope]:
        prefix = self._config.secret_env_prefix
        scopes = set()
        for env_key in os.environ:
            if env_key.startswith(prefix):
                rest = env_key[len(prefix) :]
                if "__" in rest:
                    scopes.add(rest.split("__", 1)[0])
        return [SecretScope(name=s) for s in sorted(scopes)]


class LocalFs(_HelpMixin):
    _COMMANDS = {
        "cp": "Copies a file or directory, possibly across FileSystems.",
        "head": "Returns up to max_bytes bytes of a file as UTF-8.",
        "ls": "Lists the contents of a directory.",
        "mkdirs": "Creates directories recursively.",
        "mount": "Mounts source into a DBFS mount point.",
        "mounts": "Displays mounted DBFS entries.",
        "mv": "Moves a file or directory.",
        "put": "Writes UTF-8 string to a file.",
        "refreshMounts": "Refreshes mount cache.",
        "rm": "Removes a file or directory.",
        "unmount": "Deletes a DBFS mount point.",
        "updateMount": "Updates an existing mount point.",
    }

    def __init__(self, config: BdUtilsConfig):
        self._config = config
        self._config.dbfs_root.mkdir(parents=True, exist_ok=True)
        self._mounts: Dict[str, MountInfo] = {}

    def _resolve(self, path: str) -> Path:
        if path.startswith("dbfs:/"):
            suffix = path[len("dbfs:/") :].lstrip("/")
            target = (self._config.dbfs_root / suffix).resolve()
            dbfs_root = self._config.dbfs_root.resolve()
            if not str(target).startswith(str(dbfs_root)):
                raise ValueError("dbfs path escapes configured dbfs_root.")
            return target
        if path.startswith("file:/"):
            return Path(path[len("file:/") :]).resolve()
        return Path(path).expanduser().resolve()

    def ls(self, dir: str) -> List[FileInfo]:
        p = self._resolve(dir)
        items = list(p.iterdir()) if p.is_dir() else [p]
        out: List[FileInfo] = []
        for item in items:
            stat = item.stat()
            out.append(
                FileInfo(
                    path=str(item),
                    name=item.name,
                    size=0 if item.is_dir() else stat.st_size,
                    modificationTime=int(stat.st_mtime * 1000),
                )
            )
        return out

    def cp(self, from_: Optional[str] = None, to: Optional[str] = None, recurse: bool = False, **kwargs) -> bool:
        if from_ is None and "from" in kwargs:
            from_ = kwargs["from"]
        if to is None and "to" in kwargs:
            to = kwargs["to"]
        if from_ is None or to is None:
            raise TypeError("cp requires source and destination paths")
        src = self._resolve(from_)
        dst = self._resolve(to)
        if src.is_dir():
            if not recurse:
                raise ValueError("Source is a directory; set recurse=True.")
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        return True

    def mv(self, from_: Optional[str] = None, to: Optional[str] = None, recurse: bool = False, **kwargs) -> bool:
        if from_ is None and "from" in kwargs:
            from_ = kwargs["from"]
        if to is None and "to" in kwargs:
            to = kwargs["to"]
        if from_ is None or to is None:
            raise TypeError("mv requires source and destination paths")
        del recurse
        src = self._resolve(from_)
        dst = self._resolve(to)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return True

    def rm(self, dir: str, recurse: bool = False) -> bool:
        p = self._resolve(dir)
        if p.is_dir():
            if recurse:
                shutil.rmtree(p)
            else:
                p.rmdir()
        elif p.exists():
            p.unlink()
        return True

    def mkdirs(self, dir: str) -> bool:
        self._resolve(dir).mkdir(parents=True, exist_ok=True)
        return True

    def head(self, file: str, max_bytes: int = 65536) -> str:
        p = self._resolve(file)
        with p.open("r", encoding="utf-8") as f:
            return f.read(max_bytes)

    def put(self, file: str, contents: str, overwrite: bool = False) -> bool:
        p = self._resolve(file)
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {p}")
        with p.open("w", encoding="utf-8") as f:
            f.write(contents)
        return True

    def mount(
        self,
        source: str,
        mountPoint: str,
        encryptionType: str = "",
        owner: Optional[str] = None,
        extraConfigs: Optional[Dict[str, str]] = None,
    ) -> bool:
        del owner, extraConfigs
        if mountPoint in self._mounts:
            raise ValueError("Mount point already exists")
        self._mounts[mountPoint] = MountInfo(
            mountPoint=mountPoint, source=source, encryptionType=encryptionType
        )
        return True

    def updateMount(
        self,
        source: str,
        mountPoint: str,
        encryptionType: str = "",
        owner: Optional[str] = None,
        extraConfigs: Optional[Dict[str, str]] = None,
    ) -> bool:
        del owner, extraConfigs
        if mountPoint not in self._mounts:
            raise ValueError("Mount point does not exist")
        self._mounts[mountPoint] = MountInfo(
            mountPoint=mountPoint, source=source, encryptionType=encryptionType
        )
        return True

    def mounts(self) -> List[MountInfo]:
        return list(self._mounts.values())

    def refreshMounts(self) -> bool:
        return True

    def unmount(self, mountPoint: str) -> bool:
        if mountPoint not in self._mounts:
            raise ValueError("Mount point does not exist")
        del self._mounts[mountPoint]
        return True


class LocalNotebook(_HelpMixin):
    _COMMANDS = {
        "exit": "Exits a notebook with a value.",
        "run": "Runs a notebook and returns its exit value.",
    }

    def exit(self, value: str) -> None:
        raise NotebookExit(value)

    def run(self, path: str, timeoutSeconds: int, arguments: Optional[Dict[str, str]] = None) -> str:
        del timeoutSeconds, arguments
        raise NotImplementedError(
            f"Local notebook.run is not implemented for path '{path}'. Use your orchestrator in local mode."
        )


class LocalTaskValues(_HelpMixin):
    _COMMANDS = {
        "get": "Gets the task value for a given task key and value key.",
        "set": "Sets or updates a task value.",
    }

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._current_task_key = "local-task"

    def get(
        self,
        taskKey: str,
        key: str,
        default: Optional[Any] = None,
        debugValue: Optional[Any] = None,
    ) -> Any:
        if taskKey not in self._store:
            if debugValue is not None:
                return debugValue
            raise ValueError(f"Task '{taskKey}' not found.")
        if key not in self._store[taskKey]:
            if default is not None:
                return default
            raise ValueError(f"Key '{key}' not found for task '{taskKey}'.")
        return self._store[taskKey][key]

    def set(self, key: str, value: Any) -> bool:
        self._store.setdefault(self._current_task_key, {})[key] = value
        return True


class LocalJobs(_HelpMixin):
    _COMMANDS = {"taskValues": "Utilities for leveraging job task values."}

    def __init__(self):
        self.taskValues = LocalTaskValues()


class _UnsupportedModule(_HelpMixin):
    def __init__(self, module_name: str, commands: Dict[str, str]):
        self._module_name = module_name
        self._COMMANDS = commands

    def __getattr__(self, item: str):
        if item in self._COMMANDS:
            def _call(*args, **kwargs):
                del args, kwargs
                raise NotImplementedError(
                    f"dbutils.{self._module_name}.{item} is not supported in local adapter yet."
                )

            return _call
        raise AttributeError(item)


class LocalDbutils(_HelpMixin):
    _COMMANDS = {
        "credentials": "Utilities for interacting with credentials within notebooks.",
        "data": "Utilities for understanding and interacting with datasets.",
        "fs": "Utilities for accessing the Databricks file system (DBFS).",
        "jobs": "Utilities for leveraging job features.",
        "library": "Deprecated. Utilities for managing session-scoped libraries.",
        "meta": "Utilities to hook into the compiler (experimental).",
        "notebook": "Utilities for managing notebook control flow.",
        "preview": "Utilities in preview.",
        "secrets": "Utilities for leveraging secrets within notebooks.",
        "widgets": "Utilities for parameterizing notebooks.",
        "api": "Utilities for managing application builds.",
    }

    def __init__(self, config: BdUtilsConfig):
        self.widgets = LocalWidgets(config)
        self.secrets = LocalSecrets(config)
        self.fs = LocalFs(config)
        self.notebook = LocalNotebook()
        self.jobs = LocalJobs()
        self.credentials = _UnsupportedModule(
            "credentials",
            {
                "assumeRole": "Sets the role ARN to assume.",
                "getServiceCredentialsProvider": "Returns service credentials provider.",
                "showCurrentRole": "Shows currently set role.",
                "showRoles": "Shows set of possible assumed roles.",
            },
        )
        self.data = _UnsupportedModule("data", {"summarize": "Summarizes a DataFrame."})
        self.library = _UnsupportedModule("library", {"restartPython": "Restarts Python process."})
        self.meta = _UnsupportedModule("meta", {})
        self.preview = _UnsupportedModule("preview", {})
        self.api = _UnsupportedModule("api", {})
