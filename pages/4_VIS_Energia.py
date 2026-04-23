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

col_hdr, col_exit = st.columns([6, 1])
with col_hdr:
    st.markdown(f"""
<div class="vis-header">
    <h2>📋 VIS Energia — Compilazione Pratiche</h2>
    <p>Operatore: <strong>{name}</strong> · Compila i dati e segna ogni pratica come Sì / No</p>
</div>""", unsafe_allow_html=True)
with col_exit:
    st.markdown("<div style='padding-top:18px'>", unsafe_allow_html=True)
    from auth import logout
    if st.button("🚪 Esci", use_container_width=True):
        logout()
    st.markdown("</div>", unsafe_allow_html=True)

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
    # Normalizza NEGOZIO e OPERATORE: strip spazi + forza ai valori della lista
    _negozi = ['comet pontedera', 'euronics corciano', 'euronics gavinana', 'euronics grosseto', 'euronics montecatini', 'euronics parco prato', 'mw agliana', 'mw collestrada', 'mw empoli', 'mw figline', 'mw gigli', 'mw novoli', 'mw pisa', 'mw roma est', 'mw roma (porta di)', 'mw roma primavera']
    _operatori = ['Adelina Meta', 'Aissam El Moujaid', 'Carmen Davila', 'Biggbaoo', 'David John Gallo', 'Emerson Espiritu', 'Emiliano Romei', 'Fabian Sulmina', 'Feris Rahmouni', 'Francesco Butelli', 'Giovanni Giglio', 'Gloria La Giusa', 'Katia Testa', 'Mariami Iashvili', 'Matteo Stefanelli', 'Nicole Gamboa', 'Samuele Guido', 'Serenella Nacci', 'Simona Cucu', 'Simone Marra', 'Yadira Davila']
    df['NEGOZIO']   = df['NEGOZIO'].str.strip().apply(
        lambda x: x if x in _negozi else '')
    df['OPERATORE'] = df['OPERATORE'].str.strip().apply(
        lambda x: x if x in _operatori else '')
    # Normalizza PAGABILE ai soli valori ammessi dal dropdown
    df['PAGABILE'] = df['PAGABILE'].str.strip().replace({
        'si':'Sì','SI':'Sì','sì':'Sì','SÌ':'Sì','SÌ':'Sì',
        'no':'No','NO':'No',
    })
    df['PAGABILE'] = df['PAGABILE'].apply(lambda x: x if x in ['Sì','No'] else '')
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

# ─── TOGGLE VISTA ─────────────────────────────────────
st.markdown("### ✏️ Modifica pratiche")
vista = st.radio("Vista", ["📱 Mobile (schede)", "🖥️ Desktop (tabella)"],
    horizontal=True, label_visibility="collapsed")
st.caption("Compila i campi vuoti. Usa il menu a tendina per Pagabile. Poi clicca Salva.")

NEGOZI_OPT = ["", "comet pontedera", "euronics corciano", "euronics gavinana", "euronics grosseto",
    "euronics montecatini", "euronics parco prato", "mw agliana", "mw collestrada",
    "mw empoli", "mw figline", "mw gigli", "mw novoli", "mw pisa",
    "mw roma est", "mw roma (porta di)", "mw roma primavera"]

OPERATORI_OPT = ["", "Adelina Meta", "Aissam El Moujaid", "Carmen Davila", "Biggbaoo",
    "David John Gallo", "Emerson Espiritu", "Emiliano Romei", "Fabian Sulmina",
    "Feris Rahmouni", "Francesco Butelli", "Giovanni Giglio", "Gloria La Giusa",
    "Katia Testa", "Mariami Iashvili", "Matteo Stefanelli", "Nicole Gamboa",
    "Samuele Guido", "Serenella Nacci", "Simona Cucu", "Simone Marra", "Yadira Davila"]

if "edited_rows" not in st.session_state:
    st.session_state["edited_rows"] = df.copy()

