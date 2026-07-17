# -*- coding: utf-8 -*-
"""Metrik Tutarlılık Bekçisi — çekirdek motor.

Rapor SQL tanımlarını (views/*.sql) sqlglot ile ayrıştırır, aynı isimli
metriklerin farklı formüllerle hesaplandığı yerleri (tanım kayması) ve
birebir kopya raporları (gizli kopya) bulur. Yalnızca SQL METNİNİ okur;
müşteri verisine dokunmaz. bank.db bağlantısı verilirse bulguları canlı
sayılarla zenginleştirir (sentetik veri).
"""
from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import sqlglot
from sqlglot import exp


# ---------------------------------------------------------------- veri tipleri
@dataclass
class Metrik:
    rapor: str          # view dosya adı (uzantısız)
    ad: str             # metrik adı (SELECT alias'ı)
    ifade: str          # normalize edilmiş SQL ifadesi
    ham: str            # orijinal ifade


@dataclass
class Bulgu:
    tip: str                        # "drift" | "kopya"
    kavram: str                     # metrik / kavram adı
    puan: int                       # 0-100 önem
    metrikler: list = field(default_factory=list)
    farklar: list = field(default_factory=list)
    aciklama: str = ""
    deger_farki: float | None = None    # canlı sonuç farkı (%)
    degerler: dict = field(default_factory=dict)  # rapor -> değer


# ---------------------------------------------------------------- yardımcılar
def _normalize(ifade: exp.Expression) -> str:
    """İfadeyi biçimden bağımsız karşılaştırılabilir hale getirir."""
    sql = ifade.sql(dialect="sqlite", normalize=True, comments=False)
    return re.sub(r"\s+", " ", sql).strip().upper()


def _dosya_normalize(sql_metni: str) -> str:
    """Tam dosyayı kopya kıyası için normalize eder (yorumlar atılır)."""
    try:
        agac = sqlglot.parse_one(sql_metni, dialect="sqlite")
        return _normalize(agac)
    except Exception:
        return re.sub(r"\s+", " ", sql_metni).strip().upper()


# ---------------------------------------------------------------- çıkarım
def korpusu_tara(views_dizini: Path) -> list[Metrik]:
    """Tüm view dosyalarından isimlendirilmiş metrikleri çıkarır."""
    metrikler: list[Metrik] = []
    for dosya in sorted(Path(views_dizini).glob("*.sql")):
        metin = dosya.read_text(encoding="utf-8")
        try:
            agac = sqlglot.parse_one(metin, dialect="sqlite")
        except Exception:
            continue
        for secim in agac.find_all(exp.Select):
            for ifade in secim.expressions:
                if isinstance(ifade, exp.Alias):
                    metrikler.append(Metrik(
                        rapor=dosya.stem,
                        ad=ifade.alias.upper(),
                        ifade=_normalize(ifade.this),
                        ham=ifade.this.sql(dialect="sqlite")))
            break  # yalnız en dış SELECT
    return metrikler


# ---------------------------------------------------------------- canlı değer
def _canli_degerler(views_dizini: Path, con: sqlite3.Connection,
                    kavram: str, raporlar: list[str]) -> dict:
    degerler = {}
    for rapor in raporlar:
        dosya = Path(views_dizini) / f"{rapor}.sql"
        if not dosya.exists():
            continue
        try:
            cur = con.execute(dosya.read_text(encoding="utf-8").rstrip("; \n"))
            satir = cur.fetchone()
            kolonlar = [k[0].upper() for k in cur.description]
            if satir and kavram in kolonlar:
                degerler[rapor] = satir[kolonlar.index(kavram)]
        except Exception:
            pass
    return degerler


def _yuzde_fark(degerler: dict) -> float | None:
    sayilar = [v for v in degerler.values() if isinstance(v, (int, float))]
    if len(sayilar) < 2:
        return None
    buyuk, kucuk = max(sayilar), min(sayilar)
    if buyuk == 0:
        return 0.0
    return round(100.0 * (buyuk - kucuk) / buyuk, 1)


