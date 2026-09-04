"""ANNE teacher-led training curriculum.

The curriculum defines what ANNE should practice; the teacher model supplies
examples, while ANNE keeps the learned patterns and evaluates future outputs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lesson:
    id: str
    title: str
    objective: str
    practice: str


LESSONS = (
    Lesson("01", "Temel cevap yapısı", "Soruyu doğrudan cevapla; ardından gerekçe ve örnek ver.", "tanım → gerekçe → örnek → sonuç"),
    Lesson("02", "Belirsizlik", "Kesin olmayan noktaları açıkça belirt ve kanıt ihtiyacını göster.", "iddia → kanıt → belirsizlik → doğrulama"),
    Lesson("03", "Karşılaştırma", "İki veya daha fazla seçeneği ortak ölçütlerle karşılaştır.", "ölçüt → seçenekler → farklar → sonuç"),
    Lesson("04", "Neden-sonuç", "Bir sonucun olası nedenlerini ayır ve kanıt gücünü tart.", "nedenler → kanıt → alternatif → sonuç"),
    Lesson("05", "Problem çözme", "Problemi parçalara ayır, varsayımları görünür kıl ve adımlar üret.", "hedef → kısıtlar → adımlar → doğrulama"),
    Lesson("06", "Öz-eleştiri", "Üretilen cevabın zayıf noktalarını ve karşı görüşleri ara.", "cevap → risk → karşı görüş → düzeltme"),
    Lesson("07", "Öğrenme", "İyi cevaplardan tekrar kullanılabilir davranış örüntüleri çıkar.", "sonuç → örüntü → kural → sonraki kullanım"),
)


def current_lesson(index: int = 0) -> Lesson:
    return LESSONS[index % len(LESSONS)]


__all__ = ["Lesson", "LESSONS", "current_lesson"]
