from dataclasses import dataclass


@dataclass(frozen=True)
class FileInfo:
    path: str
    name: str
    size: int
    modificationTime: int


@dataclass(frozen=True)
class SecretMetadata:
    key: str


@dataclass(frozen=True)
class SecretScope:
    name: str


@dataclass(frozen=True)
class MountInfo:
    mountPoint: str
    source: str
    encryptionType: str
