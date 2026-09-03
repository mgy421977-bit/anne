from __future__ import annotations

from pathlib import Path

import pytest

from anne.tools.local_files import LocalFilesTool


def test_local_files_tool_blocks_path_escape(tmp_path: Path) -> None:
    tool = LocalFilesTool(tmp_path)
    with pytest.raises(ValueError):
        tool.read("../secret.txt")


def test_local_files_tool_reads_workspace_file(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("hello ANNE", encoding="utf-8")
    tool = LocalFilesTool(tmp_path)
    assert tool.read("sample.txt") == "hello ANNE"
