import streamlit as st
import pandas as pd
import io
from auth import require_login
from drive import get_all_files, download_by_id
from utils import (norm, fmt_cur, fmt_date, ts_now,
                   parse_pratiche, parse_pag_fastweb, parse_pag_agenti,
                   match_agenti_v2, load_storico, add_to_storico, STORICO_AGENTI)

st.set_page_config(page_title="BIGGBAOO ↔ Agenti", page_icon="👥", layout="wide")

# ─── AUTH ────────────────────────────────────────
name, username = require_login()

# ─── CSS ─────────────────────────────────────────
st.markdown("""
<style>
.kpi-card{background:#fff;border:1px solid #e0e0e0;border-radius:12px;padding:18px 12px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.07)}
.kpi-label{font-size:.72rem;font-weight:600;letter-spacing:.08em;color:#888;text-transform:uppercase;margin-bottom:4px}
.kpi-value{font-size:1.7rem;font-weight:700;color:#1a1a1a}
.kpi-sub{font-size:.78rem;color:#aaa;margin-top:2px}
.ok{color:#1e7e4a}.err{color:#c0392b}.gold{color:#b8860b}.pri{color:#1a7abf}
</style>""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────
with st.sidebar:
    st.markdown(f"👤 **{name}**")
    st.divider()
    st.markdown("**📂 File agenti da Google Drive**")

    drive_files = get_all_files("agenti_")
    uploaded = None

    if drive_files:
        nomi = [n for n, _ in drive_files]
        scelta = st.selectbox("Seleziona file", nomi, index=0)
        fid = dict(drive_files)[scelta]
        if st.button("📥 Carica da Drive"):
            buf = download_by_id(fid)
            st.session_state["ag2_buf"] = buf
            st.session_state["ag2_name"] = scelta
        if "ag2_buf" in st.session_state:
            uploaded = st.session_state["ag2_buf"]
            uploaded.name = st.session_state["ag2_name"]
    else:
        st.caption("Nessun file su Drive — carica manualmente")

    manual = st.file_uploader("oppure carica .xlsx", type=["xlsx","xls"])
    if manual:
        uploaded = manual

    st.divider()
    st.markdown("**🕐 Storico caricamenti**")
    storico = load_storico(STORICO_AGENTI)
    if storico:
        for s in storico[:5]:
            nc = s.get("totale",0) - s.get("complete",0)
            st.markdown(f"📄 **{s.get('filename','')}**  \n🕐 {s.get('ts','')} · ✅{s.get('complete',0)} ❌{nc}")
            st.markdown("---")
    else:
        st.caption("Nessun caricamento precedente")
    st.divider()
    st.caption("👥 BIGGBAOO ↔ Agenti")

# ─── HEADER ──────────────────────────────────────
st.markdown("# 👥 BIGGBAOO ↔ Agenti")
st.markdown("Pratiche agenti · Pagamenti Fastweb · Compensi corrisposti")
st.divider()

if not uploaded:
    st.info("👈 Carica il file agenti dalla barra laterale.")
    st.stop()

# ─── LETTURA FILE ─────────────────────────────────
try:
    xl = pd.ExcelFile(uploaded)
    sheets = xl.sheet_names

    if "pratiche" not in sheets:
        st.error("❌ Sheet 'pratiche' non trovato. Usa il template standard.")
        st.stop()

    df_prat = pd.read_excel(uploaded, sheet_name="pratiche")
    df_fw   = pd.read_excel(uploaded, sheet_name="pagamenti_fastweb") if "pagamenti_fastweb" in sheets else pd.DataFrame()
    df_ag   = pd.read_excel(uploaded, sheet_name="pagamenti_agenti")  if "pagamenti_agenti"  in sheets else pd.DataFrame()

    pratiche  = parse_pratiche(df_prat)
    fw_map    = parse_pag_fastweb(df_fw)   if not df_fw.empty   else {}
    ag_map    = parse_pag_agenti(df_ag)    if not df_ag.empty   else {}
    pratiche  = match_agenti_v2(pratiche, fw_map, ag_map)

except Exception as e:
    st.error(f"❌ Errore lettura file: {e}")
    st.stop()

if not pratiche:
    st.warning("Nessuna pratica trovata nel file.")
    st.stop()

# ─── KPI ─────────────────────────────────────────
totale    = len(pratiche)
completi  = sum(1 for r in pratiche if r["_stato_match"] == "✅ Completo")
fw_pagati = sum(1 for r in pratiche if r["_fw"])
ag_pagati = sum(1 for r in pratiche if r["_ag"])
non_trov  = sum(1 for r in pratiche if r["_stato_match"] == "❌ Non trovato")

tot_fw    = sum((r["_fw"]["importo_tot"]  or 0) for r in pratiche if r["_fw"])
tot_ag    = sum((r["_ag"]["importo_pagato"] or 0) for r in pratiche if r["_ag"])
margine   = tot_fw - tot_ag

# Salva storico
fname = getattr(uploaded, "name", "agenti.xlsx")
add_to_storico(STORICO_AGENTI, {
    "filename": fname, "ts": ts_now(),
    "totale": totale, "complete": completi,
})

c1,c2,c3,c4,c5,c6 = st.columns(6)
kpis = [
    (c1, "PRATICHE TOTALI",    totale,            "",                         ""),
    (c2, "✅ COMPLETE",        completi,           f"{round(completi/totale*100)}% del totale", "ok"),
    (c3, "💶 FASTWEB PAGATO",  fmt_cur(tot_fw),   f"{fw_pagati} pratiche",     "gold"),
    (c4, "👤 AGENTI PAGATI",   fmt_cur(tot_ag),   f"{ag_pagati} pratiche",     "pri"),
    (c5, "📈 MARGINE",         fmt_cur(margine),  "fastweb - agenti",          "ok" if margine >= 0 else "err"),
    (c6, "❌ NON TROVATE",     non_trov,           f"{round(non_trov/totale*100)}% del totale", "err"),
]
for col, label, val, sub, cls in kpis:
    with col:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value {cls}">{val}</div>
            <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── FILTRI ──────────────────────────────────────
col_f1, col_f2, col_f3 = st.columns(3)
operatori = sorted(set(r["operatore"] for r in pratiche if r["operatore"]))
stati_match = sorted(set(r["_stato_match"] for r in pratiche))
target_list = sorted(set(r["target"] for r in pratiche if r["target"]))

with col_f1:
    sel_op  = st.multiselect("Operatore", operatori)
with col_f2:
    sel_sm  = st.multiselect("Stato incrocio", stati_match)
with col_f3:
    sel_tgt = st.multiselect("Target (mese)", target_list)

filtered = pratiche
if sel_op:  filtered = [r for r in filtered if r["operatore"] in sel_op]
if sel_sm:  filtered = [r for r in filtered if r["_stato_match"] in sel_sm]
if sel_tgt: filtered = [r for r in filtered if r["target"] in sel_tgt]

# ─── TABELLA ─────────────────────────────────────
st.markdown(f"### 📋 Dettaglio pratiche ({len(filtered)} righe)")

table_rows = []
for r in filtered:
    fw = r["_fw"] or {}
    ag = r["_ag"] or {}
    table_rows.append({
        "Stato":        r["_stato_match"],
        "Data":         r["data"],
        "Target":       r["target"],
        "Operatore":    r["operatore"],
        "Punto Vendita":r["punto_vendita"],
        "Servizio":     r["servizio"],
        "Stato Gest.":  r["stato"],
        "PDA/DOC":      r["pda"],
        "Cliente":      r["cliente"],
        "Offerta FW":   fw.get("offerta","—"),
        "Base FW €":    fmt_cur(fw["importo_base"]) if fw else "—",
        "Gara FW €":    fmt_cur(fw["importo_gara"]) if fw else "—",
        "Tot FW €":     fmt_cur(fw["importo_tot"])  if fw else "—",
        "Data Att.":    fw.get("data_att","—")       if fw else "—",
        "Pag. Agente €":fmt_cur(ag["importo_pagato"]) if ag else "—",
        "% Ragg.":      ag.get("pct","—")             if ag else "—",
        "Data Pag.":    ag.get("data_pag","—")         if ag else "—",
    })

df_table = pd.DataFrame(table_rows)
st.dataframe(df_table, use_container_width=True, height=450,
    column_config={"Stato": st.column_config.TextColumn(width="medium")})

# ─── RIEPILOGO PER OPERATORE ─────────────────────
st.divider()
st.markdown("### 👤 Riepilogo per operatore")

op_rows = []
for op in sorted(set(r["operatore"] for r in filtered if r["operatore"])):
    op_prat = [r for r in filtered if r["operatore"] == op]
    n_tot  = len(op_prat)
    n_comp = sum(1 for r in op_prat if r["_stato_match"] == "✅ Completo")
    n_fw   = sum(1 for r in op_prat if r["_fw"])
    n_ag   = sum(1 for r in op_prat if r["_ag"])
    t_fw   = sum((r["_fw"]["importo_tot"] or 0)     for r in op_prat if r["_fw"])
    t_ag   = sum((r["_ag"]["importo_pagato"] or 0)  for r in op_prat if r["_ag"])
    op_rows.append({
        "Operatore":       op,
        "Pratiche":        n_tot,
        "Complete":        n_comp,
        "FW Pagate":       n_fw,
        "AG Pagate":       n_ag,
        "Tot Fastweb €":   fmt_cur(t_fw),
        "Tot Agente €":    fmt_cur(t_ag),
        "Margine €":       fmt_cur(t_fw - t_ag),
    })

st.dataframe(pd.DataFrame(op_rows), use_container_width=True, hide_index=True)

# ─── EXPORT ──────────────────────────────────────
st.divider()
buf_out = io.BytesIO()
with pd.ExcelWriter(buf_out, engine="openpyxl") as writer:
    df_table.to_excel(writer, sheet_name="dettaglio", index=False)
    pd.DataFrame(op_rows).to_excel(writer, sheet_name="riepilogo_operatori", index=False)
buf_out.seek(0)
mese = fname.replace("agenti_","").replace(".xlsx","").replace(".xls","")
st.download_button("⬇️ Esporta Excel", buf_out,
    file_name=f"report_agenti_{mese}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
