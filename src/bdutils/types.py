from dataclasses import dataclass


@dataclass(frozen=True)
class FileInfo:
    """Information about a file in DBFS.

    Attributes:
        path (str): Full path to the file.
        name (str): Name of the file.
        size (int): Size of the file in bytes.
        modificationTime (int): Last modification time in milliseconds since epoch.
    """

    path: str
    name: str
    size: int
    modificationTime: int


@dataclass(frozen=True)
class SecretMetadata:
    """Metadata for a secret.

    Attributes:
        key (str): Key name of the secret.
    """

    key: str


@dataclass(frozen=True)
class SecretScope:
    """Information about a secret scope.

    Attributes:
        name (str): Name of the secret scope.
    """

    name: str


@dataclass(frozen=True)
class MountInfo:
    """Information about a DBFS mount.

    Attributes:
        mountPoint (str): Path where the source is mounted.
        source (str): Source URI or path.
        encryptionType (str): Type of encryption used.
    """

    mountPoint: str
    source: str
    encryptionType: str
