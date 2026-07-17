# -*- coding: utf-8 -*-
"""Banka Metrik Tutarlılık Bekçisi — kurumsal panel (v1.1).

Çalıştırma:  streamlit run app.py
Veri yoksa önce:  python generate_data.py
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from detector.core import dogrulugu_olc, korpusu_tara, tara

KOK = Path(__file__).parent
SURUM = "v1.1"

st.set_page_config(page_title="Banka Metrik Tutarlılık Bekçisi",
                   page_icon="🏦", layout="wide",
                   initial_sidebar_state="collapsed")

# ---------------------------------------------------------------- çeviri
T = {
 "tr": {
   "marka_alt": "Metrik Tutarlılık Bekçisi",
   "nav": ["Bulgular", "Doğruluk ölçümü", "Nasıl çalışır?"],
   "hero_eyebrow": "İŞ ZEKASI VE RAPORLAMA",
   "hero_h1a": "GÜVENİLİR", "hero_h1b": "METRİKLER.",
   "hero_p": ("Rapor tanımlarındaki metrik tutarsızlıklarını toplantıdan önce "
              "yakalar — hangi tanımın doğru olduğuna iş birimleri karar verir."),
   "hero_notu": "Yalnızca SQL tanımlarını okur · Müşteri verisine erişmez",
   "kpi": ["Taranan rapor", "Çıkarılan metrik", "Açık bulgu", "En yüksek önem"],
   "filtreler": "Filtreler", "tip": "Bulgu tipi",
   "tip_drift": "Tanım kayması", "tip_kopya": "Gizli kopya",
   "min_puan": "En düşük önem puanı", "ara": "Kavram ara",
   "ara_ph": "örn. AKTIF_MUSTERI", "sirala": "Sıralama",
   "sirala_sec": ["Önem (yüksek → düşük)", "Kavram adı (A → Z)"],
   "durum": "Kayıt durumu", "durumlar": ["Açık", "İncelemede", "Çözüldü"],
   "tara": "Yeniden tara", "son_tarama": "Son tarama",
   "indir_csv": "Bulguları indir (CSV)", "indir_json": "Bulguları indir (JSON)",
   "bos": "Bu filtrelerle gösterilecek bulgu yok. Filtreleri gevşetmeyi dene.",
   "rozet_drift": "TANIM KAYMASI", "rozet_kopya": "GİZLİ KOPYA",
   "onem": "önem", "fark_uyari": "Bu raporlar bugün çalıştırıldığında sonuçlar "
   "**%{fark}** farklı çıkıyor.",
   "drift_aciklama": ("'{kavram}' kavramı {n_rapor} raporda ({raporlar}) "
                      "{n_tanim} farklı tanımla hesaplanıyor. Fark noktaları "
                      "detayda listelendi; hangi tanımın resmi kabul edileceği "
                      "iş birimlerinin kararıdır."),
   "kopya_aciklama": ("{n_rapor} rapor ({raporlar}) birebir aynı SQL tanımına "
                      "sahip. Tek kaynak bırakılıp diğeri arşivlenebilir; "
                      "kopyalar zamanla sessizce uzaklaşıp yeni tanım "
                      "kaymaları doğurur."),
   "detay": "Detay — {n} rapor etkileniyor",
   "canli": "Canlı sonuçlar (sentetik veri)", "rapor_k": "Rapor",
   "deger_k": "Değer", "farklar_b": "Fark noktaları",
   "yanyana": "Tanımlar yan yana", "daha": "... ve {n} rapor daha",
   "eval_giris": ("Korpusa **bilerek gömülen** tutarsızlıklara karşı ölçüm — "
                  "sistemin notu kendi beyanı değil, cevap anahtarıyla "
                  "sınavıdır."),
   "recall": "Yakalama (recall)", "precision": "İsabet (precision)",
   "kacan": "Kaçan bulgu", "alarm": "Yanlış alarm",
   "tip_k": "Tip", "kavram_k": "Kavram", "sonuc_k": "Sonuç",
   "yakalandi": "✅ yakalandı", "kacti": "❌ kaçtı",
   "alarmlar": "Yanlış alarmlar: ", "anahtar_yok": "answer_key.json bulunamadı.",
   "hakkinda": """
