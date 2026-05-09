from pathlib import Path

import bdutils


def test_file_scheme_put_head_ls(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)
    target = tmp_path / "x" / "a.txt"
    path = f"file:{target}"

    bdutils.fs.put(path, "hello", overwrite=True)
    assert bdutils.fs.head(path) == "hello"

    entries = bdutils.fs.ls(f"file:{tmp_path / 'x'}")
    names = {e.name for e in entries}
    assert "a.txt" in names


def test_cp_mv_rm(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)
    src = f"file:{tmp_path / 'src.txt'}"
    dst = f"file:{tmp_path / 'dst.txt'}"
    moved = f"file:{tmp_path / 'moved.txt'}"

    bdutils.fs.put(src, "payload", overwrite=True)
    bdutils.fs.cp(src, dst)
    assert bdutils.fs.head(dst) == "payload"

    bdutils.fs.mv(dst, moved)
    assert bdutils.fs.head(moved) == "payload"

    bdutils.fs.rm(moved)
    assert not (tmp_path / "moved.txt").exists()


def test_mount_commands(monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)
    assert bdutils.fs.mount("s3a://bucket", "/mnt/my-mount")
    assert len(bdutils.fs.mounts()) == 1
    assert bdutils.fs.updateMount("s3a://bucket2", "/mnt/my-mount")
    assert bdutils.fs.refreshMounts()
    assert bdutils.fs.unmount("/mnt/my-mount")
