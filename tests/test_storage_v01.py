from __future__ import annotations

from pathlib import Path

import pytest

from anne.storage import LocalArtifactStore, MemoryStore


@pytest.mark.parametrize("factory", [MemoryStore])
def test_memory_store_round_trip(factory: type[MemoryStore]) -> None:
    store = factory()
    metadata = store.put("mitos/evidence/a.txt", b"evidence", content_type="text/plain")
    assert store.get("mitos/evidence/a.txt") == b"evidence"
    assert metadata.size_bytes == 8
    assert metadata.sha256
    assert store.list("mitos") == ["mitos/evidence/a.txt"]


def test_local_store_round_trip(tmp_path: Path) -> None:
    store = LocalArtifactStore(tmp_path)
    metadata = store.put("experiments/run-1/result.json", b"{}", content_type="application/json")
    assert metadata.key == "experiments/run-1/result.json"
    assert store.exists(metadata.key)
    assert store.get(metadata.key) == b"{}"
    assert store.list("experiments") == ["experiments/run-1/result.json"]
    store.delete(metadata.key)
    assert not store.exists(metadata.key)


def test_local_store_rejects_path_escape(tmp_path: Path) -> None:
    store = LocalArtifactStore(tmp_path)
    with pytest.raises(ValueError):
        store.put("../outside.txt", b"blocked")


def test_memory_store_is_ephemeral() -> None:
    first = MemoryStore()
    first.put("temp/item", b"x")
    second = MemoryStore()
    assert not second.exists("temp/item")
