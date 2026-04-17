import streamlit as st
import pandas as pd
import os, io
from auth import require_login
from utils import (norm, fmt_cur, fmt_date, ts_now,
                   parse_agenti, parse_pagato, parse_inserito, match_agenti,
                   load_storico, add_to_storico, STORICO_AGENTI)

st.set_page_config(page_title="BIGGBAOO ↔ Agenti", page_icon="👥", layout="wide")

# ─── AUTH CHECK ──────────────────────────────────
name, username = require_login()

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
.kpi-label { font-size:.72rem; color:#6b6b6b; text-transform:uppercase; letter-spacing:.07em; font-weight:600; }
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
with st.sidebar:
    st.markdown("### ⚡ Portale Energie")
    st.markdown("**BIGGBAOO**")
    st.markdown(f"👤 {name}")
    st.divider()
    st.markdown("**1️⃣ File gestionale agenti**")
    upl_agenti = st.file_uploader("exportgridData (.xlsx)", type=["xlsx","xls"],
        key="upl_ag", help="File esportato dal gestionale con le pratiche inserite dagli agenti")
    st.markdown("**2️⃣ File pagato Fastweb**")
    upl_pagato = st.file_uploader("File pagato (.xlsx)", type=["xlsx","xls"],
        key="upl_pag", help="File Fastweb con il foglio 'pagato nuovo format'")
    st.divider()
    st.markdown("**🕐 Storico caricamenti**")
    storico = load_storico(STORICO_AGENTI)
    if storico:
        for s in storico[:5]:
            nc = s.get("totale",0)-s.get("complete",0)
            st.markdown(f"📄 **{s['filename_ag']}**  \n🕐 {s['ts']} · ✅{s.get('complete',0)} ❌{nc}")
            st.markdown("---")
    else:
        st.caption("Nessun caricamento precedente")
    st.divider()
    st.caption("👥 BIGGBAOO ↔ Agenti")

# ─── HEADER ──────────────────────────────────────
st.markdown("# 👥 BIGGBAOO ↔ Agenti")
st.markdown("Verifica pratiche agenti · Determina i compensi da liquidare")
st.divider()

if not upl_agenti or not upl_pagato:
    missing = []
    if not upl_agenti: missing.append("📋 File gestionale agenti")
    if not upl_pagato: missing.append("💶 File pagato Fastweb")
    st.info(f"👈 Carica dalla barra laterale:  \n" + "  \n".join(missing))
    st.stop()

# ─── CARICAMENTO ─────────────────────────────────
try:
    # Agenti
    df_ag = pd.read_excel(upl_agenti)
    rows_ag = parse_agenti(df_ag)

    # Pagato Fastweb
    xl_pag = pd.ExcelFile(upl_pagato)
    sheet_pag = next((s for s in xl_pag.sheet_names if "pagato nuovo" in s.lower()), None)
    sheet_ins = next((s for s in xl_pag.sheet_names if s.lower()=="inserito"), None)
    if not sheet_pag:
        st.error("❌ Foglio 'pagato nuovo format' non trovato nel file pagato.")
        st.stop()
    df_pag = pd.read_excel(upl_pagato, sheet_name=sheet_pag)
    pag_map = parse_pagato(df_pag)

    # Inserito (opzionale ma migliora il match)
    rows_ins = []
    if sheet_ins:
        df_ins = pd.read_excel(upl_pagato, sheet_name=sheet_ins)
        rows_ins = parse_inserito(df_ins)

    # Match triplo
    rows_ag = match_agenti(rows_ag, rows_ins, pag_map)

    # Categorie
    completi   = [r for r in rows_ag if r["_match_type"]=="✅ Completo"]
    solo_ins   = [r for r in rows_ag if r["_match_type"]=="⚠️ Solo inserito"]
    solo_pag   = [r for r in rows_ag if r["_match_type"]=="⚠️ Solo pagato"]
    non_trovati= [r for r in rows_ag if r["_match_type"]=="❌ Non trovato"]

    importo_da_pagare = sum(r["_match_pag"]["importo_tot"] for r in completi if r["_match_pag"])

    add_to_storico(STORICO_AGENTI, {
        "filename_ag": upl_agenti.name,
        "filename_pag": upl_pagato.name,
        "ts": ts_now(),
        "totale": len(rows_ag),
        "complete": len(completi),
        "importo_da_pagare": importo_da_pagare,
    })

except Exception as ex:
    st.error(f"❌ Errore: {ex}")
    import traceback; st.code(traceback.format_exc())
    st.stop()

# ─── KPI ─────────────────────────────────────────
c1,c2,c3,c4,c5 = st.columns(5)
kpis = [
    ("Pratiche agenti", len(rows_ag), "", "caricate"),
    ("✅ Completo (ins+pag)", len(completi), "ok", "inserite e pagate"),
    ("⚠️ Solo inserito", len(solo_ins), "gold", "non ancora pagate"),
    ("❌ Non trovato", len(non_trovati), "err", "verificare"),
    ("💶 Da liquidare agenti", fmt_cur(importo_da_pagare), "pri", "pratiche complete"),
]
for col,(label,val,cls,sub) in zip([c1,c2,c3,c4,c5],kpis):
    with col:
        st.markdown(f'''<div class="kpi-box">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value {cls}">{val}</div>
          <div class="kpi-sub">{sub}</div>
        </div>''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── TABS STATO ──────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    f"✅ Complete ({len(completi)})",
    f"⚠️ Solo inserito ({len(solo_ins)})",
    f"⚠️ Solo pagato ({len(solo_pag)})",
    f"❌ Non trovate ({len(non_trovati)})",
])

def build_table_agenti(rows):
    out = []
    for r in rows:
        pag = r["_match_pag"]
        out.append({
            "Data":          r["data"],
            "Target":        r["target"],
            "Punto Vendita": r["punto_vendita"],
            "Operatore":     r["operatore"],
            "Servizio":      r["servizio"].replace("ATTIVAZIONE FASTWEB ",""),
            "Stato":         r["stato"],
            "PDA/DOC":       r["pda_raw"][:18]+"…" if len(r["pda_raw"])>18 else r["pda_raw"],
            "Match":         r["_match_type"],
            "Base €":        fmt_cur(pag["importo_base"]) if pag else "—",
            "Gara €":        fmt_cur(pag["importo_gara"]) if pag else "—",
            "Totale €":      fmt_cur(pag["importo_tot"])  if pag else "—",
            "Offerta":       pag["offerta"] if pag else "—",
            "Stato Fornitura": pag["stato_forn"] if pag else "—",
        })
    return pd.DataFrame(out)

# Filtri comuni
st.markdown("### 🔍 Filtri")
fa1,fa2,fa3 = st.columns([2,2,3])
pvs_ag  = ["Tutti"]+sorted(set(r["punto_vendita"] for r in rows_ag if r["punto_vendita"]))
ops_ag  = ["Tutti"]+sorted(set(r["operatore"] for r in rows_ag if r["operatore"]))
with fa1: sel_pv_ag = st.selectbox("Punto Vendita", pvs_ag, key="fpv_ag")
with fa2: sel_op_ag = st.selectbox("Operatore", ops_ag, key="fop_ag")
with fa3: search_ag = st.text_input("Cerca (PDA/DOC · Operatore · Punto Vendita)", key="fsrch_ag")

def apply_filters(rows):
    f = rows[:]
    if sel_pv_ag != "Tutti": f=[r for r in f if r["punto_vendita"]==sel_pv_ag]
    if sel_op_ag != "Tutti": f=[r for r in f if r["operatore"]==sel_op_ag]
    if search_ag:
        s=search_ag.upper()
        f=[r for r in f if s in r["pda_norm"] or s in r["operatore"].upper()
           or s in r["punto_vendita"].upper() or s in r["target"].upper()]
    return f

def excel_download(df, fname):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Pratiche")
    return buf.getvalue()

with tab1:
    rows_f = apply_filters(completi)
    st.markdown(f"**{len(rows_f)}** pratiche complete nella selezione · Importo da liquidare: **{fmt_cur(sum(r['_match_pag']['importo_tot'] for r in rows_f if r['_match_pag']))}**")
    df_t = build_table_agenti(rows_f)
    if not df_t.empty:
        st.dataframe(df_t, use_container_width=True, height=min(60+len(df_t)*38,500))
        st.download_button("📥 Esporta Excel pratiche complete",
            data=excel_download(df_t, "completi"),
            file_name=f"agenti_completi_{upl_agenti.name}",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tab2:
    rows_f = apply_filters(solo_ins)
    st.markdown(f"**{len(rows_f)}** pratiche inserite ma non ancora pagate da Fastweb")
    df_t = build_table_agenti(rows_f)
    if not df_t.empty:
        st.dataframe(df_t, use_container_width=True, height=min(60+len(df_t)*38,500))
        st.download_button("📥 Esporta Excel pratiche in attesa",
            data=excel_download(df_t, "solo_ins"),
            file_name=f"agenti_in_attesa_{upl_agenti.name}",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tab3:
    rows_f = apply_filters(solo_pag)
    st.markdown(f"**{len(rows_f)}** pratiche pagate ma non trovate nel gestionale agenti")
    df_t = build_table_agenti(rows_f)
    if not df_t.empty:
        st.dataframe(df_t, use_container_width=True, height=min(60+len(df_t)*38,500))
        st.download_button("📥 Esporta Excel",
            data=excel_download(df_t, "solo_pag"),
            file_name=f"agenti_solo_pagato_{upl_agenti.name}",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tab4:
    rows_f = apply_filters(non_trovati)
    st.markdown(f"**{len(rows_f)}** pratiche non trovate né nel pagato né nell'inserito — verificare")
    df_t = build_table_agenti(rows_f)
    if not df_t.empty:
        st.dataframe(df_t, use_container_width=True, height=min(60+len(df_t)*38,500))
        st.download_button("📥 Esporta Excel",
            data=excel_download(df_t, "non_trovati"),
            file_name=f"agenti_non_trovati_{upl_agenti.name}",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ─── RIEPILOGO PAGAMENTI PER OPERATORE ───────────
st.divider()
st.markdown("### 💶 Riepilogo compensi per operatore")
st.caption("Basato sulle pratiche complete (inserite + pagate)")

if completi:
    riepilogo = {}
    for r in apply_filters(completi):
        op = r["operatore"] or "N/D"
        pag = r["_match_pag"]
        if op not in riepilogo:
            riepilogo[op] = {"Operatore":op,"Punto Vendita":r["punto_vendita"],
                             "Pratiche":0,"Base €":0.0,"Gara €":0.0,"Totale €":0.0}
        riepilogo[op]["Pratiche"] += 1
        if pag:
            riepilogo[op]["Base €"]   += pag["importo_base"] or 0
            riepilogo[op]["Gara €"]   += pag["importo_gara"] or 0
            riepilogo[op]["Totale €"] += pag["importo_tot"]  or 0

    df_riepilogo = pd.DataFrame(list(riepilogo.values())).sort_values("Totale €", ascending=False)
    df_riepilogo["Base €"]   = df_riepilogo["Base €"].apply(fmt_cur)
    df_riepilogo["Gara €"]   = df_riepilogo["Gara €"].apply(fmt_cur)
    df_riepilogo["Totale €"] = df_riepilogo["Totale €"].apply(fmt_cur)
    st.dataframe(df_riepilogo, use_container_width=True, hide_index=True)

    buf_riepilogo = io.BytesIO()
    df_riepilogo_raw = pd.DataFrame(list(riepilogo.values())).sort_values("Totale €", ascending=False)
    with pd.ExcelWriter(buf_riepilogo, engine="openpyxl") as w:
        df_riepilogo_raw.to_excel(w, index=False, sheet_name="Riepilogo operatori")
    st.download_button("📥 Esporta riepilogo compensi Excel",
        data=buf_riepilogo.getvalue(),
        file_name=f"riepilogo_compensi_{upl_agenti.name}",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.caption("Nessuna pratica completa con i filtri correnti.")
