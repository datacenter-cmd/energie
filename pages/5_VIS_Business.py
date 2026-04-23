import streamlit as st
import pandas as pd
import os
from datetime import date

# ── Config ──────────────────────────────────────────────────────────────────
st.set_page_config(page_title="VIS Business · BIGGBAOO", layout="wide")

NEGOZI = [
    "comet pontedera", "euronics corciano", "euronics gavinana",
    "euronics grosseto", "euronics montecatini", "euronics parco prato",
    "mw agliana", "mw collestrada", "mw empoli", "mw figline",
    "mw gigli", "mw novoli", "mw pisa", "mw roma (porta di)", "mw roma est"
]
OPERATORI = [
    "Adelina Meta", "Aissam El Moujaid", "Anastasya Radecha",
    "Barbara Mattiacci", "Carmen Davila", "David John Gallo",
    "Ditifet", "Emiliano Romei", "Fabian Sulmina", "Feris Rahmouni",
    "Francesco Belmonte", "Francesco Butelli", "Giovanni Giglio",
    "Gloria La Giusa", "Mariami Iashvili", "Matteo Stefanelli",
    "Nicole Gamboa", "Samuele Guido", "Serenella Nacci",
    "Silvia Saglimbeni", "Simona Cucu"
]
PIANI = ["fissa comfort", "fissa fwa5g", "fissa smart", "fissa ob",
         "mobile smart", "mobile comfort", "mobile ob", "easy rent"]
PAGABILE_OPTS = ["sì", "no", "da verificare"]
PT_OPTS = ["fissa", "mobile", "easy r", ""]

DATA_FILE = "data/vis_business_2026.xlsx"
MESI = ["gennaio 2026", "febbraio 2026", "marzo 2026", "aprile 2026"]

# ── Auth ─────────────────────────────────────────────────────────────────────
USERS = st.secrets.get("credentials", {})

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("## 🔐 Accesso VIS Business")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Entra"):
            if USERS.get(u) == p:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else:
                st.error("Credenziali errate.")
        st.stop()

check_login()

# ── Header ───────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([8, 1])
with col_h1:
    st.markdown("## 📋 VIS Business 2026 · Pratiche Vodafone P.IVA")
with col_h2:
    if st.button("🚪 Esci", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

st.divider()

# ── Carica dati ──────────────────────────────────────────────────────────────
def load_data(mese):
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_excel(DATA_FILE, sheet_name=mese)
            df.columns = df.columns.str.strip()
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=[
        "negozio", "operatore", "id pratica", "partita iva",
        "ragione sociale", "seriale sim", "piano tariffario inserito",
        "inserito", "attivato", "pagabile", "note", "pt inserito", "pt attivato"
    ])

def save_data(df_dict):
    os.makedirs("data", exist_ok=True)
    with pd.ExcelWriter(DATA_FILE, engine="openpyxl") as writer:
        for mese, df in df_dict.items():
            df.to_excel(writer, sheet_name=mese, index=False)

# ── Selezione mese ───────────────────────────────────────────────────────────
mese_sel = st.selectbox("📅 Seleziona mese", MESI)

df = load_data(mese_sel)

# Normalizza colonne pagabile e pt
for c in ["pagabile", "pt inserito", "pt attivato"]:
    if c not in df.columns:
        df[c] = ""
    df[c] = df[c].fillna("").astype(str).str.strip()

# Rinomina colonna pagabile variabile (es. "pagabile ad aprile")
pag_col = [c for c in df.columns if c.startswith("pagabile")]
if pag_col and pag_col[0] != "pagabile":
    df.rename(columns={pag_col[0]: "pagabile"}, inplace=True)

# ── Vista mobile / desktop ───────────────────────────────────────────────────
vista = st.radio("Vista", ["🖥️ Desktop (tabella)", "📱 Mobile (schede)"], horizontal=True)

# ── Funzione colori ──────────────────────────────────────────────────────────
def color_pagabile(val):
    v = str(val).strip().lower()
    if v == "sì":
        return "background-color: #c8f7c5"
    elif v == "no":
        return "background-color: #f7c5c5"
    elif v == "da verificare":
        return "background-color: #fff3cd"
    return ""

if "df_edit" not in st.session_state or st.session_state.get("mese_corrente") != mese_sel:
    st.session_state.df_edit = df.copy()
    st.session_state.mese_corrente = mese_sel

df_work = st.session_state.df_edit

