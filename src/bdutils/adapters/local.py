import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from bdutils.config import BdUtilsConfig
from bdutils.exceptions import (
    NotebookExit,
    SecretNotDefinedError,
    WidgetNotDefinedError,
)
from bdutils.types import FileInfo, MountInfo, SecretMetadata, SecretScope


class _HelpMixin:
    """Mixin to provide a help command.

    Attributes:
        _COMMANDS (Dict[str, str]): A mapping of command names to their descriptions.
    """

    _COMMANDS: Dict[str, str] = {}

    def help(self, command: Optional[str] = None) -> str:
        """Provide help for commands.

        Args:
            command (Optional[str]): Specific command to get help for.

        Returns:
            str: Help string for the command(s).

        Raises:
            ValueError: If an unknown command is provided.
        """
        if command:
            if command not in self._COMMANDS:
                raise ValueError(f"Unknown command: {command}")
            return f"{command}: {self._COMMANDS[command]}"
        return "\n".join(f"{k}: {v}" for k, v in self._COMMANDS.items())


class LocalWidgets(_HelpMixin):
    """Local implementation of dbutils.widgets."""

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
        """Create a text input widget.

        Args:
            name (str): Widget name.
            defaultValue (str): Default value.
            label (str): Optional label.
        """
        del label
        self._values[name] = defaultValue

    def dropdown(self, name: str, defaultValue: str, choices: List[str], label: str = "") -> None:
        """Create a dropdown input widget.

        Args:
            name (str): Widget name.
            defaultValue (str): Default value.
            choices (List[str]): List of valid choices.
            label (str): Optional label.

        Raises:
            ValueError: If defaultValue is not in choices.
        """
        del label
        if defaultValue not in choices:
            raise ValueError("defaultValue must be one of choices")
        self._values[name] = defaultValue

    def combobox(self, name: str, defaultValue: str, choices: List[str], label: str = "") -> None:
        """Create a combobox input widget.

        Args:
            name (str): Widget name.
            defaultValue (str): Default value.
            choices (List[str]): List of choices.
            label (str): Optional label.
        """
        del label, choices
        self._values[name] = defaultValue

    def multiselect(self, name: str, defaultValue: str, choices: List[str], label: str = "") -> None:
        """Create a multiselect input widget.

        Args:
            name (str): Widget name.
            defaultValue (str): Default value (comma separated string).
            choices (List[str]): List of valid choices.
            label (str): Optional label.

        Raises:
            ValueError: If any chosen value is invalid.
        """
        del label
        chosen = [v.strip() for v in defaultValue.split(",") if v.strip()]
        invalid = [v for v in chosen if v not in choices]
        if invalid:
            raise ValueError(f"invalid choices for multiselect: {invalid}")
        self._values[name] = defaultValue

    def get(self, name: str) -> str:
        """Retrieve the current value of a widget.

        Args:
            name (str): Widget name.

        Returns:
            str: The widget value.

        Raises:
            WidgetNotDefinedError: If the widget is not defined and no env var exists.
        """
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
        """Retrieve all widget names and values.

        Returns:
            Dict[str, str]: Map of widget names to values.
        """
        result = dict(self._values)
        prefix = self._config.widget_env_prefix
        for key, value in os.environ.items():
            if key.startswith(prefix):
                widget_name = key[len(prefix) :].lower()
                result.setdefault(widget_name, value)
        return result

    def getArgument(self, name: str, optional: str = "") -> str:
        """Retrieve the current value of a widget, or a default value if not defined.

        Args:
            name (str): Widget name.
            optional (str): Default value to return if widget is not defined.

        Returns:
            str: Widget value or optional value.
        """
        try:
            return self.get(name)
        except WidgetNotDefinedError:
            return optional

    def remove(self, name: str) -> None:
        """Remove a widget.

        Args:
            name (str): Widget name.
        """
        self._values.pop(name, None)

    def removeAll(self) -> None:
        """Remove all widgets."""
        self._values.clear()


