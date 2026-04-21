import pandas as pd
import json, os
from datetime import datetime

STORICO_FASTWEB = "storico_fastweb.json"
STORICO_AGENTI  = "storico_agenti.json"

# ─── UTILS ───────────────────────────────────────
def norm(v):
    if v is None or (isinstance(v, float) and pd.isna(v)): return ""
    return str(v).strip().upper()

def fmt_cur(v):
    try: return f"€ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except: return "—"

def fmt_date(v):
    if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() in ("","-","nan"): return "—"
    try: return pd.to_datetime(v).strftime("%d/%m/%Y")
    except: return str(v)

def ts_now():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

# ─── STORICO ─────────────────────────────────────
def load_storico(fname):
    if os.path.exists(fname):
        try:
            with open(fname,"r",encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

def save_storico(fname, data):
    with open(fname,"w",encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_to_storico(fname, entry, max_items=20):
    storico = load_storico(fname)
    storico = [s for s in storico if s.get("filename") != entry.get("filename")]
    storico.insert(0, entry)
    save_storico(fname, storico[:max_items])

# ─── PARSE INSERITO FASTWEB ──────────────────────
def parse_inserito(df):
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "data":          fmt_date(r.get("Data","")),
            "mese":          str(r.get("Mese","")).strip(),
            "punto_vendita": str(r.get("Nome Punto Vendita","")).strip(),
            "regione":       str(r.get("Regione Punto Vendita","")).strip(),
            "provincia":     str(r.get("Nome Provincia Punto Vendita","")).strip(),
            "codice_ordine": norm(r.get("Codice Ordine","")),
            "codice_pod":    norm(r.get("Codice POD","")),
            "account":       norm(r.get("Account","")),
            "offerta":       str(r.get("Descrizione Offerta","")).strip(),
            "stato_ordine":  str(r.get("Stato Ordine","")).strip(),
            "segmento":      str(r.get("Segmento Ordine","")).strip(),
            "data_att":      fmt_date(r.get("Data Attivazione","")),
            "nr_energy":     str(r.get("Nr Energy","")).strip(),
            "comsy":         str(r.get("Codice Comsy Tecnico","")).strip(),
        })
    return [r for r in rows if r["codice_pod"] or r["codice_ordine"]]

# ─── PARSE PAGATO FASTWEB ────────────────────────
def parse_pagato(df):
    pag_map = {}
    for _, r in df.iterrows():
        try:
            ib = float(r.get("IMPORTO COMMISSIONE",0) or 0)
            if ib != ib: ib = 0.0  # nan check
        except: ib = 0.0
        try:
            ig = float(r.get("IMPORTO GARA",0) or 0)
            if ig != ig: ig = 0.0
        except: ig = 0.0
        try:
            it = float(r.get("IMPORTO TOTALE",0) or 0)
            if it != it: it = 0.0
        except: it = 0.0
        d = {
            "importo_base": ib, "importo_gara": ig, "importo_tot": it,
            "offerta":      str(r.get("OFFERTA","")).strip(),
            "voce":         str(r.get("VOCE FATTURA","")).strip(),
            "note":         str(r.get("NOTE","")).strip(),
            "stato_contr":  str(r.get("STATO CONTRATTO","")).strip(),
            "stato_forn":   str(r.get("STATO FORNITURA","")).strip(),
            "tipo_cliente": str(r.get("TIPO CLIENTE","")).strip(),
            "dettaglio":    str(r.get("DETTAGLIO OFFERTA","")).strip(),
            "data_att":     fmt_date(r.get("DATA ATTIVAZIONE","")),
            "data_ins":     fmt_date(r.get("DATA INSERIMENTO","")),
            "competenza":   fmt_date(r.get("COMPETENZA","")),
            "pv":           str(r.get("PUNTO VENDITA","")).strip(),
            "cod_pod":      str(r.get("CODICE POD","")).strip(),
            "cod_contr":    str(r.get("CODICE CONTRATTO","")).strip(),
            "cod_cliente":  str(r.get("CODICE CLIENTE","")).strip(),
        }
        pod  = norm(r.get("CODICE POD",""))
        fwen = norm(r.get("CODICE CONTRATTO",""))
        cc   = norm(r.get("CODICE CLIENTE",""))
        if pod:  pag_map[pod]  = {**d, "_src":"POD"}
        if fwen: pag_map[fwen] = {**d, "_src":"FWEN"}
        if cc:   pag_map[cc]   = {**d, "_src":"ACC"}
    return pag_map

# ─── PARSE GESTIONALE AGENTI ─────────────────────
def parse_agenti(df):
    rows = []
    for _, r in df.iterrows():
        pda = str(r.get("PDA/DOC","")).strip()
        rows.append({
            "target":        str(r.get("Target","")).strip(),
            "punto_vendita": str(r.get("Punto Vendita","")).strip(),
            "data":          fmt_date(r.get("Data","")),
            "operatore":     str(r.get("Operatore","")).strip(),
            "pista":         str(r.get("Pista","")).strip(),
            "servizio":      str(r.get("Servizio","")).strip(),
            "stato":         str(r.get("Stato","")).strip(),
            "pda_raw":       pda,
            "pda_norm":      norm(pda),
            "cliente_pda":   norm(r.get("CLIENTE PDA","")),
            "n_tel":         str(r.get("N° Tel.","")).strip(),
            "_match_ins":    None,
            "_match_pag":    None,
            "_match_type":   None,
        })
    return [r for r in rows if r["pda_norm"] or r["pda_raw"]]

