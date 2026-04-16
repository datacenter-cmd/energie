# ⚡ Portale Energie · BIGGBAOO v6

App Streamlit — verifica pagamenti Fastweb e controllo pratiche agenti.

## Struttura file
```
portale-biggbaoo/
├── app.py                          ← Dashboard + Login
├── utils.py                        ← Funzioni condivise
├── config.yaml                     ← Utenti e password
├── requirements.txt
├── .streamlit/
│   └── config.toml                 ← Tema sobrio Inter
└── pages/
    ├── 1_BIGGBAOO_Fastweb.py
    └── 2_BIGGBAOO_Agenti.py
```

## Credenziali di default
Password iniziale per tutti: **biggbaoo2025** — cambiare al primo accesso.

| Username       | Nome             |
|----------------|------------------|
| ignazio.gatta  | Ignazio Gatta    |
| admin1         | Amministratore 1 |
| admin2         | Amministratore 2 |
| admin3         | Amministratore 3 |
| admin4         | Amministratore 4 |

## URL personalizzato — Come ottenere biggbaoohub.streamlit.app/energie

### Opzione A — Streamlit Cloud (gratis, subdominio personalizzato)
1. Crea un account GitHub con username **biggbaoohub**
2. Crea repository chiamato **energie**
3. Deploy su Streamlit Cloud → URL risultante:
   `https://biggbaoohub-energie.streamlit.app`

### Opzione B — Dominio custom (es. energie.biggbaoo.it)
1. Deploy normale su Streamlit Cloud (ottieni un URL .streamlit.app)
2. Vai sul tuo provider DNS (Aruba, Register.it, ecc.)
3. Aggiungi un record CNAME:
   - Nome: `energie`
   - Valore: `[tuo-app].streamlit.app`
4. Su Streamlit Cloud → Settings → Custom domain → inserisci `energie.biggbaoo.it`
5. URL finale: **https://energie.biggbaoo.it**

### Opzione C — Integrazione in portal.easytlc.it (SSO futuro)
Il codice è già predisposto con il commento `SSO_INTEGRATION_POINT`.
Quando vuoi integrare, fornisci CLIENT_ID e TOKEN_URL del portale easytlc.

## Deploy su Streamlit Cloud
1. Carica tutti i file su GitHub mantenendo la struttura cartelle
2. Vai su https://share.streamlit.io → New app
3. Repository: portale-biggbaoo · Branch: main · File: app.py
4. Deploy!

## Uso locale
```
pip install -r requirements.txt
streamlit run app.py
```
