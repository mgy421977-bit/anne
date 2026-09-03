from __future__ import annotations

from pathlib import Path

from desktop.anne_tinker import AnneTinker


def test_text_attachment_reader(tmp_path: Path) -> None:
    path = tmp_path / "athena_notes.md"
    path.write_text("## Hypothesis\nA different interpretation.", encoding="utf-8")

    name, text = AnneTinker._read_attachment(path)

    assert name == "athena_notes.md"
    assert "different interpretation" in text
