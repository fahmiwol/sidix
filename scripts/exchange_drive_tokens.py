#!/usr/bin/env python3
"""
exchange_drive_tokens.py — Exchange Google OAuth2 auth code → refresh_token
=============================================================================
Usage:
  python scripts/exchange_drive_tokens.py \
    --code "4/0AeoWuM..." \
    --client-id "YOUR_CLIENT_ID" \
    --client-secret "YOUR_CLIENT_SECRET" \
    --redirect-uri "https://developers.google.com/oauthplayground"

Output:
  JSON dengan access_token, refresh_token, expires_in

Catatan:
  - refresh_token tidak expired (kecuali user revoke)
  - Simpan refresh_token ke .env
  - access_token expired ~1 jam, auto-refresh oleh collector
"""
from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request

OAUTH2_TOKEN_URL = "https://oauth2.googleapis.com/token"


def exchange_code(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str = "http://localhost:8080",
) -> dict:
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    body = urllib.parse.urlencode(data).encode("utf-8")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    req = urllib.request.Request(
        OAUTH2_TOKEN_URL, method="POST", headers=headers, data=body
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Exchange Google OAuth2 code for tokens")
    parser.add_argument("--code", required=True, help="Authorization code from Google")
    parser.add_argument("--client-id", required=True, help="OAuth2 Client ID")
    parser.add_argument("--client-secret", required=True, help="OAuth2 Client Secret")
    parser.add_argument(
        "--redirect-uri",
        default="https://developers.google.com/oauthplayground",
        help="Redirect URI used in auth flow (default: Playground)",
    )
    parser.add_argument("--account", default="", help="Account label (e.g. fahmiwol)")
    args = parser.parse_args()

    print(f"🔑 Exchanging code for account: {args.account or 'default'}")
    print(f"   Redirect URI: {args.redirect_uri}")

    try:
        result = exchange_code(
            args.code, args.client_id, args.client_secret, args.redirect_uri
        )

        if "error" in result:
            print(f"\n❌ ERROR: {result['error']}")
            print(f"   Description: {result.get('error_description', 'N/A')}")
            return 1

        print("\n✅ SUCCESS! Tokens received:\n")
        print(json.dumps(result, indent=2))

        # Print env var format
        acc = f"_{args.account.upper()}" if args.account else ""
        print(f"\n# ── Copy ke .env ──")
        print(f"GOOGLE_DRIVE_ACCESS_TOKEN{acc}={result.get('access_token', '')}")
        print(f"GOOGLE_DRIVE_REFRESH_TOKEN{acc}={result.get('refresh_token', '')}")

        return 0

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
