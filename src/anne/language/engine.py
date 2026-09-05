"""Model-independent Turkish language analysis for ANNE.

This is deliberately symbolic: it does not train or modify model weights.
It provides vocabulary lookup, simple agglutinative morphology and grammar
metadata that the cognitive core can use before/without an LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


@dataclass
class LanguageAnalysis:
    text: str
    tokens: list[str] = field(default_factory=list)
    known_words: list[dict[str, Any]] = field(default_factory=list)
    unknown_words: list[str] = field(default_factory=list)
    morphology: list[dict[str, Any]] = field(default_factory=list)
    grammar: dict[str, Any] = field(default_factory=dict)


class LanguageEngine:
    """Small extensible Turkish lexicon + suffix analyzer.

    The lexicon is intentionally data-driven. More vocabulary and rules can be
    added later without changing the cognitive architecture.
    """

    VOWELS = "aeıioöuü"
    LEXICON: dict[str, dict[str, Any]] = {
        "ben": {"pos": "zamir", "meaning": "konuşan kişi", "en": "I/me"},
        "sen": {"pos": "zamir", "meaning": "dinleyen kişi", "en": "you"},
        "o": {"pos": "zamir", "meaning": "üçüncü kişi/varlık", "en": "he/she/it"},
        "biz": {"pos": "zamir", "meaning": "konuşanlar", "en": "we"},
        "siz": {"pos": "zamir", "meaning": "dinleyenler", "en": "you(pl/formal)"},
        "onlar": {"pos": "zamir", "meaning": "üçüncü kişiler/varlıklar", "en": "they"},
        "ev": {"pos": "isim", "meaning": "insanların yaşadığı yapı", "en": "house/home"},
        "kitap": {"pos": "isim", "meaning": "okumak için kullanılan yazılı eser", "en": "book"},
        "araba": {"pos": "isim", "meaning": "karayolunda kullanılan motorlu taşıt", "en": "car"},
        "insan": {"pos": "isim", "meaning": "insan türünden birey", "en": "person/human"},
        "çocuk": {"pos": "isim", "meaning": "küçük yaştaki insan", "en": "child"},
        "su": {"pos": "isim", "meaning": "H2O; yaşam için temel sıvı", "en": "water"},
        "güneş": {"pos": "isim", "meaning": "Dünya'nın enerji aldığı yıldız", "en": "sun"},
        "enerji": {"pos": "isim", "meaning": "iş yapabilme kapasitesi", "en": "energy"},
        "bilgi": {"pos": "isim", "meaning": "bir konu hakkındaki anlamlı/veri temelli içerik", "en": "knowledge/information"},
        "sistem": {"pos": "isim", "meaning": "bir amaç için birlikte çalışan öğeler bütünü", "en": "system"},
        "yapay": {"pos": "sıfat", "meaning": "doğal olmayan, insan tarafından oluşturulan", "en": "artificial"},
        "zeka": {"pos": "isim", "meaning": "öğrenme ve problem çözme kapasitesi", "en": "intelligence"},
        "akıl": {"pos": "isim", "meaning": "düşünme ve değerlendirme yetisi", "en": "mind/reason"},
        "gitmek": {"pos": "fiil", "meaning": "bir yerden başka yere yönelmek", "en": "to go"},
        "gelmek": {"pos": "fiil", "meaning": "bulunulan yere doğru yönelmek", "en": "to come"},
        "yapmak": {"pos": "fiil", "meaning": "bir işi gerçekleştirmek", "en": "to do/make"},
        "öğrenmek": {"pos": "fiil", "meaning": "bilgi veya beceri edinmek", "en": "to learn"},
        "araştırmak": {"pos": "fiil", "meaning": "bilgi edinmek için sistematik incelemek", "en": "to research"},
        "bilmek": {"pos": "fiil", "meaning": "bir şeyi bilgi olarak kavramış olmak", "en": "to know"},
        "olmak": {"pos": "fiil", "meaning": "bir duruma geçmek veya bulunmak", "en": "to be/become"},
        "iyi": {"pos": "sıfat", "meaning": "olumlu nitelikte", "en": "good"},
        "büyük": {"pos": "sıfat", "meaning": "boyut veya önem bakımından fazla", "en": "big/great"},
        "küçük": {"pos": "sıfat", "meaning": "boyut veya miktar bakımından az", "en": "small"},
        "ve": {"pos": "bağlaç", "meaning": "öğeleri birbirine bağlar", "en": "and"},
        "ama": {"pos": "bağlaç", "meaning": "karşıtlık bildirir", "en": "but"},
        "için": {"pos": "edat", "meaning": "amaç veya neden ilişkisi kurar", "en": "for/because of"},
        "mi": {"pos": "soru edatı", "meaning": "evet-hayır sorusu oluşturur", "en": "question particle"},
    }

    # Longest-first suffixes. These are analyses, not a complete Turkish grammar.
    SUFFIXES = (
        ("ler", "çoğul"), ("lar", "çoğul"),
        ("ımız", "1pl_iyelik"), ("imiz", "1pl_iyelik"), ("umuz", "1pl_iyelik"), ("ümüz", "1pl_iyelik"),
        ("ımızda", "1pl_iyelik+bulunma"), ("imizde", "1pl_iyelik+bulunma"),
        ("umuzda", "1pl_iyelik+bulunma"), ("ümüzda", "1pl_iyelik+bulunma"),
        ("imde", "1sg_iyelik+bulunma"), ("ımda", "1sg_iyelik+bulunma"),
        ("umda", "1sg_iyelik+bulunma"), ("ümde", "1sg_iyelik+bulunma"),
        ("im", "1sg_iyelik"), ("ım", "1sg_iyelik"), ("um", "1sg_iyelik"), ("üm", "1sg_iyelik"),
        ("da", "bulunma"), ("de", "bulunma"), ("ta", "bulunma"), ("te", "bulunma"),
        ("dan", "ayrılma"), ("den", "ayrılma"), ("tan", "ayrılma"), ("ten", "ayrılma"),
        ("a", "yönelme"), ("e", "yönelme"),
        ("ı", "belirtme"), ("i", "belirtme"), ("u", "belirtme"), ("ü", "belirtme"),
        ("m", "1sg_iyelik"), ("n", "2sg_iyelik"),
    )

    def tokenize(self, text: str) -> list[str]:
        return re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü]+", text.lower())

    def _analyze_word(self, word: str) -> dict[str, Any] | None:
        if word in self.LEXICON:
            return {"word": word, "root": word, "suffixes": [], **self.LEXICON[word]}
        for suffix, label in sorted(self.SUFFIXES, key=lambda item: len(item[0]), reverse=True):
            if word.endswith(suffix) and len(word) > len(suffix) + 1:
                root = word[:-len(suffix)]
                if root in self.LEXICON:
                    return {"word": word, "root": root, "suffixes": [label], **self.LEXICON[root]}
        return None

    def analyze(self, text: str) -> LanguageAnalysis:
        tokens = self.tokenize(text)
        known, unknown, morphology = [], [], []
        for token in tokens:
            item = self._analyze_word(token)
            if item:
                known.append(item)
                if item["suffixes"]:
                    morphology.append(item)
            else:
                unknown.append(token)
        grammar = self._grammar(tokens, known)
        return LanguageAnalysis(text=text, tokens=tokens, known_words=known, unknown_words=unknown, morphology=morphology, grammar=grammar)

    def _grammar(self, tokens: list[str], known: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "language": "tr",
            "word_order": "SOV_candidate",
            "question_particle": "mi" if "mi" in tokens or "mı" in tokens or "mu" in tokens or "mü" in tokens else None,
            "known_token_ratio": len(known) / len(tokens) if tokens else 0.0,
        }

    def lookup(self, word: str) -> dict[str, Any] | None:
        return self._analyze_word(word.lower())


__all__ = ["LanguageEngine", "LanguageAnalysis"]