**Ne yapar?** Bankadaki rapor SQL tanımlarını (view'lar) tarar; aynı isimli
metriğin farklı formüllerle hesaplandığı yerleri (*tanım kayması*) ve birebir
kopya raporları (*gizli kopya*) bulur. Böylece "yönetim toplantısında iki
rapor farklı aktif müşteri sayısı gösteriyor" sorunu, toplantıdan **önce**
yakalanır.

**Nasıl çalışır?**
1. `views/` klasöründeki her SQL dosyası **sqlglot** ile sözdizimi ağacına
   (AST) çevrilir.
2. `SELECT ... AS METRIK_ADI` ifadeleri çıkarılır ve biçimden bağımsız
   normalize edilir.
3. Aynı isimli metriklerin formülleri karşılaştırılır; fark varsa bulgu
   açılır ve sentetik veri üzerinde çalıştırılıp **gerçek sonuç farkı**
   gösterilir.
4. Önem puanı; etkilenen rapor sayısı ve sonuç farkının büyüklüğüyle
   hesaplanır.

**Güvenlik:** Sistem yalnızca SQL *metnini* okur; üretimde müşteri verisine
erişim gerektirmez. Bu demodaki tüm sayılar sentetik veridendir.

**Yol haritası:** Oracle kataloğundan (ALL_VIEWS) otomatik korpus çekme ·
JOIN/CTE içeren karmaşık raporlar · benzer (birebir olmayan) isimler için
gömme (embedding) tabanlı eşleştirme · bulguların e-posta özeti.
""",
   "altbilgi": ("Banka Metrik Tutarlılık Bekçisi {surum} · İş Zekası ve "
                "Raporlama · Sentetik veri — müşteri verisi içermez"),
 },
 "en": {
   "marka_alt": "Metric Consistency Guard",
   "nav": ["Findings", "Accuracy", "How it works"],
   "hero_eyebrow": "BUSINESS INTELLIGENCE & REPORTING",
   "hero_h1a": "TRUSTED", "hero_h1b": "METRICS.",
   "hero_p": ("Catches metric inconsistencies across report definitions "
              "before the meeting — business units decide which definition "
              "is official."),
   "hero_notu": "Reads SQL definitions only · Never touches customer data",
   "kpi": ["Reports scanned", "Metrics extracted", "Open findings",
           "Highest severity"],
   "filtreler": "Filters", "tip": "Finding type",
   "tip_drift": "Definition drift", "tip_kopya": "Hidden copy",
   "min_puan": "Minimum severity score", "ara": "Search concept",
   "ara_ph": "e.g. AKTIF_MUSTERI", "sirala": "Sort by",
   "sirala_sec": ["Severity (high → low)", "Concept name (A → Z)"],
   "durum": "Record status", "durumlar": ["Open", "In review", "Resolved"],
   "tara": "Rescan", "son_tarama": "Last scan",
   "indir_csv": "Download findings (CSV)",
   "indir_json": "Download findings (JSON)",
   "bos": "No findings match these filters. Try loosening them.",
   "rozet_drift": "DEFINITION DRIFT", "rozet_kopya": "HIDDEN COPY",
   "onem": "severity", "fark_uyari": "Run today, these reports return "
   "results that differ by **{fark}%**.",
   "drift_aciklama": ("The concept '{kavram}' is calculated with {n_tanim} "
                      "different definitions across {n_rapor} reports "
                      "({raporlar}). Differences are listed in the details; "
                      "which definition becomes official is a business "
                      "decision."),
   "kopya_aciklama": ("{n_rapor} reports ({raporlar}) share the exact same "
                      "SQL definition. Keep a single source and archive the "
                      "rest; copies silently diverge over time and create "
                      "new drift."),
   "detay": "Details — {n} reports affected",
   "canli": "Live results (synthetic data)", "rapor_k": "Report",
   "deger_k": "Value", "farklar_b": "Points of difference",
   "yanyana": "Definitions side by side", "daha": "... and {n} more reports",
   "eval_giris": ("Measured against inconsistencies **deliberately embedded** "
                  "in the corpus — the score is an exam against an answer "
                  "key, not a self-report."),
   "recall": "Recall", "precision": "Precision",
   "kacan": "Missed findings", "alarm": "False alarms",
   "tip_k": "Type", "kavram_k": "Concept", "sonuc_k": "Result",
   "yakalandi": "✅ caught", "kacti": "❌ missed",
   "alarmlar": "False alarms: ", "anahtar_yok": "answer_key.json not found.",
   "hakkinda": """
**What it does.** Scans the bank's report SQL definitions (views) and finds
places where the same metric is calculated with different formulas
(*definition drift*) plus reports that are exact duplicates (*hidden
copies*). The classic "two reports show different active-customer counts in
the management meeting" problem is caught **before** the meeting.

**How it works.**
1. Every SQL file under `views/` is parsed into a syntax tree (AST) with
   **sqlglot**.
2. `SELECT ... AS METRIC_NAME` expressions are extracted and normalized.
3. Formulas sharing the same name are compared; differences open a finding,
   which is executed against synthetic data to show the **real result gap**.
4. The severity score combines the number of affected reports and the size
   of the result gap.

**Security.** The system only reads SQL *text*; production use requires no
access to customer data. All numbers in this demo come from synthetic data.

**Roadmap.** Automatic corpus ingestion from the Oracle catalog (ALL_VIEWS)
· complex reports with JOIN/CTE · embedding-based matching for similar (but
not identical) names · e-mail digest of findings.
""",
   "altbilgi": ("Bank Metric Consistency Guard {surum} · Business "
                "Intelligence & Reporting · Synthetic data — no customer "
                "data involved"),
 }}

if "dil" not in st.session_state:
    st.session_state.dil = "tr"
t = T[st.session_state.dil]

# ---------------------------------------------------------------- tema
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Manrope:wght@400;500;600;700&display=swap');

:root {
  --yesil-koyu:#0F3527; --yesil:#164A36; --yesil-acik:#2D6A4F;
  --amber:#E8A317; --amber-koyu:#B57D0C;
  --zemin:#F7FAF7; --kart:#FFFFFF; --cizgi:#E1E8E1;
  --metin:#1B2620; --metin-soluk:#5C6B62;
}
html, body, [class*="css"] { font-family:'Manrope',sans-serif;
  color:var(--metin); }
h1,h2,h3 { font-family:'Sora',sans-serif !important; }
.stApp { background:var(--zemin); }
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display:none; }

/* üst navbar */
.navbar {
  background:var(--yesil-koyu); border-radius:0 0 16px 16px;
  padding:14px 28px; margin:-1rem 0 0;
  display:flex; align-items:center; justify-content:space-between; }
.navbar .logo { display:flex; align-items:center; gap:12px; }
.navbar .isaret {
  width:40px; height:40px; border-radius:9px; background:var(--amber);
  color:var(--yesil-koyu); font-family:'Sora'; font-weight:800;
  font-size:1.35rem; display:flex; align-items:center;
  justify-content:center; }
.navbar .ad { color:#fff; font-family:'Sora'; font-weight:800;
  font-size:1.25rem; letter-spacing:.14em; }
.navbar .altad { color:#A9C7B6; font-size:.74rem; letter-spacing:.03em; }
.navbar .sag { display:flex; align-items:center; gap:10px; }
.navbar .rozet { color:#fff; border:1px solid rgba(255,255,255,.35);
  padding:3px 11px; border-radius:999px; font-size:.75rem; }

/* hero */
.hero { display:flex; gap:28px; align-items:stretch; margin:18px 0 6px; }
.hero-metin {
  flex:1.35; background:var(--yesil);
  background-image:repeating-linear-gradient(45deg,
     rgba(255,255,255,.035) 0 6px, transparent 6px 14px);
  border-radius:16px; padding:34px 38px; color:#fff; }
.hero-metin .eyebrow { color:var(--amber); font-size:.74rem;
  letter-spacing:.22em; font-weight:700; }
.hero-metin h1 { color:#fff; font-size:2.7rem; line-height:1.04;
  margin:.45rem 0 .8rem; letter-spacing:.01em; }
.hero-metin h1 .dis { color:transparent;
  -webkit-text-stroke:1.6px rgba(255,255,255,.85); }
.hero-metin p { color:#CFE2D7; max-width:34rem; font-size:.95rem; }
.hero-metin .not { display:inline-block; margin-top:14px; color:#fff;
  border:1px solid rgba(255,255,255,.3); border-radius:999px;
  padding:5px 14px; font-size:.78rem; }
.hero-gorsel { flex:1; background:#E9F1EB; border-radius:16px;
  display:flex; align-items:flex-end; justify-content:center;
  overflow:hidden; min-height:250px; }
.hero-gorsel svg { width:100%; height:100%; display:block; }
@media (max-width:900px){ .hero{flex-direction:column} }

/* KPI şeridi */
.kpi-serit { background:var(--yesil-koyu); border-radius:14px;
  display:flex; margin:14px 0 4px; overflow:hidden; }
.kpi { flex:1; padding:16px 24px; }
.kpi + .kpi { border-left:1px solid rgba(255,255,255,.14); }
.kpi .etiket { color:#A9C7B6; font-size:.74rem; text-transform:uppercase;
  letter-spacing:.09em; }
.kpi .deger { color:var(--amber); font-family:'Sora'; font-weight:800;
  font-size:2rem; line-height:1.25; }

/* kartlar, rozetler */
.rozet-drift { background:#FCF3DF; color:var(--amber-koyu);
  border:1px solid #F0DCAB; }
.rozet-kopya { background:#E7F2EC; color:var(--yesil-acik);
  border:1px solid #CBE3D6; }
.rozet-drift, .rozet-kopya { padding:3px 12px; border-radius:999px;
  font-size:.73rem; font-weight:700; letter-spacing:.05em; }
.puan-yuksek { color:#B3261E; font-weight:800; }
.puan-orta   { color:var(--amber-koyu); font-weight:800; }
.puan-dusuk  { color:var(--yesil-acik); font-weight:800; }
div[data-testid="stVerticalBlockBorderWrapper"] {
  background:var(--kart); border:1px solid var(--cizgi) !important;
  border-radius:14px; }
.stTabs [data-baseweb="tab-highlight"] { background-color:var(--amber); }
.stTabs [aria-selected="true"] { color:var(--yesil) !important;
  font-weight:700; }
.stButton>button { border-color:var(--yesil) !important; }

.altbilgi { color:var(--metin-soluk); font-size:.78rem; text-align:center;
  border-top:1px solid var(--cizgi); padding-top:14px; margin-top:30px; }
</style>""", unsafe_allow_html=True)