# ─── MATCH INSERITO ↔ PAGATO ─────────────────────
def match_ins_pag(rows_ins, pag_map):
    for r in rows_ins:
        m, mt = None, None
        if r["codice_pod"] and r["codice_pod"] in pag_map:
            m = pag_map[r["codice_pod"]]; mt = "POD"
        elif r["codice_ordine"] and r["codice_ordine"] in pag_map:
            m = pag_map[r["codice_ordine"]]; mt = "FWEN"
        elif r["account"] and r["account"] in pag_map:
            m = pag_map[r["account"]]; mt = "ACC"
        r["_match"] = m
        r["_match_type"] = mt
    return rows_ins

# ─── MATCH AGENTI ↔ INSERITO + PAGATO ────────────
def match_agenti(rows_ag, ins_rows, pag_map):
    # Costruisci lookup da inserito
    ins_map = {}
    for r in ins_rows:
        if r["codice_pod"]:   ins_map[r["codice_pod"]]   = r
        if r["codice_ordine"]:ins_map[r["codice_ordine"]] = r
        if r["account"]:      ins_map[r["account"]]       = r

    for r in rows_ag:
        key = r["pda_norm"]
        # match inserito
        r["_match_ins"]  = ins_map.get(key)
        # match pagato (diretto su pda o via codice_ordine dell'inserito)
        r["_match_pag"]  = pag_map.get(key)
        if not r["_match_pag"] and r["_match_ins"]:
            ins = r["_match_ins"]
            r["_match_pag"] = pag_map.get(ins["codice_pod"]) or pag_map.get(ins["codice_ordine"])
        # tipo match
        if r["_match_ins"] and r["_match_pag"]:   r["_match_type"] = "✅ Completo"
        elif r["_match_ins"] and not r["_match_pag"]: r["_match_type"] = "⚠️ Solo inserito"
        elif not r["_match_ins"] and r["_match_pag"]: r["_match_type"] = "⚠️ Solo pagato"
        else: r["_match_type"] = "❌ Non trovato"
    return rows_ag

# ─── PARSE NUOVO FORMATO AGENTI ──────────────────
def parse_pratiche(df):
    """Sheet 'pratiche' — pratiche inserite dagli agenti."""
    rows = []
    for _, r in df.iterrows():
        pda = norm(r.get("PDA/DOC",""))
        if not pda: continue
        rows.append({
            "data":          fmt_date(r.get("Data","")),
            "target":        str(r.get("Target (Mese)","")).strip(),
            "punto_vendita": str(r.get("Punto Vendita","")).strip(),
            "operatore":     str(r.get("Operatore","")).strip(),
            "servizio":      str(r.get("Servizio","")).strip(),
            "stato":         str(r.get("Stato","")).strip(),
            "pda":           pda,
            "cliente":       str(r.get("Cliente","")).strip(),
        })
    return rows

def parse_pag_fastweb(df):
    """Sheet 'pagamenti_fastweb' — quanto Fastweb ha pagato a BIGGBAOO."""
    pmap = {}
    for _, r in df.iterrows():
        try: ib = float(r.get("Importo Base €", 0) or 0)
        except: ib = 0.0
        if ib != ib: ib = 0.0
        try: ig = float(r.get("Importo Gara €", 0) or 0)
        except: ig = 0.0
        if ig != ig: ig = 0.0
        try: it = float(r.get("Importo Totale €", 0) or 0)
        except: it = it = ib + ig
        if it != it: it = ib + ig
        entry = {
            "importo_base": ib, "importo_gara": ig, "importo_tot": it,
            "offerta":       str(r.get("Offerta","")).strip(),
            "data_att":      fmt_date(r.get("Data Attivazione","")),
            "competenza":    fmt_date(r.get("Competenza","")),
            "codice_pod":    norm(r.get("Codice POD","")),
            "codice_contr":  norm(r.get("Codice Contratto","")),
        }
        for key in [norm(r.get("Codice POD","")), norm(r.get("Codice Contratto",""))]:
            if key: pmap[key] = entry
    return pmap

def parse_pag_agenti(df):
    """Sheet 'pagamenti_agenti' — quanto BIGGBAOO ha già pagato agli agenti."""
    pmap = {}
    for _, r in df.iterrows():
        pda = norm(r.get("PDA/DOC",""))
        if not pda: continue
        try: imp = float(r.get("Importo Pagato €", 0) or 0)
        except: imp = 0.0
        if imp != imp: imp = 0.0
        pmap[pda] = {
            "importo_pagato": imp,
            "pct":            str(r.get("% Raggiungimento","")).strip(),
            "data_pag":       fmt_date(r.get("Data Pagamento","")),
            "mese_fattura":   str(r.get("Mese Fattura","")).strip(),
            "operatore":      str(r.get("Operatore","")).strip(),
        }
    return pmap

def match_agenti_v2(pratiche, fw_map, ag_map):
    """Incrocia pratiche con pagamenti Fastweb e pagamenti agenti."""
    for r in pratiche:
        key = r["pda"]
        # Match con Fastweb
        r["_fw"] = fw_map.get(key)
        # Match con pagamenti agenti
        r["_ag"] = ag_map.get(key)
        # Stato incrocio
        has_fw = r["_fw"] is not None
        has_ag = r["_ag"] is not None
        if has_fw and has_ag:   r["_stato_match"] = "✅ Completo"
        elif has_fw:            r["_stato_match"] = "💶 Fastweb pagato"
        elif has_ag:            r["_stato_match"] = "👤 Solo agente"
        else:                   r["_stato_match"] = "❌ Non trovato"
    return pratiche