class LocalSecrets(_HelpMixin):
    """Local implementation of dbutils.secrets."""

    _COMMANDS = {
        "get": "Gets the string representation of a secret value with scope and key.",
        "getBytes": ("Gets the bytes representation of a secret value with scope and key."),
        "list": "Lists secret metadata for secrets within a scope.",
        "listScopes": "Lists secret scopes.",
    }

    def __init__(self, config: BdUtilsConfig):
        self._config = config

    def get(self, scope: str, key: str) -> str:
        """Get the string value of a secret.

        Args:
            scope (str): Secret scope.
            key (str): Secret key.

        Returns:
            str: Secret value.

        Raises:
            SecretNotDefinedError: If the secret is not defined as an env var.
        """
        env_key = self._config.secret_env_key(scope, key)
        value = os.environ.get(env_key)
        if value is None:
            raise SecretNotDefinedError(f"Secret '{scope}/{key}' is not defined. Expected env var '{env_key}'.")
        return value

    def getBytes(self, scope: str, key: str) -> bytes:
        """Get the byte value of a secret.

        Args:
            scope (str): Secret scope.
            key (str): Secret key.

        Returns:
            bytes: Secret value as bytes.
        """
        return self.get(scope, key).encode("utf-8")

    def list(self, scope: str) -> List[SecretMetadata]:
        """List secret metadata in a scope.

        Args:
            scope (str): Secret scope.

        Returns:
            List[SecretMetadata]: List of secret metadata.
        """
        prefix = f"{self._config.secret_env_prefix}{scope}__"
        out: List[SecretMetadata] = []
        for env_key in os.environ:
            if env_key.startswith(prefix):
                out.append(SecretMetadata(key=env_key[len(prefix) :]))
        return out

    def listScopes(self) -> List[SecretScope]:
        """List available secret scopes.

        Returns:
            List[SecretScope]: List of secret scopes.
        """
        prefix = self._config.secret_env_prefix
        scopes = set()
        for env_key in os.environ:
            if env_key.startswith(prefix):
                rest = env_key[len(prefix) :]
                if "__" in rest:
                    scopes.add(rest.split("__", 1)[0])
        return [SecretScope(name=s) for s in sorted(scopes)]


