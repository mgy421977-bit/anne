"""Model-independent Turkish language analysis with on-demand web learning."""
from __future__ import annotations
from dataclasses import dataclass, field
import re
from typing import Any
from anne.language.online_learner import TurkishOnlineLearner

@dataclass
class LanguageAnalysis:
    text: str
    tokens: list[str] = field(default_factory=list)
    known_words: list[dict[str, Any]] = field(default_factory=list)
    unknown_words: list[str] = field(default_factory=list)
    morphology: list[dict[str, Any]] = field(default_factory=list)
    grammar: dict[str, Any] = field(default_factory=dict)
    learned_words: list[str] = field(default_factory=list)

class LanguageEngine:
    """Symbolic Turkish language layer; unknown words are acquired online on demand."""
    VOWELS = "aeıioöuü"
    LEXICON = {
        "ben": {"pos": "zamir", "meaning": "konuşan kişi"}, "sen": {"pos": "zamir", "meaning": "dinleyen kişi"},
        "o": {"pos": "zamir", "meaning": "üçüncü kişi/varlık"}, "biz": {"pos": "zamir", "meaning": "konuşanlar"},
        "siz": {"pos": "zamir", "meaning": "dinleyenler"}, "onlar": {"pos": "zamir", "meaning": "üçüncü kişiler/varlıklar"},
        "ve": {"pos": "bağlaç", "meaning": "öğeleri birbirine bağlar"}, "ama": {"pos": "bağlaç", "meaning": "karşıtlık bildirir"},
        "için": {"pos": "edat", "meaning": "amaç veya neden ilişkisi kurar"}, "mi": {"pos": "soru edatı", "meaning": "evet-hayır sorusu oluşturur"},
    }
    SUFFIXES = (("larımızda","çoğul+1pl_iyelik+bulunma"),("lerimizde","çoğul+1pl_iyelik+bulunma"),("larımız","çoğul+1pl_iyelik"),("lerimiz","çoğul+1pl_iyelik"),("ımızda","1pl_iyelik+bulunma"),("imizde","1pl_iyelik+bulunma"),("umuzda","1pl_iyelik+bulunma"),("ümüzde","1pl_iyelik+bulunma"),("lar","çoğul"),("ler","çoğul"),("ımız","1pl_iyelik"),("imiz","1pl_iyelik"),("umuz","1pl_iyelik"),("ümüz","1pl_iyelik"),("imde","1sg_iyelik+bulunma"),("ımda","1sg_iyelik+bulunma"),("umda","1sg_iyelik+bulunma"),("ümde","1sg_iyelik+bulunma"),("im","1sg_iyelik"),("ım","1sg_iyelik"),("um","1sg_iyelik"),("üm","1sg_iyelik"),("da","bulunma"),("de","bulunma"),("ta","bulunma"),("te","bulunma"),("dan","ayrılma"),("den","ayrılma"),("tan","ayrılma"),("ten","ayrılma"),("a","yönelme"),("e","yönelme"),("ı","belirtme"),("i","belirtme"),("u","belirtme"),("ü","belirtme"),("m","1sg_iyelik"),("n","2sg_iyelik"))

    def __init__(self, *, online: bool = True, timeout: float = 5.0):
        self.online = online
        self.learner = TurkishOnlineLearner(timeout=timeout)
        self.cache = dict(self.LEXICON)
        self.sources = {"human_reference": "https://sozluk.tdk.gov.tr/", "machine_lookup": "https://tr.wiktionary.org/w/api.php"}

    def tokenize(self, text: str) -> list[str]:
        return re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü]+", text.lower())

    def _analyze_word(self, word: str) -> dict[str, Any] | None:
        if word in self.cache:
            return {"word": word, "root": word, "suffixes": [], **self.cache[word]}
        for suffix, label in sorted(self.SUFFIXES, key=lambda x: len(x[0]), reverse=True):
            if word.endswith(suffix) and len(word) > len(suffix) + 1:
                root = word[:-len(suffix)]
                if root in self.cache:
                    return {"word": word, "root": root, "suffixes": [label], **self.cache[root]}
        if self.online:
            item = self.learner.lookup(word)
            if item:
                self.cache[word] = {k: v for k, v in item.items() if k != "word"}
                return item | {"suffixes": []}
        return None

    def analyze(self, text: str, *, internet: bool | None = None) -> LanguageAnalysis:
        old = self.online
        self.online = self.online if internet is None else internet
        try:
            tokens = self.tokenize(text)
            known, unknown, morphology, learned = [], [], [], []
            for token in tokens:
                was_unknown = token not in self.cache
                item = self._analyze_word(token)
                if item:
                    known.append(item)
                    if was_unknown: learned.append(token)
                    if item.get("suffixes"): morphology.append(item)
                else: unknown.append(token)
            return LanguageAnalysis(text=text, tokens=tokens, known_words=known, unknown_words=unknown, morphology=morphology, learned_words=learned, grammar=self._grammar(tokens, known))
        finally:
            self.online = old

    def _grammar(self, tokens, known):
        return {"language":"tr", "word_order":"SOV_candidate", "question_particle":"mi" if any(x in tokens for x in ("mi","mı","mu","mü")) else None, "known_token_ratio":len(known)/len(tokens) if tokens else 0.0}

    def lookup(self, word: str, *, internet: bool | None = None):
        old = self.online
        self.online = self.online if internet is None else internet
        try: return self._analyze_word(word.lower())
        finally: self.online = old

__all__ = ["LanguageEngine", "LanguageAnalysis"]