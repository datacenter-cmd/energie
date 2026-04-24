import streamlit as st
import pandas as pd
import os, io
from sidebar_shared import render_sidebar
from auth import require_login, require_admin
from drive import get_all_files, download_by_id
from utils import (norm, fmt_cur, fmt_date, ts_now,
                   parse_inserito, parse_pagato, match_ins_pag,
                   load_storico, add_to_storico, STORICO_FASTWEB)

st.set_page_config(page_title="BIGGBAOO ↔ Fastweb", page_icon="📋", layout="wide")

# ─── AUTH CHECK ──────────────────────────────────
name, username = require_admin()

# ─── CSS ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], .stMarkdown, .stText, button, input, select, textarea {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
.kpi-box {
    background: #ffffff; border-radius: 8px; padding: .9rem 1.1rem;
    border: 1px solid #e0e0e0; box-shadow: 0 1px 3px rgba(0,0,0,.06);
    text-align: center; margin-bottom: .5rem;
}
.kpi-label { font-size:.75rem; color:#1a1a1a; text-transform:uppercase; letter-spacing:.04em; font-weight:800; }
.kpi-value { font-size:1.8rem; font-weight:700; line-height:1.1; margin:.25rem 0; color:#1a1a1a; }
.kpi-sub   { font-size:.72rem; color:#6b6b6b; }
.ok   { color:#2a7a2a; } .err  { color:#b02020; }
.gold { color:#7a5c00; } .pri  { color:#2d2d2d; }
.info-box {
    background:#ffffff; border:1px solid #d8d8d8; border-left:3px solid #2d2d2d;
    border-radius:6px; padding:.75rem 1rem; font-size:.875rem; margin-bottom:.75rem;
}
.warn-box {
    background:#fff8f0; border:1px solid #e8d0b0; border-left:3px solid #b05a00;
    border-radius:6px; padding:.75rem 1rem; font-size:.875rem; margin-bottom:.75rem;
}
.section-title {
    font-size:1rem; font-weight:600; color:#1a1a1a; margin-bottom:.6rem;
    display:flex; align-items:center; gap:.4rem;
    border-bottom:1px solid #e0e0e0; padding-bottom:.4rem;
}
div[data-testid="stSidebarContent"] { background:#ebebeb !important; }
.storico-item {
    background:#ffffff; border:1px solid #e0e0e0; border-radius:6px;
    padding:.5rem .9rem; font-size:.8rem; margin-bottom:.4rem;
}
.login-header { text-align:center; padding:2.5rem 0 1rem; }
.login-header .logo  { font-size:2.5rem; }
.login-header .title { font-size:1.5rem; font-weight:700; margin:.4rem 0; color:#1a1a1a; }
.login-header .sub   { color:#6b6b6b; font-size:.9rem; }
[data-sso-provider="easytlc"] { display:none; }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────
render_sidebar(name)
with st.sidebar:
    st.divider()
    st.markdown("**📂 Carica file Fastweb:**")
    uploaded = st.file_uploader("File Fastweb (.xlsx)", type=["xlsx"], label_visibility="collapsed")
# ─── HEADER ──────────────────────────────────────
st.markdown("# 📋 BIGGBAOO ↔ Fastweb")
st.markdown("Confronto pratiche inserite vs pagamenti ricevuti da Fastweb")
st.divider()


if not uploaded:
    st.info("👈 Carica il file Excel mensile Fastweb dalla barra laterale.")
    st.stop()

# ─── CARICAMENTO ─────────────────────────────────
try:
    xl = pd.ExcelFile(uploaded)
    sheet_ins = next((s for s in xl.sheet_names if s.lower()=="inserito"), None)
    sheet_pag = next((s for s in xl.sheet_names if "pagato nuovo" in s.lower()), None)
    if not sheet_ins: st.error("❌ Foglio 'inserito' non trovato."); st.stop()
    if not sheet_pag: st.error("❌ Foglio 'pagato nuovo format' non trovato."); st.stop()
    df_ins = pd.read_excel(uploaded, sheet_name=sheet_ins)
    df_pag = pd.read_excel(uploaded, sheet_name=sheet_pag)
    pag_map = parse_pagato(df_pag)
    rows    = match_ins_pag(parse_inserito(df_ins), pag_map)
    paid    = [r for r in rows if r["_match"]]
    unpaid  = [r for r in rows if not r["_match"]]
    def safe_float(v):
        try: return float(v) if v is not None else 0.0
        except: return 0.0
    importo_base = sum(safe_float(r["_match"]["importo_base"]) for r in paid)
    importo_tot  = sum(safe_float(r["_match"]["importo_tot"])  for r in paid)
    add_to_storico(STORICO_FASTWEB, {
        "filename": uploaded.name, "ts": ts_now(),
        "totale": len(rows), "pagate": len(paid),
        "importo_tot": importo_tot,
    })
except Exception as ex:
    st.error(f"❌ Errore: {ex}"); st.stop()

# ─── KPI ─────────────────────────────────────────
c1,c2,c3,c4,c5 = st.columns(5)
kpis = [
    ("Pratiche totali", len(rows), "", "caricate"),
    ("✅ Pagate", len(paid), "ok", f"{round(len(paid)/len(rows)*100)}% del totale"),
    ("❌ Non pagate", len(unpaid), "err", f"{round(len(unpaid)/len(rows)*100)}% del totale"),
    ("💶 Compenso base", fmt_cur(importo_base), "gold", "importo base"),
    ("🏆 Totale (base+gara)", fmt_cur(importo_tot), "pri", "importo totale"),
]
for col, (label, val, cls, sub) in zip([c1,c2,c3,c4,c5], kpis):
    with col:
        st.markdown(f'''<div class="kpi-box">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value {cls}">{val}</div>
          <div class="kpi-sub">{sub}</div>
        </div>''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── PANEL NON PAGATE ────────────────────────────
if unpaid:
    with st.expander(f"⚠️ {len(unpaid)} pratiche NON trovate nel pagato", expanded=False):
        cols = st.columns(3)
        for i,r in enumerate(unpaid):
            with cols[i%3]:
                off = r["offerta"].replace("MONO ","").replace("Fastweb Energia ","")
                st.markdown(f"🔴 **{off or 'n.d.'}**  \n`{r['codice_pod'] or r['codice_ordine']}`  \n{r['data']}")

# ─── FILTRI ──────────────────────────────────────
st.markdown("### 🔍 Filtri")
f1,f2,f3,f4 = st.columns([2,1,1,3])
pvs  = ["Tutti"]+sorted(set(r["punto_vendita"] for r in rows if r["punto_vendita"]))
mesi = ["Tutti"]+sorted(set(r["mese"] for r in rows if r["mese"]))
with f1: sel_pv   = st.selectbox("Punto Vendita", pvs)
with f2: sel_mese = st.selectbox("Mese", mesi)
with f3: sel_stato= st.selectbox("Stato", ["Tutti","✅ Pagato","❌ Non pagato"])
with f4: search   = st.text_input("Cerca (POD / FWEN / offerta)")

filtered = rows[:]
if sel_pv   != "Tutti": filtered=[r for r in filtered if r["punto_vendita"]==sel_pv]
if sel_mese != "Tutti": filtered=[r for r in filtered if r["mese"]==sel_mese]
if sel_stato=="✅ Pagato":    filtered=[r for r in filtered if r["_match"]]
if sel_stato=="❌ Non pagato":filtered=[r for r in filtered if not r["_match"]]
if search:
    s=search.upper()
    filtered=[r for r in filtered if s in r["codice_pod"] or s in r["codice_ordine"]
              or s in r["offerta"].upper() or s in r["punto_vendita"].upper()
              or (r["_match"] and s in norm(r["_match"]["cod_pod"]))]

st.markdown(f"**{len(filtered)}** pratiche nella selezione")

# ─── TABELLA ─────────────────────────────────────
MATCH_LABEL={"POD":"🟢 POD","FWEN":"🔵 FWEN","ACC":"🟡 ACC",None:"—"}
table=[{
    "Data": r["data"], "Mese": r["mese"],
    "Punto Vendita": r["punto_vendita"],
    "POD": r["codice_pod"][:16]+"…" if len(r["codice_pod"])>16 else r["codice_pod"],
    "Offerta": r["offerta"].replace("MONO ","").replace("Fastweb Energia ",""),
    "Stato Ordine": r["stato_ordine"],
    "Match": MATCH_LABEL.get(r["_match_type"],"—"),
    "Stato Pag.": "✅ Pagata" if r["_match"] else "❌ Non pagata",
    "Base €": fmt_cur(r["_match"]["importo_base"]) if r["_match"] else "—",
    "Gara €": fmt_cur(r["_match"]["importo_gara"]) if r["_match"] else "—",
    "Totale €": fmt_cur(r["_match"]["importo_tot"]) if r["_match"] else "—",
} for r in filtered]

if table:
    st.dataframe(pd.DataFrame(table), use_container_width=True,
        height=min(60+len(table)*38,550))

    # ─── DETTAGLIO ───────────────────────────────
    st.markdown("### 🔎 Dettaglio pratica")
    opts=[f"{r['data']} · {r['punto_vendita']} · {r['codice_pod'] or r['codice_ordine']}" for r in filtered]
    idx=st.selectbox("Seleziona pratica",range(len(opts)),format_func=lambda i:opts[i])
    r=filtered[idx]
    d1,d2=st.columns(2)
    with d1:
        st.markdown("**📋 Dati pratica inserita**")
        for k,v in [("Data",r["data"]),("Mese",r["mese"]),("Punto Vendita",r["punto_vendita"]),
                    ("Offerta",r["offerta"]),("Stato Ordine",r["stato_ordine"]),
                    ("Segmento",r["segmento"]),("Data Attivazione",r["data_att"])]:
            st.markdown(f"- **{k}:** {v}")
        pod_v=r["codice_pod"]; fwen_v=r["codice_ordine"]; acc_v=r["account"]
        st.code(f"POD:     {pod_v}\nFWEN:    {fwen_v}\nAccount: {acc_v}", language="text")
    with d2:
        if r["_match"]:
            m=r["_match"]
            st.markdown(f"**💰 Dati pagamento** · Match: `{r['_match_type']}`")
            for k,v in [("Compenso Base",fmt_cur(m["importo_base"])),
                        ("Compenso Gara",fmt_cur(m["importo_gara"])),
                        ("Importo Totale",fmt_cur(m["importo_tot"])),
                        ("Offerta",m["offerta"]),("Stato Contratto",m["stato_contr"]),
                        ("Stato Fornitura",m["stato_forn"]),("Competenza",m["competenza"]),
                        ("Data Attivazione",m["data_att"])]:
                st.markdown(f"- **{k}:** {v}")
            cod_pod_v=m["cod_pod"]; cod_contr_v=m["cod_contr"]; cod_cl_v=m["cod_cliente"]
            st.code(f"COD POD:      {cod_pod_v}\nCOD CONTR:   {cod_contr_v}\nCOD CLIENTE: {cod_cl_v}", language="text")
        else:
            st.warning("❌ Pratica non trovata nel file pagato Fastweb.")
            pod_v2=r["codice_pod"] or "(vuoto)"; fwen_v2=r["codice_ordine"] or "(vuoto)"
            st.markdown(f"- **POD cercato:** `{pod_v2}`")
            st.markdown(f"- **FWEN cercato:** `{fwen_v2}`")

    # ─── EXPORT ──────────────────────────────────
    st.divider()
    export=[{
        "Data":r["data"],"Mese":r["mese"],"Punto Vendita":r["punto_vendita"],
        "Codice POD":r["codice_pod"],"Codice Ordine":r["codice_ordine"],"Offerta":r["offerta"],
        "Stato Ordine":r["stato_ordine"],"Stato Pagamento":"Pagato" if r["_match"] else "Non pagato",
        "Motivo Match":r["_match_type"] or "—",
        "Base €":r["_match"]["importo_base"] if r["_match"] else "",
        "Gara €":r["_match"]["importo_gara"] if r["_match"] else "",
        "Totale €":r["_match"]["importo_tot"] if r["_match"] else "",
        "Offerta Pagato":r["_match"]["offerta"] if r["_match"] else "",
        "Stato Contratto":r["_match"]["stato_contr"] if r["_match"] else "",
        "Stato Fornitura":r["_match"]["stato_forn"] if r["_match"] else "",
        "Competenza":r["_match"]["competenza"] if r["_match"] else "",
        "Cod. Contratto":r["_match"]["cod_contr"] if r["_match"] else "",
    } for r in filtered]
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        pd.DataFrame(export).to_excel(w, index=False, sheet_name="Pratiche Fastweb")
    st.download_button("📥 Esporta Excel selezione",
        data=buf.getvalue(),
        file_name=f"fastweb_{uploaded.name}",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
