#!/usr/bin/env python3
import json, urllib.request
from urllib.error import HTTPError
b = json.dumps({"business_name": "QA", "niche": "Test", "target_audience": "Dev", "budget": "1jt"}).encode()
req = urllib.request.Request("http://127.0.0.1:8765/creative/agency_kit", data=b, method="POST")
req.add_header("Content-Type", "application/json")
try:
    r = urllib.request.urlopen(req, timeout=15)
    print("OK", r.status, json.loads(r.read().decode()))
except HTTPError as e:
    body = e.read().decode()
    print("ERR HTTP", e.code, body)
except Exception as e:
    print("ERR", type(e).__name__, e)
