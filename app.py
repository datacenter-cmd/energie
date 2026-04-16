import streamlit as st
import pandas as pd
import yaml
import os
from yaml.loader import SafeLoader

st.set_page_config(
    page_title="Portale Energie · BIGGBAOO",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], .stMarkdown, .stText, button, input, select, textarea {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* KPI boxes */
.kpi-box {
    background: #ffffff;
    border-radius: 8px;
    padding: .9rem 1.1rem;
    border: 1px solid #e0e0e0;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    text-align: center;
    margin-bottom: .5rem;
}
.kpi-label { font-size:.72rem; color:#6b6b6b; text-transform:uppercase; letter-spacing:.07em; font-weight:600; }
.kpi-value { font-size:1.8rem; font-weight:700; line-height:1.1; margin:.25rem 0; color:#1a1a1a; }
.kpi-sub   { font-size:.72rem; color:#6b6b6b; }

/* Colori semantici neutri */
.ok   { color:#2a7a2a; }
.err  { color:#b02020; }
.gold { color:#7a5c00; }
.pri  { color:#2d2d2d; }
.muted { color:#6b6b6b; }

/* Info/Warn boxes */
.info-box {
    background:#ffffff; border:1px solid #d8d8d8; border-left:3px solid #2d2d2d;
    border-radius:6px; padding:.75rem 1rem; font-size:.875rem; margin-bottom:.75rem;
}
.warn-box {
    background:#fff8f0; border:1px solid #e8d0b0; border-left:3px solid #b05a00;
    border-radius:6px; padding:.75rem 1rem; font-size:.875rem; margin-bottom:.75rem;
}
.err-box {
    background:#fff5f5; border:1px solid #e8b0b0; border-left:3px solid #b02020;
    border-radius:6px; padding:.75rem 1rem; font-size:.875rem; margin-bottom:.75rem;
}

/* Section titles */
.section-title {
    font-size:1rem; font-weight:600; color:#1a1a1a; margin-bottom:.6rem;
    display:flex; align-items:center; gap:.4rem;
    border-bottom:1px solid #e0e0e0; padding-bottom:.4rem;
}

/* Sidebar */
div[data-testid="stSidebarContent"] { background:#ebebeb !important; }

/* Storico items */
.storico-item {
    background:#ffffff; border:1px solid #e0e0e0; border-radius:6px;
    padding:.5rem .9rem; font-size:.8rem; margin-bottom:.4rem;
}

/* Badge match */
.badge-pod  { background:#e8f0e8; color:#2a7a2a; padding:2px 8px; border-radius:4px; font-size:.72rem; font-weight:600; }
.badge-fwen { background:#e8eaf8; color:#2a40a0; padding:2px 8px; border-radius:4px; font-size:.72rem; font-weight:600; }
.badge-acc  { background:#f5f0e0; color:#7a5c00; padding:2px 8px; border-radius:4px; font-size:.72rem; font-weight:600; }
.badge-no   { background:#f0f0f0; color:#6b6b6b; padding:2px 8px; border-radius:4px; font-size:.72rem; font-weight:600; }

/* Login box */
.login-header {
    text-align:center; padding:2.5rem 0 1rem;
}
.login-header .logo { font-size:2.5rem; }
.login-header .title { font-size:1.5rem; font-weight:700; margin:.4rem 0; color:#1a1a1a; }
.login-header .sub { color:#6b6b6b; font-size:.9rem; }

/* SSO ready: data attribute per integrazione futura */
[data-sso-provider="easytlc"] { display:none; }
</style>
""", unsafe_allow_html=True)

# ─── LOGIN ───────────────────────────────────────
try:
    import streamlit_authenticator as stauth
    CONFIG_FILE = "config.yaml"
    if not os.path.exists(CONFIG_FILE):
        st.error("❌ File config.yaml non trovato. Contatta l'amministratore.")
        st.stop()
    with open(CONFIG_FILE, encoding="utf-8") as f:
        config = yaml.load(f, Loader=SafeLoader)
    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )
    name, auth_status, username = authenticator.login("Accedi al Portale", "main")
except Exception as ex:
    st.error(f"Errore di autenticazione: {ex}")
    st.stop()


if auth_status is False:
    st.error("❌ Username o password errati.")
    st.stop()
if auth_status is None:
    st.markdown("""
    <div class="login-header">
      <div class="logo">⚡</div>
      <div class="title">Portale Energie · BIGGBAOO</div>
      <div class="sub">Verifica pagamenti Fastweb · Controllo pratiche agenti</div>
      <div style="margin-top:.5rem;font-size:.75rem;color:#b0b0b0;" data-sso-provider="easytlc">
        <!-- SSO_INTEGRATION_POINT: sostituire login con OAuth2 easytlc -->
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ─── SIDEBAR ─────────────────────────────────────
with st.sidebar:
    st.markdown(f"### ⚡ Portale Energie")
    st.markdown(f"**BIGGBAOO**")
    st.markdown(f"👤 Benvenuto, **{name}**")
    st.divider()
    st.markdown("**Navigazione:**")
    st.markdown("- 🏠 Dashboard ← sei qui")
    st.markdown("- 📋 BIGGBAOO ↔ Fastweb")
    st.markdown("- 👥 BIGGBAOO ↔ Agenti")
    st.divider()
    authenticator.logout("🚪 Esci", "sidebar")
    st.divider()
    st.caption("v6 · Portale Energie BIGGBAOO")

# ─── DASHBOARD ───────────────────────────────────
st.markdown("# ⚡ Portale Energie · BIGGBAOO")
st.markdown("Verifica pagamenti Fastweb · Controllo pratiche agenti")
st.divider()

# Carica storico da entrambe le sezioni
from utils import load_storico, STORICO_FASTWEB, STORICO_AGENTI

sto_fw  = load_storico(STORICO_FASTWEB)
sto_ag  = load_storico(STORICO_AGENTI)

# ─── KPI GLOBALI ─────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

tot_fw_prat  = sum(s.get("totale",0) for s in sto_fw)
tot_fw_pag   = sum(s.get("pagate",0) for s in sto_fw)
tot_ag_prat  = sum(s.get("totale",0) for s in sto_ag)
tot_ag_compl = sum(s.get("complete",0) for s in sto_ag)
tot_fw_amt   = sum(s.get("importo_tot",0) for s in sto_fw)

with c1:
    st.markdown(f'''<div class="kpi-box">
      <div class="kpi-label">📋 Pratiche Fastweb</div>
      <div class="kpi-value pri">{tot_fw_prat}</div>
      <div class="kpi-sub">totale storico caricato</div>
    </div>''', unsafe_allow_html=True)
with c2:
    pct = round(tot_fw_pag/tot_fw_prat*100) if tot_fw_prat else 0
    st.markdown(f'''<div class="kpi-box">
      <div class="kpi-label">✅ Pagate Fastweb</div>
      <div class="kpi-value ok">{tot_fw_pag}</div>
      <div class="kpi-sub">{pct}% del totale</div>
    </div>''', unsafe_allow_html=True)
with c3:
    st.markdown(f'''<div class="kpi-box">
      <div class="kpi-label">👥 Pratiche Agenti</div>
      <div class="kpi-value pri">{tot_ag_prat}</div>
      <div class="kpi-sub">totale storico caricato</div>
    </div>''', unsafe_allow_html=True)
with c4:
    pct2 = round(tot_ag_compl/tot_ag_prat*100) if tot_ag_prat else 0
    st.markdown(f'''<div class="kpi-box">
      <div class="kpi-label">✅ Complete (ins+pag)</div>
      <div class="kpi-value ok">{tot_ag_compl}</div>
      <div class="kpi-sub">{pct2}% del totale</div>
    </div>''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── STORICO FASTWEB ─────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-title">📋 Ultimi caricamenti · BIGGBAOO ↔ Fastweb</div>', unsafe_allow_html=True)
    if sto_fw:
        for s in sto_fw[:5]:
            non_pag = s.get("totale",0) - s.get("pagate",0)
            col_icon = "ok" if non_pag == 0 else ("err" if non_pag > 5 else "gold")
            st.markdown(f'''<div class="info-box">
              📄 <strong>{s.get("filename","—")}</strong><br>
              🕐 {s.get("ts","—")} &nbsp;|&nbsp;
              📊 {s.get("totale",0)} pratiche &nbsp;|&nbsp;
              ✅ <span class="{col_icon}">{s.get("pagate",0)} pagate</span> &nbsp;|&nbsp;
              ❌ {non_pag} non pagate
            </div>''', unsafe_allow_html=True)
    else:
        st.caption("Nessun caricamento ancora. Vai alla sezione BIGGBAOO ↔ Fastweb.")

with col2:
    st.markdown('<div class="section-title">👥 Ultimi caricamenti · BIGGBAOO ↔ Agenti</div>', unsafe_allow_html=True)
    if sto_ag:
        for s in sto_ag[:5]:
            non_compl = s.get("totale",0) - s.get("complete",0)
            col_icon = "ok" if non_compl == 0 else ("err" if non_compl > 5 else "gold")
            st.markdown(f'''<div class="info-box">
              📄 <strong>{s.get("filename","—")}</strong><br>
              🕐 {s.get("ts","—")} &nbsp;|&nbsp;
              📊 {s.get("totale",0)} pratiche &nbsp;|&nbsp;
              ✅ <span class="{col_icon}">{s.get("complete",0)} complete</span> &nbsp;|&nbsp;
              ❌ {non_compl} incomplete
            </div>''', unsafe_allow_html=True)
    else:
        st.caption("Nessun caricamento ancora. Vai alla sezione BIGGBAOO ↔ Agenti.")

st.divider()

# ─── GUIDA RAPIDA ────────────────────────────────
st.markdown("### 📖 Come usare il portale")
g1, g2 = st.columns(2)
with g1:
    st.markdown("""
    **📋 BIGGBAOO ↔ Fastweb**
    - Carica il file Excel mensile Fastweb
    - Fogli richiesti: `inserito` + `pagato nuovo format`
    - Controlla quali pratiche sono state pagate
    - Filtra per punto vendita, mese, stato
    - Esporta il risultato in CSV
    """)
with g2:
    st.markdown("""
    **👥 BIGGBAOO ↔ Agenti**
    - Carica il file gestionale agenti (exportgridData)
    - Carica il file pagato Fastweb
    - Verifica quali pratiche degli agenti risultano pagate
    - Individua le pratiche da pagare agli agenti
    - Esporta la lista pagamenti agenti in CSV
    """)
