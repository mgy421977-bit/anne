"""Minimal, dependency-free DXF writer for engineering drawing generation.

The abstraction intentionally targets ASCII DXF first. DWG-specific integration can
be added later without coupling the cognitive layer to AutoCAD internals.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class DxfEntity:
    kind: str
    values: tuple[tuple[int, str | float | int], ...]


@dataclass
class DxfDrawing:
    entities: list[DxfEntity] = field(default_factory=list)

    def add_line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.entities.append(
            DxfEntity("LINE", ((0, "LINE"), (8, "0"), (10, x1), (20, y1), (11, x2), (21, y2)))
        )

    def add_text(self, text: str, x: float, y: float, height: float = 2.5) -> None:
        self.entities.append(
            DxfEntity("TEXT", ((0, "TEXT"), (8, "0"), (10, x), (20, y), (40, height), (1, text)))
        )

    def to_ascii(self) -> str:
        lines = ["0", "SECTION", "2", "HEADER", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
        for entity in self.entities:
            for code, value in entity.values:
                lines.extend((str(code), str(value)))
        lines.extend(("0", "ENDSEC", "0", "EOF"))
        return "\n".join(lines) + "\n"

    def write(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_ascii(), encoding="utf-8")
        return target
