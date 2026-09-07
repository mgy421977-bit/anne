"""ANNE Windows Tinker v0.2: offline runtime + evidence-gated knowledge learning."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from anne.learning.knowledge_memory import KnowledgeMemory
from anne.learning.knowledge_resolver import KnowledgeResolver
from anne_tinker import AnneTinker


class AnneTinkerV02(AnneTinker):
    """Keep v0.1 offline capabilities and add persistent terminology learning."""

    _TERM_RE = re.compile(r"^\s*(.{1,80}?)\s*=\s*(.{1,200})\s*$")
    _ACRONYM_RE = re.compile(r"\b([A-ZÇĞİÖŞÜ]{2,10})\b")

    def __init__(self) -> None:
        super().__init__()
        self.knowledge_resolver = KnowledgeResolver()
        self.knowledge_memory = KnowledgeMemory(self.knowledge_resolver.memory.path)
        self.title("ANNE AI — Windows Tinker v0.2")

    def _learn_user_terminology(self, user_input: str) -> tuple[str, list[str]] | None:
        match = self._TERM_RE.match(user_input.strip())
        if not match:
            return None
        left, right = (part.strip() for part in match.groups())
        if len(left.split()) > 8 or len(right) < 2:
            return None

        # Canonicalize mappings such as ``Güneş Enerjisi Sistemi = GES`` so
        # the searchable key is the acronym the user will ask about later.
        left_acronym = self._ACRONYM_RE.fullmatch(left)
        right_acronym = self._ACRONYM_RE.fullmatch(right)
        if right_acronym and not left_acronym:
            term, meaning = right, left
        else:
            term, meaning = left, right

        record = self.knowledge_memory.save_term(term=term, meaning=meaning, source="user")
        return (
            f"Öğrendim: {left} = {right}",
            [
                "01 OBSERVE | Kullanıcı açık bir kavram eşlemesi verdi.",
                f"02 LEARN | {left} = {right}",
                f"03 NORMALIZE | canonical term={term}; meaning={meaning}",
                "04 MEMORY | Terminoloji kalıcı knowledge memory'ye kaydedildi.",
                f"05 VERIFY | status=LEARNED_CANDIDATE; confidence={record['confidence']:.2f}; source=user.",
                "06 ANSWER | Öğrenilen eşleştirme kabul edildi.",
            ],
        )

    def _answer_from_learned_term(self, question: str) -> tuple[str, list[str]] | None:
        for term in self._ACRONYM_RE.findall(question):
            record = self.knowledge_memory.get_term(term)
            if record and record.get("meaning"):
                meaning = str(record["meaning"])
                return (
                    f"{term}: {meaning}.",
                    [
                        "01 OBSERVE | Soru alındı.",
                        "02 CAPABILITY CHECK | PROMOTED capability yok; terminology memory kontrol ediliyor.",
                        "03 MEMORY | Öğrenilmiş terminoloji eşleşmesi bulundu.",
                        f"04 TERM | {term} = {meaning}",
                        "05 VERIFY | Kullanıcı kaynaklı LEARNED_CANDIDATE kullanıldı.",
                        "06 ROUTE | terminology memory → answer; web/API çağrısı yapılmadı.",
                        "07 ANSWER | Yerel öğrenilmiş bilgi kullanıldı.",
                    ],
                )
        return None

    def _execute_local(self, user_input: str) -> tuple[str, list[str]]:
        learned = self._learn_user_terminology(user_input)
        if learned is not None:
            return learned

        analysis = self.language.analyze(user_input)
        if analysis.intent != "question":
            return super()._execute_local(user_input)

        local_term = self._answer_from_learned_term(user_input)
        if local_term is not None:
            return local_term

        resolution = self.knowledge_resolver.resolve(user_input)
        trace = list(resolution.trace)
        if resolution.answer is not None:
            trace.append(f"11 ANSWER | provider={resolution.provider or 'memory'}; confidence={resolution.confidence:.2f}")
            return resolution.answer, trace

        trace.append("11 ANSWER | Güvenilir dış kaynak cevabı alınamadı; ANNE cevap uydurmadı.")
        return "Bu soruya şu anda güvenilir bir cevap oluşturamadım. Web ve harici danışman yolları başarısız oldu.", trace


if __name__ == "__main__":
    AnneTinkerV02().mainloop()