if vista == "📱 Mobile (schede)":
    # ── VISTA MOBILE: un expander per ogni pratica ──
    df_work = st.session_state["edited_rows"].copy()
    # Aggiungi riga vuota
    if st.button("➕ Aggiungi pratica"):
        new_row = {c: '' for c in df_work.columns}
        df_work = pd.concat([df_work, pd.DataFrame([new_row])], ignore_index=True)
        st.session_state["edited_rows"] = df_work

    for i, row in df_work.iterrows():
        neg  = row.get('NEGOZIO','') or '—'
        op   = row.get('OPERATORE','') or '—'
        data = row.get('DATA INSERIMENTO','') or '—'
        pag  = str(row.get('PAGABILE','')).strip()
        badge = '✅' if pag.upper() in ['SÌ','SI'] else ('❌' if pag.upper()=='NO' else '⏳')
        label = f"{badge} {data} · {neg} · {op}"

        with st.expander(label, expanded=(pag=='')):
            c1, c2 = st.columns(2)
            with c1:
                negozio = st.selectbox("Negozio", NEGOZI_OPT,
                    index=NEGOZI_OPT.index(row.get('NEGOZIO','')) if row.get('NEGOZIO','') in NEGOZI_OPT else 0,
                    key=f"neg_{i}")
                operatore = st.selectbox("Operatore", OPERATORI_OPT,
                    index=OPERATORI_OPT.index(row.get('OPERATORE','')) if row.get('OPERATORE','') in OPERATORI_OPT else 0,
                    key=f"op_{i}")
                tipologia = st.selectbox("Tipologia", ["","CONSUMER","BUSINESS"],
                    index=["","CONSUMER","BUSINESS"].index(row.get('TIPOLOGIA','')) if row.get('TIPOLOGIA','') in ["","CONSUMER","BUSINESS"] else 0,
                    key=f"tip_{i}")
            with c2:
                fwen = st.text_input("FWEN", value=str(row.get('FWEN','')), key=f"fwen_{i}")
                cf   = st.text_input("Cod. Fiscale", value=str(row.get('CODICE FISCALE','')), key=f"cf_{i}")
                pod  = st.text_input("POD", value=str(row.get('POD','')), key=f"pod_{i}")
            cliente = st.text_input("Nome e Cognome Cliente",
                value=str(row.get('NOME E COGNOME CLIENTE','')), key=f"cli_{i}")
            pagabile = st.selectbox("Pagabile", ["","Sì","No"],
                index=["","Sì","No"].index(pag) if pag in ["","Sì","No"] else 0,
                key=f"pag_{i}")

            # Aggiorna session state
            df_work.at[i,'NEGOZIO']   = negozio
            df_work.at[i,'OPERATORE'] = operatore
            df_work.at[i,'TIPOLOGIA'] = tipologia
            df_work.at[i,'FWEN']      = fwen
            df_work.at[i,'CODICE FISCALE'] = cf
            df_work.at[i,'POD']       = pod
            df_work.at[i,'NOME E COGNOME CLIENTE'] = cliente
            df_work.at[i,'PAGABILE']  = pagabile

    st.session_state["edited_rows"] = df_work
    edited_df = df_work

else:
    # ── VISTA DESKTOP: data_editor ──
    col_config = {
        'DATA INSERIMENTO':       st.column_config.TextColumn("Data",      disabled=True, width="small"),
        'NEGOZIO':                st.column_config.SelectboxColumn("Negozio",    options=NEGOZI_OPT[1:],    required=False, width="medium"),
        'OPERATORE':              st.column_config.SelectboxColumn("Operatore",  options=OPERATORI_OPT[1:], required=False, width="medium"),
        'TIPOLOGIA':              st.column_config.TextColumn("Tipologia",  disabled=True, width="small"),
        'FWEN':                   st.column_config.TextColumn("FWEN",                      width="medium"),
        'PARTITA IVA':            st.column_config.TextColumn("Partita IVA",               width="medium"),
        'CODICE FISCALE':         st.column_config.TextColumn("Cod. Fiscale",              width="medium"),
        'POD':                    st.column_config.TextColumn("POD",                       width="medium"),
        'NOME E COGNOME CLIENTE': st.column_config.TextColumn("Cliente",                   width="large"),
        'PAGABILE':               st.column_config.SelectboxColumn("Pagabile",
            options=["", "Sì", "No"], required=False, width="small"),
    }
    edited_df = st.data_editor(
        df,
        column_config=col_config,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        height=min(400, 50 + len(df) * 40),
    )

# ─── ANTEPRIMA COLORATA ──────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 🎨 Anteprima con colori")

def color_row(row):
    p = str(row.get('PAGABILE','')).strip().upper()
    if p in ['SÌ','SI']:
        bg = '#e8f5e9'; color = '#1b5e20'; badge = '✅ Sì'
    elif p == 'NO':
        bg = '#ffebee'; color = '#b71c1c'; badge = '❌ No'
    else:
        bg = '#fffde7'; color = '#795548'; badge = '⏳ —'
    return bg, color, badge

rows_html = ''
for _, row in edited_df.iterrows():
    bg, color, badge = color_row(row)
    rows_html += f"""<tr style="background:{bg}">
        <td style="padding:7px 10px">{row.get('DATA INSERIMENTO','')}</td>
        <td style="padding:7px 10px">{row.get('NEGOZIO','')}</td>
        <td style="padding:7px 10px">{row.get('OPERATORE','')}</td>
        <td style="padding:7px 10px">{row.get('TIPOLOGIA','')}</td>
        <td style="padding:7px 10px">{row.get('FWEN','')}</td>
        <td style="padding:7px 10px">{row.get('CODICE FISCALE','')}</td>
        <td style="padding:7px 10px">{row.get('POD','')}</td>
        <td style="padding:7px 10px">{row.get('NOME E COGNOME CLIENTE','')}</td>
        <td style="padding:7px 10px;font-weight:800;color:{color}">{badge}</td>
    </tr>"""

st.markdown(f"""
<div style="overflow-x:auto">
<table style="width:100%;border-collapse:collapse;font-size:.85rem;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
    <thead>
        <tr style="background:#1a1a1a;color:#fff">
            <th style="padding:9px 10px;text-align:left">Data</th>
            <th style="padding:9px 10px;text-align:left">Negozio</th>
            <th style="padding:9px 10px;text-align:left">Operatore</th>
            <th style="padding:9px 10px;text-align:left">Tipologia</th>
            <th style="padding:9px 10px;text-align:left">FWEN</th>
            <th style="padding:9px 10px;text-align:left">Cod. Fiscale</th>
            <th style="padding:9px 10px;text-align:left">POD</th>
            <th style="padding:9px 10px;text-align:left">Cliente</th>
            <th style="padding:9px 10px;text-align:left">Pagabile</th>
        </tr>
    </thead>
    <tbody>{rows_html}</tbody>
</table>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

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