# ---------------------------------------------------------------- illüstrasyon
BANKACI_SVG = """
<svg viewBox="0 0 520 320" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Banka çalışanı illüstrasyonu">
  <circle cx="360" cy="140" r="120" fill="#D7E7DC"/>
  <rect x="40" y="52" width="150" height="96" rx="10" fill="#FFFFFF"
        stroke="#CBDCD1"/>
  <rect x="58" y="86" width="16" height="46" rx="3" fill="#2D6A4F"/>
  <rect x="84" y="72" width="16" height="60" rx="3" fill="#E8A317"/>
  <rect x="110" y="96" width="16" height="36" rx="3" fill="#2D6A4F"/>
  <rect x="136" y="64" width="16" height="68" rx="3" fill="#E8A317"/>
  <polyline points="58,80 92,62 118,88 152,56" fill="none"
            stroke="#164A36" stroke-width="3" stroke-linecap="round"/>
  <!-- kişi -->
  <circle cx="330" cy="118" r="30" fill="#C68B59"/>
  <path d="M300 112 q8 -34 40 -28 q22 4 20 30 q-2 -18 -22 -20 q-26 -2 -38 18Z"
        fill="#2B211A"/>
  <path d="M282 232 q6 -62 48 -66 q42 4 48 66 Z" fill="#164A36"/>
  <path d="M318 170 l12 14 l12 -14 l8 10 l-20 24 l-20 -24 Z" fill="#FFFFFF"/>
  <path d="M328 182 h4 l6 34 l-8 10 l-8 -10 Z" fill="#E8A317"/>
  <!-- masa + laptop -->
  <rect x="210" y="232" width="290" height="14" rx="7" fill="#0F3527"/>
  <path d="M356 196 l58 8 l-8 30 l-58 -8 Z" fill="#33413A"/>
  <path d="M348 226 l66 8 l6 6 l-78 -9 Z" fill="#4A5A52"/>
  <!-- rozetler -->
  <rect x="236" y="120" width="86" height="30" rx="15" fill="#FFFFFF"
        stroke="#CBDCD1"/>
  <circle cx="252" cy="135" r="8" fill="#E8A317"/>
  <text x="266" y="140" font-family="Sora, sans-serif" font-size="13"
        font-weight="700" fill="#164A36">%100</text>
  <rect x="416" y="82" width="76" height="30" rx="15" fill="#164A36"/>
  <text x="430" y="102" font-family="Sora, sans-serif" font-size="13"
        font-weight="700" fill="#E8A317">SQL ✓</text>
</svg>"""

