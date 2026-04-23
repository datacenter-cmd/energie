import streamlit as st
import pandas as pd
import io, os
from auth import require_login, get_role

st.set_page_config(page_title="VIS Energia", page_icon="📋", layout="wide")
name, username = require_login()
role = get_role()

st.markdown("""
<style>
.vis-header{background:linear-gradient(135deg,#1a7abf,#0d5a8a);color:#fff;border-radius:12px;
    padding:20px 28px;margin-bottom:1.5rem}
.vis-header h2{margin:0;font-size:1.4rem;font-weight:800}
.vis-header p{margin:4px 0 0;opacity:.85;font-size:.9rem}
</style>""", unsafe_allow_html=True)

st.markdown(f"""
<div class="vis-header">
    <h2>📋 VIS Energia — Compilazione Pratiche</h2>
    <p>Operatore: <strong>{name}</strong> · Compila i dati e segna ogni pratica come Sì / No</p>
</div>""", unsafe_allow_html=True)

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'vis_energia.xlsx')

def load_data():
    if os.path.exists(DATA_PATH):
        df = pd.read_excel(DATA_PATH, sheet_name=0)
    else:
        df = pd.DataFrame(columns=[
            'DATA INSERIMENTO','NEGOZIO','OPERATORE','FWEN',
            'PARTITA IVA','CODICE FISCALE','POD',
            'NOME E COGNOME CLIENTE','TIPOLOGIA','PAGABILE'
        ])
    # Normalizza nomi colonne (rimuove spazi)
    df.columns = [c.strip() for c in df.columns]
    # Aggiunge PAGABILE se mancante
    if 'PAGABILE' not in df.columns:
        df['PAGABILE'] = ''
    # Converte tutti i campi in stringa pulita (evita problemi di tipo con data_editor)
    for col in ['FWEN','PARTITA IVA','CODICE FISCALE','POD','NOME E COGNOME CLIENTE','PAGABILE']:
        df[col] = df[col].fillna('').astype(str).str.strip()
    # Data come stringa
    df['DATA INSERIMENTO'] = pd.to_datetime(df['DATA INSERIMENTO'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('')
    return df

df = load_data()

# ─── KPI ──────────────────────────────────────────────
tot      = len(df)
pagabili = (df['PAGABILE'].str.upper() == 'SÌ').sum() + (df['PAGABILE'].str.upper() == 'SI').sum()
non_pag  = (df['PAGABILE'].str.upper() == 'NO').sum()
da_verif = tot - pagabili - non_pag

c1,c2,c3,c4 = st.columns(4)
for col, label, val, color in [
    (c1, "PRATICHE TOTALI",  tot,      "#1a1a1a"),
    (c2, "✅ PAGABILI",      pagabili, "#1e7e4a"),
    (c3, "❌ NON PAGABILI",  non_pag,  "#c0392b"),
    (c4, "⏳ DA VERIFICARE", da_verif, "#b8860b"),
]:
    with col:
        st.markdown(f"""<div style="background:#fff;border:1px solid #e0e0e0;border-radius:12px;
            padding:16px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.07);min-height:90px">
            <div style="font-size:.72rem;font-weight:800;color:#1a1a1a;text-transform:uppercase;
                letter-spacing:.04em;margin-bottom:6px">{label}</div>
            <div style="font-size:1.8rem;font-weight:800;color:{color}">{val}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── TABELLA EDITABILE ────────────────────────────────
st.markdown("### ✏️ Modifica pratiche")
st.caption("Compila i campi vuoti. Per **Pagabile** scrivi **Sì** oppure **No**. Poi clicca Salva.")

col_config = {
    'DATA INSERIMENTO':       st.column_config.TextColumn("Data",          disabled=True, width="small"),
    'NEGOZIO':                st.column_config.TextColumn("Negozio",       disabled=True, width="medium"),
    'OPERATORE':              st.column_config.TextColumn("Operatore",     disabled=True, width="medium"),
    'TIPOLOGIA':              st.column_config.TextColumn("Tipologia",     disabled=True, width="small"),
    'FWEN':                   st.column_config.TextColumn("FWEN",                         width="medium"),
    'PARTITA IVA':            st.column_config.TextColumn("Partita IVA",                  width="medium"),
    'CODICE FISCALE':         st.column_config.TextColumn("Cod. Fiscale",                 width="medium"),
    'POD':                    st.column_config.TextColumn("POD",                          width="medium"),
    'NOME E COGNOME CLIENTE': st.column_config.TextColumn("Cliente",                      width="large"),
    'PAGABILE':               st.column_config.TextColumn("Pagabile (Sì/No)",             width="small"),
}

edited_df = st.data_editor(
    df,
    column_config=col_config,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    height=min(400, 50 + len(df) * 40),
)

# ─── SALVA / EXPORT ───────────────────────────────────
col_save, col_export = st.columns([1, 4])
with col_save:
    if st.button("💾 Salva modifiche", type="primary", use_container_width=True):
        try:
            # Normalizza PAGABILE prima di salvare
            edited_df['PAGABILE'] = edited_df['PAGABILE'].str.strip().replace({
                'si':'Sì','SI':'Sì','sì':'Sì','SÌ':'Sì',
                'no':'No','NO':'No',
            })
            edited_df.to_excel(DATA_PATH, sheet_name='APRILE 2026', index=False)
            st.success("✅ Modifiche salvate!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Errore nel salvataggio: {e}")

with col_export:
    buf = io.BytesIO()
    edited_df.to_excel(buf, sheet_name='APRILE 2026', index=False)
    buf.seek(0)
    st.download_button("⬇️ Esporta Excel", buf,
        file_name="VIS_BIGGBAOO_ENERGIA_compilato.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
