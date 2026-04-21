import streamlit as st
import pandas as pd
import io
import re
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
FOLDER_NAME = "BIGGBAOO-Dati"

@st.cache_resource
def get_drive_service():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)

def get_folder_id(service):
    res = service.files().list(
        q=f"name='{FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()
    files = res.get("files", [])
    if not files:
        raise Exception(f"Cartella '{FOLDER_NAME}' non trovata su Drive. Assicurati di averla condivisa con la service account.")
    return files[0]["id"]

def list_files_in_folder(service, folder_id, prefix):
    """Lista tutti i file con un certo prefisso nella cartella."""
    res = service.files().list(
        q=f"'{folder_id}' in parents and name contains '{prefix}' and trashed=false",
        fields="files(id, name)",
        orderBy="name desc"
    ).execute()
    return res.get("files", [])

def download_file(service, file_id):
    """Scarica un file da Drive e ritorna un BytesIO."""
    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)
    return buf

def get_latest_file(prefix):
    """Ritorna (nome_file, BytesIO) del file più recente con quel prefisso."""
    try:
        service = get_drive_service()
        folder_id = get_folder_id(service)
        files = list_files_in_folder(service, folder_id, prefix)
        if not files:
            return None, None
        # Il primo è il più recente (orderBy name desc: fastweb_2026_04 > fastweb_2026_03)
        latest = files[0]
        buf = download_file(service, latest["id"])
        return latest["name"], buf
    except Exception as e:
        st.error(f"❌ Errore connessione Drive: {e}")
        return None, None

def get_all_files(prefix):
    """Ritorna lista di (nome_file, file_id) con quel prefisso — per selezione manuale."""
    try:
        service = get_drive_service()
        folder_id = get_folder_id(service)
        files = list_files_in_folder(service, folder_id, prefix)
        return [(f["name"], f["id"]) for f in files]
    except Exception as e:
        st.error(f"❌ Errore connessione Drive: {e}")
        return []

def download_by_id(file_id):
    service = get_drive_service()
    return download_file(service, file_id)
