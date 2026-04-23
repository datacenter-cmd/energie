import streamlit as st
import base64, os
from auth import require_login

st.set_page_config(page_title="Gara Energy", page_icon="⚡", layout="wide")
name, username = require_login()

st.markdown("# ⚡ Gara Fastweb Energia")
st.markdown("Lettera di remunerazione · Aprile 2026")
st.divider()

# Riepilogo rapido dalla lettera
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
<div style="background:#fff;border:1px solid #e0e0e0;border-radius:12px;padding:24px;box-shadow:0 1px 4px rgba(0,0,0,.07)">
    <div style="font-size:.75rem;font-weight:800;color:#1a1a1a;text-transform:uppercase;letter-spacing:.04em;margin-bottom:12px">🏠 B2C — Residential</div>
    <table style="width:100%;border-collapse:collapse;font-size:.9rem">
        <tr style="background:#f5f5f5">
            <th style="padding:8px;text-align:left;border-radius:4px">Soglia</th>
            <th style="padding:8px;text-align:left">Target Energy</th>
            <th style="padding:8px;text-align:left">Compenso M+1</th>
        </tr>
        <tr>
            <td style="padding:8px;color:#888">Base</td>
            <td style="padding:8px">—</td>
            <td style="padding:8px;font-weight:700">€ 70</td>
        </tr>
        <tr style="background:#f9f9f9">
            <td style="padding:8px;font-weight:700">1</td>
            <td style="padding:8px">≥ 1</td>
            <td style="padding:8px;font-weight:800;color:#1e7e4a;font-size:1.1rem">€ 140</td>
        </tr>
    </table>
</div>
""", unsafe_allow_html=True)

with col2:
    st.markdown("""
<div style="background:#fff;border:1px solid #e0e0e0;border-radius:12px;padding:24px;box-shadow:0 1px 4px rgba(0,0,0,.07)">
    <div style="font-size:.75rem;font-weight:800;color:#1a1a1a;text-transform:uppercase;letter-spacing:.04em;margin-bottom:12px">🏢 B2B — Soho Professional</div>
    <table style="width:100%;border-collapse:collapse;font-size:.9rem">
        <tr style="background:#f5f5f5">
            <th style="padding:8px;text-align:left;border-radius:4px">Soglia</th>
            <th style="padding:8px;text-align:left">Target Energy</th>
            <th style="padding:8px;text-align:left">Compenso M+1</th>
        </tr>
        <tr>
            <td style="padding:8px;color:#888">Base</td>
            <td style="padding:8px">—</td>
            <td style="padding:8px;font-weight:700">€ 80</td>
        </tr>
        <tr style="background:#f9f9f9">
            <td style="padding:8px;font-weight:700">1</td>
            <td style="padding:8px">≥ 1</td>
            <td style="padding:8px;font-weight:800;color:#1a7abf;font-size:1.1rem">€ 200</td>
        </tr>
    </table>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Note chiave dalla lettera
st.markdown("""
<div style="background:#fffbea;border:1px solid #f0d060;border-radius:12px;padding:20px 24px;font-size:.9rem;line-height:1.7">
    <div style="font-weight:800;margin-bottom:8px">📋 Regole di Gara</div>
    <ul style="margin:0;padding-left:18px">
        <li>Periodo di Gara: <strong>01 aprile 2026 → 30 aprile 2026</strong></li>
        <li>Valide tutte le PDA Energy <strong>Residential</strong> e <strong>Soho Professional</strong> (escluse offerte Fastweb Luce Placet)</li>
        <li>Le PDA devono essere in stato <strong>Attivato</strong> l'ultimo giorno del mese successivo a quello d'inserimento (M+1)</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# Visualizzatore PDF inline
st.markdown("### 📄 Lettera originale Fastweb")

pdf_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'gara_energy_aprile_2026.pdf')
try:
    with open(pdf_path, 'rb') as f:
        pdf_b64 = base64.b64encode(f.read()).decode()
    st.markdown(
        f'''<iframe src="data:application/pdf;base64,{pdf_b64}"
            width="100%" height="800px"
            style="border:1px solid #e0e0e0;border-radius:8px">
        </iframe>''',
        unsafe_allow_html=True
    )
    # Pulsante download
    st.download_button(
        "⬇️ Scarica PDF",
        data=open(pdf_path,'rb').read(),
        file_name="Gara_Fastweb_Energy_Aprile_2026.pdf",
        mime="application/pdf"
    )
except Exception as e:
    st.error(f"PDF non trovato: {e}")