class LocalFs(_HelpMixin):
    """Local implementation of dbutils.fs."""

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
        """Resolve a DBFS or file path to a local Path.

        Args:
            path (str): The path to resolve.

        Returns:
            Path: Resolved local Path object.

        Raises:
            ValueError: If a dbfs path escapes the dbfs_root.
        """
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
        """List contents of a directory.

        Args:
            dir (str): Directory path.

        Returns:
            List[FileInfo]: List of file information.
        """
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

    def cp(
        self,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        recurse: bool = False,
        **kwargs,
    ) -> bool:
        """Copy a file or directory.

        Args:
            from_ (Optional[str]): Source path.
            to (Optional[str]): Destination path.
            recurse (bool): Whether to copy recursively.
            **kwargs: Support for 'from' keyword.

        Returns:
            bool: True if successful.

        Raises:
            TypeError: If source or destination is missing.
            ValueError: If source is a directory but recurse is False.
        """
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

    def mv(
        self,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        recurse: bool = False,
        **kwargs,
    ) -> bool:
        """Move a file or directory.

        Args:
            from_ (Optional[str]): Source path.
            to (Optional[str]): Destination path.
            recurse (bool): Ignored.
            **kwargs: Support for 'from' keyword.

        Returns:
            bool: True if successful.

        Raises:
            TypeError: If source or destination is missing.
        """
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
        """Remove a file or directory.

        Args:
            dir (str): Path to remove.
            recurse (bool): Whether to remove recursively.

        Returns:
            bool: True if successful.
        """
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
        """Create directories recursively.

        Args:
            dir (str): Directory path.

        Returns:
            bool: True if successful.
        """
        self._resolve(dir).mkdir(parents=True, exist_ok=True)
        return True

    def head(self, file: str, max_bytes: int = 65536) -> str:
        """Read the beginning of a file.

        Args:
            file (str): File path.
            max_bytes (int): Maximum bytes to read.

        Returns:
            str: Content of the file.
        """
        p = self._resolve(file)
        with p.open("r", encoding="utf-8") as f:
            return f.read(max_bytes)

    def put(self, file: str, contents: str, overwrite: bool = False) -> bool:
        """Write a string to a file.

        Args:
            file (str): File path.
            contents (str): Content to write.
            overwrite (bool): Whether to overwrite if file exists.

        Returns:
            bool: True if successful.

        Raises:
            FileExistsError: If file exists and overwrite is False.
        """
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
        """Mount a source to a DBFS mount point.

        Args:
            source (str): Source path.
            mountPoint (str): DBFS mount point.
            encryptionType (str): Encryption type.
            owner (Optional[str]): Owner.
            extraConfigs (Optional[Dict[str, str]]): Extra configurations.

        Returns:
            bool: True if successful.

        Raises:
            ValueError: If mount point already exists.
        """
        del owner, extraConfigs
        if mountPoint in self._mounts:
            raise ValueError("Mount point already exists")
        self._mounts[mountPoint] = MountInfo(mountPoint=mountPoint, source=source, encryptionType=encryptionType)
        return True

    def updateMount(
        self,
        source: str,
        mountPoint: str,
        encryptionType: str = "",
        owner: Optional[str] = None,
        extraConfigs: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Update an existing mount point.

        Args:
            source (str): Source path.
            mountPoint (str): DBFS mount point.
            encryptionType (str): Encryption type.
            owner (Optional[str]): Owner.
            extraConfigs (Optional[Dict[str, str]]): Extra configurations.

        Returns:
            bool: True if successful.

        Raises:
            ValueError: If mount point does not exist.
        """
        del owner, extraConfigs
        if mountPoint not in self._mounts:
            raise ValueError("Mount point does not exist")
        self._mounts[mountPoint] = MountInfo(mountPoint=mountPoint, source=source, encryptionType=encryptionType)
        return True

    def mounts(self) -> List[MountInfo]:
        """List current mounts.

        Returns:
            List[MountInfo]: List of mount information.
        """
        return list(self._mounts.values())

    def refreshMounts(self) -> bool:
        """Refresh mounts (no-op in local).

        Returns:
            bool: True.
        """
        return True

    def unmount(self, mountPoint: str) -> bool:
        """Unmount a DBFS mount point.

        Args:
            mountPoint (str): DBFS mount point.

        Returns:
            bool: True if successful.

        Raises:
            ValueError: If mount point does not exist.
        """
        if mountPoint not in self._mounts:
            raise ValueError("Mount point does not exist")
        del self._mounts[mountPoint]
        return True


class LocalNotebook(_HelpMixin):
    """Local implementation of dbutils.notebook."""

    _COMMANDS = {
        "exit": "Exits a notebook with a value.",
        "run": "Runs a notebook and returns its exit value.",
    }

    def exit(self, value: str) -> None:
        """Exit the notebook with a value.

        Args:
            value (str): Exit value.

        Raises:
            NotebookExit: Always raised to simulate notebook exit.
        """
        raise NotebookExit(value)

    def run(
        self,
        path: str,
        timeoutSeconds: int,
        arguments: Optional[Dict[str, str]] = None,
    ) -> str:
        """Run a notebook (not implemented in local).

        Args:
            path (str): Notebook path.
            timeoutSeconds (int): Timeout in seconds.
            arguments (Optional[Dict[str, str]]): Notebook arguments.

        Returns:
            str: Exit value.

        Raises:
            NotImplementedError: Always raised as notebook.run is not supported locally.
        """
        del timeoutSeconds, arguments
        raise NotImplementedError(
            f"Local notebook.run is not implemented for path '{path}'. Use your orchestrator in local mode."
        )


class LocalTaskValues(_HelpMixin):
    """Local implementation of dbutils.jobs.taskValues."""

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
        """Get a task value.

        Args:
            taskKey (str): Task key.
            key (str): Value key.
            default (Optional[Any]): Default value if key is not found.
            debugValue (Optional[Any]): Debug value if taskKey is not found.

        Returns:
            Any: The task value.

        Raises:
            ValueError: If task or key is not found and no default/debugValue provided.
        """
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
        """Set a task value.

        Args:
            key (str): Value key.
            value (Any): Value to set.

        Returns:
            bool: True.
        """
        self._store.setdefault(self._current_task_key, {})[key] = value
        return True


class LocalJobs(_HelpMixin):
    """Local implementation of dbutils.jobs."""

    _COMMANDS = {"taskValues": "Utilities for leveraging job task values."}

    def __init__(self):
        self.taskValues = LocalTaskValues()


class _UnsupportedModule(_HelpMixin):
    def __init__(self, module_name: str, commands: Dict[str, str]):
        """Initialize an unsupported module.

        Args:
            module_name (str): Name of the module.
            commands (Dict[str, str]): Commands that are theoretically supported by this module.
        """
        self._module_name = module_name
        self._COMMANDS = commands

    def __getattr__(self, item: str):
        if item in self._COMMANDS:

            def _call(*args, **kwargs):
                del args, kwargs
                raise NotImplementedError(f"dbutils.{self._module_name}.{item} is not supported in local adapter yet.")

            return _call
        raise AttributeError(item)


class LocalDbutils(_HelpMixin):
    """Local implementation of dbutils."""

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
                "getServiceCredentialsProvider": ("Returns service credentials provider."),
                "showCurrentRole": "Shows currently set role.",
                "showRoles": "Shows set of possible assumed roles.",
            },
        )
        self.data = _UnsupportedModule("data", {"summarize": "Summarizes a DataFrame."})
        self.library = _UnsupportedModule("library", {"restartPython": "Restarts Python process."})
        self.meta = _UnsupportedModule("meta", {})
        self.preview = _UnsupportedModule("preview", {})
        self.api = _UnsupportedModule("api", {})