# ── DESKTOP ──────────────────────────────────────────────────────────────────
if vista == "🖥️ Desktop (tabella)":
    edited = st.data_editor(
        df_work,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "negozio": st.column_config.SelectboxColumn("Negozio", options=NEGOZI, required=False),
            "operatore": st.column_config.SelectboxColumn("Operatore", options=OPERATORI, required=False),
            "piano tariffario inserito": st.column_config.SelectboxColumn("Piano tariffario", options=PIANI, required=False),
            "pagabile": st.column_config.SelectboxColumn("Pagabile", options=PAGABILE_OPTS, required=False),
            "pt inserito": st.column_config.SelectboxColumn("PT inserito", options=PT_OPTS, required=False),
            "pt attivato": st.column_config.SelectboxColumn("PT attivato", options=PT_OPTS, required=False),
            "inserito": st.column_config.DateColumn("Inserito", format="DD/MM/YYYY"),
            "attivato": st.column_config.DateColumn("Attivato", format="DD/MM/YYYY"),
            "id pratica": st.column_config.TextColumn("ID Pratica"),
            "partita iva": st.column_config.TextColumn("Partita IVA"),
            "ragione sociale": st.column_config.TextColumn("Ragione Sociale"),
            "seriale sim": st.column_config.TextColumn("Seriale SIM"),
            "note": st.column_config.TextColumn("Note"),
        },
        key=f"editor_{mese_sel}"
    )
    st.session_state.df_edit = edited

# ── MOBILE ───────────────────────────────────────────────────────────────────
else:
    for i, row in df_work.iterrows():
        with st.expander(f"#{i+1} — {row.get('ragione sociale','') or 'Nuova pratica'} | {row.get('negozio','')}", expanded=False):
            c1, c2 = st.columns(2)
            df_work.at[i, "negozio"] = c1.selectbox("Negozio", [""] + NEGOZI, index=([""] + NEGOZI).index(row.get("negozio","")) if row.get("negozio","") in NEGOZI else 0, key=f"neg_{i}")
            df_work.at[i, "operatore"] = c2.selectbox("Operatore", [""] + OPERATORI, index=([""] + OPERATORI).index(row.get("operatore","")) if row.get("operatore","") in OPERATORI else 0, key=f"op_{i}")
            df_work.at[i, "ragione sociale"] = c1.text_input("Ragione Sociale", value=str(row.get("ragione sociale","") or ""), key=f"rs_{i}")
            df_work.at[i, "partita iva"] = c2.text_input("Partita IVA", value=str(row.get("partita iva","") or ""), key=f"piva_{i}")
            df_work.at[i, "id pratica"] = c1.text_input("ID Pratica", value=str(row.get("id pratica","") or ""), key=f"idp_{i}")
            df_work.at[i, "seriale sim"] = c2.text_input("Seriale SIM", value=str(row.get("seriale sim","") or ""), key=f"sim_{i}")
            df_work.at[i, "piano tariffario inserito"] = c1.selectbox("Piano tariffario", [""] + PIANI, key=f"pt_{i}")
            df_work.at[i, "pagabile"] = c2.selectbox("Pagabile", PAGABILE_OPTS, index=PAGABILE_OPTS.index(row.get("pagabile","sì")) if row.get("pagabile","") in PAGABILE_OPTS else 0, key=f"pag_{i}")
            df_work.at[i, "pt inserito"] = c1.selectbox("PT inserito", PT_OPTS, key=f"pti_{i}")
            df_work.at[i, "pt attivato"] = c2.selectbox("PT attivato", PT_OPTS, key=f"pta_{i}")
            df_work.at[i, "note"] = st.text_input("Note", value=str(row.get("note","") or ""), key=f"note_{i}")

    if st.button("➕ Aggiungi pratica"):
        new_row = {c: "" for c in df_work.columns}
        st.session_state.df_edit = pd.concat([df_work, pd.DataFrame([new_row])], ignore_index=True)
        st.rerun()

# ── Anteprima colorata ────────────────────────────────────────────────────────
st.markdown("#### 🎨 Anteprima colorata — colonna Pagabile")
styled = st.session_state.df_edit.style.applymap(color_pagabile, subset=["pagabile"])
st.dataframe(styled, use_container_width=True)

# ── Salva / Export ────────────────────────────────────────────────────────────
col_s1, col_s2 = st.columns(2)

with col_s1:
    if st.button("💾 Salva", use_container_width=True):
        all_data = {}
        for m in MESI:
            if m == mese_sel:
                all_data[m] = st.session_state.df_edit
            else:
                all_data[m] = load_data(m)
        save_data(all_data)
        st.success("Dati salvati!")

with col_s2:
    import io
    buf = io.BytesIO()
    st.session_state.df_edit.to_excel(buf, index=False)
    st.download_button(
        "⬇️ Esporta Excel",
        data=buf.getvalue(),
        file_name=f"vis_business_{mese_sel.replace(' ','_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# ── Riepilogo mese ────────────────────────────────────────────────────────────
st.divider()
st.markdown("#### 📊 Riepilogo mese")
df_rie = st.session_state.df_edit.copy()
col_r1, col_r2, col_r3, col_r4 = st.columns(4)
col_r1.metric("Totale pratiche", len(df_rie))
col_r2.metric("✅ Pagabili", len(df_rie[df_rie["pagabile"].str.strip().str.lower() == "sì"]))
col_r3.metric("❌ Non pagabili", len(df_rie[df_rie["pagabile"].str.strip().str.lower() == "no"]))
col_r4.metric("⚠️ Da verificare", len(df_rie[df_rie["pagabile"].str.strip().str.lower() == "da verificare"]))
