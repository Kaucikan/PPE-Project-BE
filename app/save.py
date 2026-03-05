import requests

SUPABASE_URL = "https://cxeiiuceqamnnircdpuf.supabase.co"
SUPABASE_KEY = "sb_publishable_9hdhDdABEY89pperW7W-HA_ZFZuiviX"


def save_violation(label, confidence):
    url = f"{SUPABASE_URL}/rest/v1/violations"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    data = {
        "violation_type": label,
        "confidence": confidence
    }

    requests.post(url, json=data, headers=headers)