"""
airtable_store.py — Airtable persistence for Ask Lionel
Handles: config (incl. bilingual profile), experiences, case studies, recommendations
"""

import os, json, requests
import streamlit as st

BASE_ID = "appf02tzrzmTIHBza"
CONFIG_TABLE = "tblGMmMaP8Z00HkLE"
RECOS_TABLE = "tblayphpRLIXktphw"
API_URL = "https://api.airtable.com/v0"

def get_token():
    try: return st.secrets["AIRTABLE_TOKEN"]
    except: return os.getenv("AIRTABLE_TOKEN", "")

def headers():
    return {"Authorization": f"Bearer {get_token()}", "Content-Type": "application/json"}

def load_config():
    url = f"{API_URL}/{BASE_ID}/{CONFIG_TABLE}"
    try:
        resp = requests.get(url, headers=headers(), params={"pageSize": 100}, timeout=10)
        resp.raise_for_status(); data = resp.json()
    except Exception as e:
        print(f"[airtable] load_config error: {e}"); return {}

    config = {}; record_ids = {}
    for rec in data.get("records", []):
        fields = rec.get("fields", {})
        key = fields.get("Name", "").strip(); val = fields.get("Notes", "")
        if key: config[key] = val; record_ids[key] = rec["id"]

    for i in range(1, 5):
        mk = f"metric{i}"
        if mk in config:
            parts = config[mk].split("|")
            if len(parts) == 3:
                config[f"{mk}_label"] = parts[0]; config[f"{mk}_value"] = parts[1]; config[f"{mk}_desc"] = parts[2]

    for jk in ["exp", "case_studies"]:
        if jk in config:
            try: config[jk] = json.loads(config[jk])
            except: config[jk] = []

    for bk in ["show_tjm", "show_phone", "show_profil", "show_metrics", "show_case_studies", "show_parcours", "show_recos"]:
        if bk in config: config[bk] = str(config[bk]).lower() == "true"

    config["_record_ids"] = record_ids
    return config

def save_config(config):
    record_ids = config.get("_record_ids", {}); kv = {}
    for k in ["tjm","disponibilite","remote","linkedin","email","phone","calendly",
              "profil_p1","profil_p2","profil_p3","profil_p4",
              "profil_p1_en","profil_p2_en","profil_p3_en","profil_p4_en",
              "hero_name","hero_title","hero_tagline_fr","hero_tagline_en","hero_badges"]:
        if k in config: kv[k] = str(config[k])
    for bk in ["show_tjm","show_phone","show_profil","show_metrics","show_case_studies","show_parcours","show_recos"]:
        if bk in config: kv[bk] = "true" if config[bk] else "false"
    for i in range(1, 5):
        mk = f"metric{i}"
        kv[mk] = f"{config.get(f'{mk}_label','')}|{config.get(f'{mk}_value','')}|{config.get(f'{mk}_desc','')}"
    for jk in ["exp", "case_studies"]:
        if jk in config: kv[jk] = json.dumps(config[jk], ensure_ascii=False)

    url = f"{API_URL}/{BASE_ID}/{CONFIG_TABLE}"
    updates = []; creates = []
    for key, val in kv.items():
        if key in record_ids: updates.append({"id": record_ids[key], "fields": {"Name": key, "Notes": val}})
        else: creates.append({"fields": {"Name": key, "Notes": val}})
    for i in range(0, len(updates), 10):
        try: requests.patch(url, headers=headers(), json={"records": updates[i:i+10]}, timeout=10)
        except Exception as e: print(f"[airtable] update error: {e}")
    for i in range(0, len(creates), 10):
        try: requests.post(url, headers=headers(), json={"records": creates[i:i+10]}, timeout=10)
        except Exception as e: print(f"[airtable] create error: {e}")

def load_recos():
    url = f"{API_URL}/{BASE_ID}/{RECOS_TABLE}"
    try:
        resp = requests.get(url, headers=headers(), params={"pageSize": 100}, timeout=10)
        resp.raise_for_status(); data = resp.json()
    except Exception as e:
        print(f"[airtable] load_recos error: {e}"); return []
    return [{"id":rec["id"],"name":rec.get("fields",{}).get("name",""),"title":rec.get("fields",{}).get("title",""),"company":rec.get("fields",{}).get("company",""),"relation":rec.get("fields",{}).get("relation",""),"text":rec.get("fields",{}).get("text",""),"approved":rec.get("fields",{}).get("approved",False),"date":rec.get("fields",{}).get("date",""),"linkedin":rec.get("fields",{}).get("linkedin",""),"collab_period":rec.get("fields",{}).get("collab_period","")} for rec in data.get("records",[])]

def add_reco(reco):
    url = f"{API_URL}/{BASE_ID}/{RECOS_TABLE}"
    try: requests.post(url, headers=headers(), json={"records": [{"fields":{"name":reco.get("name",""),"title":reco.get("title",""),"company":reco.get("company",""),"relation":reco.get("relation",""),"text":reco.get("text",""),"approved":False,"date":reco.get("date",""),"linkedin":reco.get("linkedin",""),"collab_period":reco.get("collab_period","")}}]}, timeout=10)
    except Exception as e: print(f"[airtable] add_reco error: {e}")

def update_all_recos(recos):
    url = f"{API_URL}/{BASE_ID}/{RECOS_TABLE}"
    records = [{"id":r["id"],"fields":{"name":r.get("name",""),"title":r.get("title",""),"company":r.get("company",""),"relation":r.get("relation",""),"text":r.get("text",""),"approved":r.get("approved",False),"date":r.get("date",""),"linkedin":r.get("linkedin",""),"collab_period":r.get("collab_period","")}} for r in recos if r.get("id")]
    for i in range(0, len(records), 10):
        try: requests.patch(url, headers=headers(), json={"records": records[i:i+10]}, timeout=10)
        except Exception as e: print(f"[airtable] update_recos error: {e}")
