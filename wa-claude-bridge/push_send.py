#!/usr/bin/env python3
"""push_send.py — kirim FCM push ke semua device terdaftar (FCM HTTP v1, service-account).
Usage: push_send.py "Judul" "Isi pesan"
Token device disimpan oleh /v1/push/register di state/push_tokens.json.
Service-account: /opt/wa-claude-bridge/fcm-service-account.json (RAHASIA)."""
import sys, os, json
import google.auth.transport.requests
from google.oauth2 import service_account
import requests

DIR = os.path.dirname(os.path.abspath(__file__))
SA = os.path.join(DIR, "fcm-service-account.json")
TOKENS = os.path.join(DIR, "state", "push_tokens.json")
SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]

def _auth():
    cred = service_account.Credentials.from_service_account_file(SA, scopes=SCOPES)
    cred.refresh(google.auth.transport.requests.Request())
    project = json.load(open(SA))["project_id"]
    return cred.token, project

def send(title, body):
    if not os.path.exists(TOKENS):
        print("[push] tak ada token terdaftar"); return 0
    toks = json.load(open(TOKENS))
    if not toks:
        print("[push] tak ada token"); return 0
    tok, project = _auth()
    url = f"https://fcm.googleapis.com/v1/projects/{project}/messages:send"
    H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    ok, dead = 0, []
    for t in toks:
        msg = {"message": {
            "token": t,
            "notification": {"title": title, "body": body},
            "android": {"priority": "high"},
        }}
        r = requests.post(url, headers=H, json=msg, timeout=15)
        if r.status_code == 200:
            ok += 1
        elif r.status_code in (400, 403, 404):
            dead.append(t); print(f"[push] token mati ({r.status_code})")
        else:
            print(f"[push] err {r.status_code}: {r.text[:140]}")
    if dead:
        live = [t for t in toks if t not in dead]
        json.dump(live, open(TOKENS, "w"))
    print(f"[push] terkirim {ok}/{len(toks)}; buang {len(dead)} token mati")
    return ok

if __name__ == "__main__":
    title = sys.argv[1] if len(sys.argv) > 1 else "Anonymouse Trade"
    body = sys.argv[2] if len(sys.argv) > 2 else ""
    send(title, body)