# ---------------------------------------------------------------- veri
@st.cache_data(show_spinner=False)
def taramayi_calistir():
    db = KOK / "bank.db"
    con = sqlite3.connect(db) if db.exists() else None
    bulgular = tara(KOK / "views", con=con)
    metrikler = korpusu_tara(KOK / "views")
    if con:
        con.close()
    return ([{"tip": b.tip, "kavram": b.kavram, "puan": b.puan,
              "deger_farki": b.deger_farki, "degerler": b.degerler,
              "raporlar": sorted({m.rapor for m in b.metrikler}),
              "farklar": b.farklar}
             for b in bulgular],
            len(list((KOK / "views").glob("*.sql"))), len(metrikler),
            datetime.now().strftime("%d.%m.%Y %H:%M"))


def puan_sinifi(p):
    return ("puan-yuksek" if p >= 60
            else "puan-orta" if p >= 40 else "puan-dusuk")


def rapor_sql(ad):
    dosya = KOK / "views" / f"{ad}.sql"
    return (dosya.read_text(encoding="utf-8")
            if dosya.exists() else "-- ?")


def aciklama_uret(b):
    if b["tip"] == "drift":
        return t["drift_aciklama"].format(
            kavram=b["kavram"], n_rapor=len(b["raporlar"]),
            raporlar=", ".join(b["raporlar"]),
            n_tanim=max(2, len(b["farklar"])))
    return t["kopya_aciklama"].format(
        n_rapor=len(b["raporlar"]), raporlar=", ".join(b["raporlar"]))