# ---------------------------------------------------------------- puanlama
def _drift_puani(n_rapor: int, fark: float | None) -> int:
    puan = 40 + 5 * (n_rapor - 2)
    if fark is not None:
        puan += min(40, int(fark * 0.4))
    return min(100, puan)


# ---------------------------------------------------------------- ana tarama
def tara(views_dizini: Path,
         con: sqlite3.Connection | None = None) -> list[Bulgu]:
    views_dizini = Path(views_dizini)
    metrikler = korpusu_tara(views_dizini)
    bulgular: list[Bulgu] = []

    # --- tanım kayması: aynı isim, farklı formül
    gruplar: dict[str, list[Metrik]] = {}
    for m in metrikler:
        gruplar.setdefault(m.ad, []).append(m)

    for kavram, grup in gruplar.items():
        raporlar = sorted({m.rapor for m in grup})
        ifadeler = sorted({m.ifade for m in grup})
        if len(raporlar) < 2 or len(ifadeler) < 2:
            continue
        degerler, fark = {}, None
        if con is not None:
            degerler = _canli_degerler(views_dizini, con, kavram, raporlar)
            fark = _yuzde_fark(degerler)
        farklar = sorted({m.ham.strip() for m in grup})
        aciklama = (f"'{kavram}' kavramı {len(raporlar)} raporda "
                    f"({', '.join(raporlar)}) {len(ifadeler)} farklı tanımla "
                    f"hesaplanıyor.")
        if fark is not None:
            aciklama += (f" Bu raporlar bugün çalıştırıldığında sonuçlar "
                         f"%{fark:.1f} farklı çıkıyor.")
        aciklama += (" Fark noktaları detayda listelendi; hangi tanımın resmi "
                     "kabul edileceği iş birimlerinin kararıdır.")
        bulgular.append(Bulgu(
            tip="drift", kavram=kavram,
            puan=_drift_puani(len(raporlar), fark),
            metrikler=grup, farklar=farklar, aciklama=aciklama,
            deger_farki=fark, degerler=degerler))

    # --- gizli kopya: birebir aynı tanım, farklı dosya
    imzalar: dict[str, list[str]] = {}
    for dosya in sorted(views_dizini.glob("*.sql")):
        imza = _dosya_normalize(dosya.read_text(encoding="utf-8"))
        imzalar.setdefault(imza, []).append(dosya.stem)
    for imza, raporlar in imzalar.items():
        if len(raporlar) < 2:
            continue
        bulgular.append(Bulgu(
            tip="kopya", kavram=" / ".join(raporlar), puan=35,
            metrikler=[m for m in metrikler if m.rapor in raporlar],
            farklar=[],
            aciklama=(f"{len(raporlar)} rapor ({', '.join(raporlar)}) birebir "
                      "aynı SQL tanımına sahip. Biri diğerinin kopyası; "
                      "tek kaynak bırakılıp diğeri arşivlenebilir. Kopyalar "
                      "zamanla sessizce birbirinden uzaklaşıp yeni tanım "
                      "kaymaları doğurur.")))

    bulgular.sort(key=lambda b: -b.puan)
    return bulgular


# ---------------------------------------------------------------- doğruluk
def dogrulugu_olc(bulgular: list[Bulgu],
                  cevap_anahtari: Path) -> dict:
    """Bulguları bilerek gömülen tutarsızlıklarla kıyaslar."""
    anahtar = json.loads(Path(cevap_anahtari).read_text(encoding="utf-8"))
    beklenen = {(k["tip"], k["kavram"].upper()) for k in anahtar}
    bulunan = {(b.tip, b.kavram.upper()) for b in bulgular}

    dogru = beklenen & bulunan
    kacan = beklenen - bulunan
    yanlis_alarm = bulunan - beklenen

    recall = len(dogru) / len(beklenen) if beklenen else 1.0
    precision = len(dogru) / len(bulunan) if bulunan else 1.0
    return {"beklenen": sorted(beklenen), "dogru": sorted(dogru),
            "kacan": sorted(kacan), "yanlis_alarm": sorted(yanlis_alarm),
            "recall": recall, "precision": precision}
