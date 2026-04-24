import streamlit as st
import hashlib
import yaml
import os
from yaml.loader import SafeLoader

_SALT = "biggbaoo_salt_2025"

def _hash(pw: str) -> str:
    return hashlib.sha256(f"{_SALT}{pw}".encode()).hexdigest()

def load_users():
    cfg_path = "config.yaml"
    if not os.path.exists(cfg_path):
        return {}
    with open(cfg_path, encoding="utf-8") as f:
        config = yaml.load(f, SafeLoader)
    return config.get("users", {})

def login_form():
    """Mostra form di login. Ritorna True se autenticato."""
    if st.session_state.get("logged_in"):
        return True

    st.markdown("""
    <div style="text-align:center; padding:2.5rem 0 1rem;">
      <div style="font-size:2.5rem;">⚡</div>
      <div style="font-size:1.5rem; font-weight:700; margin:.4rem 0; color:#1a1a1a;">Portale Energie · BIGGBAOO</div>
      <div style="color:#6b6b6b; font-size:.9rem;">Verifica pagamenti Fastweb · Controllo pratiche agenti</div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 1.2, 1])[1]
    with col:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="es. ignazio.gatta")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("🔐 Accedi", use_container_width=True)

        if submitted:
            users = load_users()
            user = users.get(username)
            if user and user["password"] == _hash(password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["name"] = user["name"]
                st.session_state["role"] = user.get("role", "admin")
                st.rerun()
            else:
                st.error("❌ Username o password errati.")
    return False

def logout():
    for k in ["logged_in", "username", "name"]:
        st.session_state.pop(k, None)
    st.rerun()

def require_login():
    """Per le pagine secondarie: blocca se non loggato."""
    if not st.session_state.get("logged_in"):
        st.warning("🔒 Accedi dalla pagina principale per usare questa sezione.")
        st.stop()
    return st.session_state.get("name"), st.session_state.get("username")

def get_role():
    return st.session_state.get("role", "admin")

def require_admin():
    """Blocca l'accesso se l'utente non è admin."""
    require_login()
    if st.session_state.get("role") != "admin":
        st.error("🔒 Accesso riservato agli amministratori.")
        st.stop()
    return st.session_state.get("name"), st.session_state.get("username")

def require_vis_energy():
    """Blocca se non loggato o non ha ruolo vis_energy o admin."""
    require_login()
    role = st.session_state.get("role", "")
    if role not in ("admin", "vis_energy"):
        st.error("🔒 Accesso riservato agli operatori VIS Energia.")
        st.stop()
    return st.session_state.get("name"), st.session_state.get("username")

def require_vis_business():
    """Blocca se non loggato o non ha ruolo vis_business o admin."""
    require_login()
    role = st.session_state.get("role", "")
    if role not in ("admin", "vis_business"):
        st.error("🔒 Accesso riservato agli operatori VIS Business.")
        st.stop()
    return st.session_state.get("name"), st.session_state.get("username")
