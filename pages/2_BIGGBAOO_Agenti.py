import streamlit as st
import pandas as pd
import io
from auth import require_login
from drive import get_all_files, download_by_id
from utils import (norm, fmt_cur, fmt_date, ts_now,
                   build_fw_map, build_ag_map, match_row,
                   parse_pratiche_v2, load_storico, add_to_storico, STORICO_AGENTI)

st.set_page_config(page_title="BIGGBAOO ↔ Agenti", page_icon="👥", layout="wide")
name, username = require_login()

st.markdown("""
<style>
.kpi-card{background:#fff;border:1px solid #e0e0e0;border-radius:12px;padding:18px 12px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.07);height:110px;display:flex;flex-direction:column;justify-content:center;align-items:center}
.kpi-label{font-size:.72rem;font-weight:600;letter-spacing:.08em;color:#888;text-transform:uppercase;margin-bottom:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;width:100%}
.kpi-value{font-size:1.55rem;font-weight:700;color:#1a1a1a;white-space:nowrap}
.kpi-sub{font-size:.75rem;color:#aaa;margin-top:2px;white-space:nowrap}
.ok{color:#1e7e4a}.err{color:#c0392b}.gold{color:#b8860b}.pri{color:#1a7abf}
</style>""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────
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
    if manual: uploaded = manual
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

st.markdown("# 👥 BIGGBAOO ↔ Agenti")
st.markdown("Pratiche agenti · Pagamenti Fastweb · Compensi corrisposti")
st.divider()

if not uploaded:
    st.info("👈 Carica il file agenti dalla barra laterale.")
    st.stop()

# ─── LETTURA FILE ─────────────────────────────────────
try:
    xl = pd.ExcelFile(uploaded)
    sheets = xl.sheet_names

    if "pratiche" not in sheets:
        st.error("❌ Sheet 'pratiche' non trovato. Usa il template standard.")
        st.stop()

    df_prat = pd.read_excel(uploaded, sheet_name="pratiche")
    df_fw_raw = pd.read_excel(uploaded, sheet_name="pagamenti_fastweb") if "pagamenti_fastweb" in sheets else pd.DataFrame()
    df_ag_raw = pd.read_excel(uploaded, sheet_name="pagamenti_agenti")  if "pagamenti_agenti"  in sheets else pd.DataFrame()

    # Carica tutti i fogli vis_fattura_*
    vis_sheets = []
    for sh in sheets:
        if sh.startswith("vis_fattura_"):
            vis_sheets.append(pd.read_excel(uploaded, sheet_name=sh))

    pratiche_all = parse_pratiche_v2(df_prat)

except Exception as e:
    st.error(f"❌ Errore lettura file: {e}")
    st.stop()

if not pratiche_all:
    st.warning("Nessuna pratica trovata nel file.")
    st.stop()

# ─── SELETTORE MESE DI COMPETENZA ─────────────────────
mesi_disponibili = sorted(set(r["target"] for r in pratiche_all if r["target"]), reverse=True)
TUTTI = "📊 TUTTI I MESI"

st.markdown("### 📅 Seleziona il mese di competenza")
col_ms, col_info = st.columns([2,3])
with col_ms:
    mese_sel = st.selectbox("Mese", [TUTTI] + mesi_disponibili, index=0, label_visibility="collapsed")
with col_info:
    if mese_sel == TUTTI:
        st.info(f"**Tutti i mesi** → {len(pratiche_all)} pratiche totali nel file")
    else:
        n_mese = sum(1 for r in pratiche_all if r["target"] == mese_sel)
        st.info(f"**{mese_sel}** → {n_mese} pratiche nel file")

st.divider()

# Filtra pratiche per mese selezionato
if mese_sel == TUTTI:
    pratiche_mese = pratiche_all
else:
    pratiche_mese = [r for r in pratiche_all if r["target"] == mese_sel]

# Costruisci mappe per il matching
fw_map = build_fw_map(df_fw_raw) if not df_fw_raw.empty else {}

# Per i vis_fattura: se "tutti" usa tutti i fogli, altrimenti solo quello del mese
if mese_sel == TUTTI:
    vis_mese = vis_sheets
else:
    vis_mese = []
    mese_lower = mese_sel.lower()
    for sh in sheets:
        if sh.startswith("vis_fattura_") and sh != "vis_fattura_TUTTI":
            tag = sh.replace("vis_fattura_","").replace("_"," ")
            if any(p in mese_lower for p in tag.split()):
                vis_mese.append(pd.read_excel(uploaded, sheet_name=sh))
    if not vis_mese:
        vis_mese = vis_sheets

ag_map = build_ag_map(df_ag_raw if not df_ag_raw.empty else pd.DataFrame(), vis_mese)

# Esegui matching
pratiche = [match_row(r, fw_map, ag_map) for r in pratiche_mese]

# ─── KPI ──────────────────────────────────────────────
totale   = len(pratiche)
completi = sum(1 for r in pratiche if r["_stato_match"] == "✅ Completo")
fw_pag   = sum(1 for r in pratiche if r["_fw"])
ag_pag   = sum(1 for r in pratiche if r["_ag"])
non_trov = sum(1 for r in pratiche if r["_stato_match"] == "❌ Non trovato")
tot_fw   = sum((r["_fw"]["importo_tot"] or 0) for r in pratiche if r["_fw"])
tot_ag   = sum((r["_ag"]["importo_pagato"] or 0) for r in pratiche if r["_ag"])
margine  = tot_fw - tot_ag

fname = getattr(uploaded, "name", "agenti.xlsx")
add_to_storico(STORICO_AGENTI, {"filename": fname, "ts": ts_now(), "totale": totale, "complete": completi})

c1,c2,c3,c4,c5,c6 = st.columns(6)
kpis = [
    (c1, "PRATICHE TOTALI" if mese_sel == TUTTI else "PRATICHE MESE",     totale,           "",                                   ""),
    (c2, "✅ COMPLETE",       completi,          f"{round(completi/totale*100) if totale else 0}% del totale", "ok"),
    (c3, "💶 FASTWEB PAGATO", fmt_cur(tot_fw),  f"{fw_pag} pratiche",                 "gold"),
    (c4, "👤 AGENTI PAGATI",  fmt_cur(tot_ag),  f"{ag_pag} pratiche",                 "pri"),
    (c5, "📈 MARGINE",        fmt_cur(margine), "fastweb - agenti",                   "ok" if margine >= 0 else "err"),
    (c6, "❌ NON TROVATE",    non_trov,          f"{round(non_trov/totale*100) if totale else 0}% del totale", "err"),
]
for col, label, val, sub, cls in kpis:
    with col:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value {cls}">{val}</div>
            <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── FILTRI ───────────────────────────────────────────
col_f1, col_f2 = st.columns(2)
operatori   = sorted(set(r["operatore"] for r in pratiche if r["operatore"]))
stati_match = sorted(set(r["_stato_match"] for r in pratiche))
with col_f1:
    sel_op = st.multiselect("Operatore", operatori)
with col_f2:
    sel_sm = st.multiselect("Stato incrocio", stati_match)

filtered = pratiche
if sel_op: filtered = [r for r in filtered if r["operatore"] in sel_op]
if sel_sm: filtered = [r for r in filtered if r["_stato_match"] in sel_sm]

# ─── TABELLA ──────────────────────────────────────────
st.markdown(f"### 📋 Dettaglio pratiche — {mese_sel} ({len(filtered)} righe)")

table_rows = []
for r in filtered:
    fw = r["_fw"] or {}
    ag = r["_ag"] or {}
    table_rows.append({
        "Stato":         r["_stato_match"],
        "Data":          r["data"],
        "Operatore":     r["operatore"],
        "Punto Vendita": r["punto_vendita"],
        "Servizio":      r["servizio"],
        "Stato Gest.":   r["stato"],
        "PDA/DOC":       r["pda"],
        "Cliente":       r["cliente"],
        "Offerta FW":    fw.get("offerta","—"),
        "Base FW €":     fmt_cur(fw["importo_base"]) if fw else "—",
        "Gara FW €":     fmt_cur(fw["importo_gara"]) if fw else "—",
        "Tot FW €":      fmt_cur(fw["importo_tot"])  if fw else "—",
        "Data Att.":     fw.get("data_att","—")       if fw else "—",
        "Pag. Agente €": fmt_cur(ag["importo_pagato"]) if ag else "—",
        "% Ragg.":       ag.get("pct","—")             if ag else "—",
    })

df_table = pd.DataFrame(table_rows)
st.dataframe(df_table, use_container_width=True, height=450,
    column_config={"Stato": st.column_config.TextColumn(width="medium")})

# ─── RIEPILOGO PER OPERATORE ──────────────────────────
st.divider()
st.markdown(f"### 👤 Riepilogo per operatore — {mese_sel}")
op_rows = []
for op in sorted(set(r["operatore"] for r in filtered if r["operatore"])):
    op_p  = [r for r in filtered if r["operatore"] == op]
    n_tot = len(op_p)
    n_ok  = sum(1 for r in op_p if r["_stato_match"] == "✅ Completo")
    t_fw  = sum((r["_fw"]["importo_tot"] or 0)    for r in op_p if r["_fw"])
    t_ag  = sum((r["_ag"]["importo_pagato"] or 0) for r in op_p if r["_ag"])
    op_rows.append({
        "Operatore":     op,
        "Pratiche":      n_tot,
        "Complete":      n_ok,
        "Tot Fastweb €": fmt_cur(t_fw),
        "Tot Agente €":  fmt_cur(t_ag),
        "Margine €":     fmt_cur(t_fw - t_ag),
    })
st.dataframe(pd.DataFrame(op_rows), use_container_width=True, hide_index=True)

# ─── RIEPILOGO PER MESE (solo se TUTTI) ──────────────
if mese_sel == TUTTI:
    st.divider()
    st.markdown("### 📅 Riepilogo per mese")
    mese_rows = []
    for mese in sorted(set(r["target"] for r in pratiche if r["target"])):
        mp = [r for r in pratiche if r["target"] == mese]
        n_tot = len(mp)
        n_ok  = sum(1 for r in mp if r["_stato_match"] == "✅ Completo")
        n_fw  = sum(1 for r in mp if r["_fw"])
        n_ag  = sum(1 for r in mp if r["_ag"])
        t_fw  = sum((r["_fw"]["importo_tot"] or 0)    for r in mp if r["_fw"])
        t_ag  = sum((r["_ag"]["importo_pagato"] or 0) for r in mp if r["_ag"])
        mese_rows.append({
            "Mese":          mese,
            "Pratiche":      n_tot,
            "Complete":      n_ok,
            "FW Pagate":     n_fw,
            "AG Pagate":     n_ag,
            "Tot Fastweb €": fmt_cur(t_fw),
            "Tot Agente €":  fmt_cur(t_ag),
            "Margine €":     fmt_cur(t_fw - t_ag),
        })
    st.dataframe(pd.DataFrame(mese_rows), use_container_width=True, hide_index=True)

# ─── EXPORT ───────────────────────────────────────────
st.divider()
buf_out = io.BytesIO()
with pd.ExcelWriter(buf_out, engine="openpyxl") as writer:
    df_table.to_excel(writer, sheet_name="dettaglio", index=False)
    pd.DataFrame(op_rows).to_excel(writer, sheet_name="riepilogo_operatori", index=False)
    if mese_sel == TUTTI:
        pd.DataFrame(mese_rows).to_excel(writer, sheet_name="riepilogo_mesi", index=False)
buf_out.seek(0)
mese_tag = mese_sel.replace(" ","_").replace("/","_").replace("📊","ALL")
st.download_button("⬇️ Esporta Excel", buf_out,
    file_name=f"report_agenti_{mese_tag}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