# bank.db yoksa (örn. ilk deploy) sentetik veriyi otomatik üret
if not (KOK / "bank.db").exists():
    import generate_data
    with st.spinner("Sentetik veri üretiliyor..."):
        generate_data.main()

bulgular, n_rapor, n_metrik, son_tarama = taramayi_calistir()
if "durumlar" not in st.session_state:
    st.session_state.durumlar = {}   # kavram -> 0/1/2 (Açık/İncelemede/Çözüldü)

# ---------------------------------------------------------------- navbar
nav_sol, nav_sag = st.columns([5.2, 1])
with nav_sol:
    st.markdown(f"""
<div class="navbar">
  <div class="logo">
    <div class="isaret">B</div>
    <div>
      <div class="ad">BANKA</div>
      <div class="altad">{t["marka_alt"]}</div>
    </div>
  </div>
  <div class="sag"><span class="rozet">{SURUM}</span></div>
</div>""", unsafe_allow_html=True)
with nav_sag:
    dil = st.selectbox("Dil / Language", ["tr", "en"],
                       index=["tr", "en"].index(st.session_state.dil),
                       format_func=lambda d: "🇹🇷 Türkçe" if d == "tr"
                       else "🇬🇧 English",
                       label_visibility="collapsed")
    if dil != st.session_state.dil:
        st.session_state.dil = dil
        st.rerun()

