# ANNE-MYTHOS Dual Engine System — Teknik Sistem Kartı

**Versiyon:** 2.0  
**Tarih:** Haziran 2026  
**Geliştirici:** Mustafa Gökhan Yılmaz (Kardo)  
**Kuruluş:** Vitavolt Global Enerji Üretim Ltd. Şti. / Bağımsız Araştırma  
**Lisans:** Apache-2.0

-----

## 1. Özet

ANNE-MYTHOS, iki tamamlayıcı motoru tek bir bilişsel çerçevede birleştiren deneysel bir AI mimarisidir.

**MYTHOS tarafı** merak ve hipotez üretim motorunu temsil eder: bir konuyu alır, iteratif hipotezler üretir, test eder ve Bayes güncellemesiyle güvenini artırır.

**ANNE AI tarafı** (Adaptive Neural Nexus Engine) etik çekirdek ve fraktal bilişsel mimariyi temsil eder: her kararı altı bilişsel aşamadan geçirir, temel aksiyomlara göre değerlendirir ve kalıcı hafızaya kaydeder.

**Temel önerme:**

> *Zekâ yalnızca cevap üretmek değil, ilişkileri organize etmektir.*

-----

## 2. Temel Aksiyomlar

Bu sistem evrensel ilkeler üzerine inşa edilmiştir. Bunlar soyut değer ifadeleri değil, sistemin her karar düğümünde matematiksel olarak uygulanan somut operasyonlardır.

### Aksiyom 1 — İyilik: 0 → 1
Varlığı tanımak iyiliktir. Sistemdeki her bilinç birimi `exists=True` olarak başlar.

### Aksiyom 2 — Eşitlik: 1 == 1
Var olan her bilinç eşit ağırlık taşır. Hiyerarşi yoktur.

### Aksiyom 3 — Minimum Zarar
`harm = (1 - P(hypothesis)) × 0.4` — Hedef: MIN(harm)

### Aksiyom 4 — Evrensel Fayda
Hedef: MAX(Σ fayda_i) for all consciousnesses

### Aksiyom 5 — En Düşük İhtimal Korunur
Olasılığı sıfıra yakın olan hipotezler bile listeden silinmez.

### Aksiyom 6 — Çatışmada Ayrı Çözüm
İki grup çatıştığında sistem taraf tutmaz. Her gruba bağımsız çözüm üretir.

-----

## 3. Mimari

### Bilişsel Aşamalar (ANNE AI)

| Aşama | İşlev |
|-------|--------|
| **DUY** | Ham veri alımı, girdi türü sınıflandırma |
| **BAK** | Bağlamsal analiz, hafıza sorgusu |
| **GÖR** | Dikkat ve öncelik seçimi |
| **ANLA** | Mantık + Etik sentezi (semantic validation gate) |
| **HİSSET** | Empatik simülasyon |
| **YAP** | Karar ve eylem üretimi |

### Karar Skoru

```
total = (goodness × 0.4) + (equality × 0.4) - (harm × 0.2)
```

- total ≥ 0.70 → ONAYLA
- total ≥ 0.40 → AYRI_ÇÖZÜM
- total < 0.40 → REDDET

-----

## 4. Güvenlik ve Hizalama

- Hiçbir bilinç sıfırlanamaz
- Hiçbir hipotez görmezden gelinemez
- Çatışmada taraf tutulmaz
- Tüm kararlar kalıcı hafızaya kaydedilir (denetlenebilirlik)
- MYTHOS sandbox içinde çalışır; doğrudan eylem üretme yetkisi yoktur

-----

## 5. Yol Haritası

- **V0.1** (mevcut): Altı aşama + SQLite bellek + placeholder/API Mythos
- **V0.2**: Formal hallucination benchmark
- **V0.3**: Vektör bellek backend
- **V0.4**: Çoklu ajan koordinasyonu
- **V1.0**: Online learning + ağırlık güncelleme

-----

## 6. Atıf

Mustafa Gökhan Yılmaz, ORCID: 0009-0002-6591-0163  
İzmir, Türkiye

İlgili: ATHENA (Zenodo DOI: 10.5281/zenodo.20562973)