# ---------------------------------------------------------------- hero
st.markdown(f"""
<div class="hero">
  <div class="hero-metin">
    <div class="eyebrow">{t["hero_eyebrow"]}</div>
    <h1>{t["hero_h1a"]}<br><span class="dis">{t["hero_h1b"]}</span></h1>
    <p>{t["hero_p"]}</p>
    <span class="not">{t["hero_notu"]}</span>
  </div>
  <div class="hero-gorsel">{BANKACI_SVG}</div>
</div>""", unsafe_allow_html=True)

acik_sayisi = sum(1 for b in bulgular
                  if st.session_state.durumlar.get(b["kavram"], 0) != 2)
kpi_degerler = [n_rapor, n_metrik, acik_sayisi,
                max((b["puan"] for b in bulgular), default=0)]
st.markdown('<div class="kpi-serit">' + "".join(
    f'<div class="kpi"><div class="etiket">{e}</div>'
    f'<div class="deger">{v}</div></div>'
    for e, v in zip(t["kpi"], kpi_degerler)) + "</div>",
    unsafe_allow_html=True)

# ---------------------------------------------------------------- üst filtre
with st.expander(f"⚙️ {t['filtreler']}", expanded=False):
    f1, f2, f3 = st.columns([1.4, 1, 1.2])
    tipler = f1.multiselect(
        t["tip"], ["drift", "kopya"], default=["drift", "kopya"],
        format_func=lambda x: t["tip_drift"] if x == "drift"
        else t["tip_kopya"])
    min_puan = f2.slider(t["min_puan"], 0, 100, 0, 5)
    arama = f3.text_input(t["ara"], placeholder=t["ara_ph"])
    f4, f5, f6 = st.columns([1.4, 1, 1.2])
    siralama = f4.selectbox(t["sirala"], [0, 1],
                            format_func=lambda i: t["sirala_sec"][i])
    durum_f = f5.multiselect(t["durum"], [0, 1, 2], default=[0, 1],
                             format_func=lambda i: t["durumlar"][i])
    with f6:
        st.caption(f'{t["son_tarama"]}: {son_tarama}')
        if st.button(f'🔄 {t["tara"]}', use_container_width=True):
            taramayi_calistir.clear()
            st.rerun()

gorunen = [b for b in bulgular
           if b["tip"] in tipler and b["puan"] >= min_puan
           and (not arama or arama.upper() in b["kavram"].upper())
           and st.session_state.durumlar.get(b["kavram"], 0) in durum_f]
if siralama == 1:
    gorunen = sorted(gorunen, key=lambda b: b["kavram"])

sekme_bulgu, sekme_eval, sekme_hakkinda = st.tabs(t["nav"])

# ---------------------------------------------------------------- bulgular
with sekme_bulgu:
    u1, u2, _ = st.columns([1.3, 1.3, 3.4])
    disari = [{**{k: b[k] for k in ("tip", "kavram", "puan", "deger_farki",
                                    "raporlar")},
               "aciklama": aciklama_uret(b)} for b in bulgular]
    u1.download_button(t["indir_csv"],
                       pd.DataFrame(disari).to_csv(index=False)
                       .encode("utf-8-sig"),
                       "bulgular.csv", "text/csv", use_container_width=True)
    u2.download_button(t["indir_json"],
                       json.dumps(disari, ensure_ascii=False, indent=2,
                                  default=str).encode("utf-8"),
                       "bulgular.json", "application/json",
                       use_container_width=True)

    if not gorunen:
        st.info(t["bos"])
    for b in gorunen:
        with st.container(border=True):
            sol, orta, sag = st.columns([4.2, 1.3, 1])
            rozet = (f'<span class="rozet-drift">{t["rozet_drift"]}</span>'
                     if b["tip"] == "drift"
                     else f'<span class="rozet-kopya">{t["rozet_kopya"]}</span>')
            sol.markdown(f'{rozet}&nbsp;&nbsp;**{b["kavram"]}**',
                         unsafe_allow_html=True)
            orta.markdown(
                f'<div style="text-align:right">{t["onem"]} '
                f'<span class="{puan_sinifi(b["puan"])}">{b["puan"]}</span>'
                f'</div>', unsafe_allow_html=True)
            eski = st.session_state.durumlar.get(b["kavram"], 0)
            yeni = sag.selectbox("d", [0, 1, 2], index=eski,
                                 format_func=lambda i: t["durumlar"][i],
                                 key=f'durum_{b["kavram"]}',
                                 label_visibility="collapsed")
            st.session_state.durumlar[b["kavram"]] = yeni

            if b["deger_farki"]:
                st.warning(t["fark_uyari"].format(
                    fark=f'{b["deger_farki"]:.1f}'))
            st.write(aciklama_uret(b))

            with st.expander(t["detay"].format(n=len(b["raporlar"]))):
                if b["degerler"]:
                    st.markdown(f'**{t["canli"]}**')
                    st.dataframe(pd.DataFrame(
                        [{t["rapor_k"]: r,
                          t["deger_k"]: f"{v:,.1f}"
                          if isinstance(v, float) else f"{v:,}"}
                         for r, v in b["degerler"].items()]),
                        hide_index=True, use_container_width=True)
                if b["farklar"]:
                    st.markdown(f'**{t["farklar_b"]}**')
                    for f in b["farklar"]:
                        st.code(f, language="sql")
                st.markdown(f'**{t["yanyana"]}**')
                kolonlar = st.columns(min(3, len(b["raporlar"])))
                for k, rapor in zip(kolonlar * 3, b["raporlar"][:3]):
                    with k:
                        st.caption(rapor)
                        st.code(rapor_sql(rapor), language="sql")
                if len(b["raporlar"]) > 3:
                    st.caption(t["daha"].format(n=len(b["raporlar"]) - 3))

# ---------------------------------------------------------------- doğruluk
with sekme_eval:
    st.markdown(t["eval_giris"])
    anahtar = KOK / "answer_key.json"
    if anahtar.exists():
        db = KOK / "bank.db"
        con = sqlite3.connect(db) if db.exists() else None
        sonuc = dogrulugu_olc(tara(KOK / "views", con=con), anahtar)
        if con:
            con.close()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t["recall"], f"%{sonuc['recall'] * 100:.0f}")
        c2.metric(t["precision"], f"%{sonuc['precision'] * 100:.0f}")
        c3.metric(t["kacan"], len(sonuc["kacan"]))
        c4.metric(t["alarm"], len(sonuc["yanlis_alarm"]))
        st.dataframe(pd.DataFrame(
            [{t["tip_k"]: tt, t["kavram_k"]: k,
              t["sonuc_k"]: t["yakalandi"]
              if (tt, k) in set(map(tuple, sonuc["dogru"]))
              else t["kacti"]}
             for tt, k in sonuc["beklenen"]]),
            hide_index=True, use_container_width=True)
        if sonuc["yanlis_alarm"]:
            st.error(t["alarmlar"] + ", ".join(
                f"{tt}:{k}" for tt, k in sonuc["yanlis_alarm"]))
    else:
        st.info(t["anahtar_yok"])

# ---------------------------------------------------------------- hakkında
with sekme_hakkinda:
    st.markdown(t["hakkinda"])

st.markdown(f'<div class="altbilgi">'
            f'{t["altbilgi"].format(surum=SURUM)}</div>',
            unsafe_allow_html=True)
