> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

---
name: Rate Limit Strategy Free Tier — Pivot 2026-04-26
description: Analisa pilihan strategi rate limit untuk SIDIX free tier — daily counter (current), rolling 24h window, hourly throttle, token bucket, time-based session. Trade-off + rekomendasi implementasi.
type: project
---

# Rate Limit Strategy untuk Free Tier SIDIX

**Tanggal**: 2026-04-26
**Konteks**: User minta limit free tier yang lebih enak. Saat ini pakai daily counter (reset midnight UTC), user feedback: hit 0 lalu tunggu 24h frustrating.

## Strategy Comparison

### Strategy 1: Daily counter (CURRENT)

```
guest:     5/hari
free:      30/hari
sponsored: 200/hari
whitelist: unlimited
```

**Pros**: simple, predictable, easy to communicate ("5 pesan/hari")
**Cons**:
- User hit 0 lalu tunggu sampai 00:00 UTC = 7 AM WIB. Frustrating.
- "Midnight reset gaming" — user simpan request untuk tunggu reset
- Tidak fair: orang yang chat 3 sekaligus jam 23:00 langsung dapat reset 1 jam kemudian

### Strategy 2: Rolling 24h window

```
guest:     5 dalam 24 jam terakhir
free:      30 dalam 24 jam terakhir
```

**Pros**:
- Lebih fair — kalau chat banyak jam 14:00, baru bisa lagi besok jam 14:00
- No "midnight reset gaming"
- Token-bucket-like behavior — natural backoff

**Cons**:
- Lebih sulit di-explain ("kapan reset-nya?")
- Storage lebih kompleks: butuh timestamp per request, bukan counter
- Calculation per-request lebih heavy (filter timestamps)

**Estimasi storage**: 1 user × 30 timestamps × 8 bytes = 240 bytes/user. 10k user = 2.4 MB. Acceptable.

### Strategy 3: Hourly throttle

```
guest:     2/hour, max 10/hari
free:      5/hour, max 50/hari
```

**Pros**:
- User selalu bisa kembali tiap jam → reduces frustration
- Total daily budget tetap controlled

**Cons**:
- Power user (chatting deep dive) frustrated by hourly cap
- 2 layer cap (hour + day) lebih confusing

### Strategy 4: Token bucket

```
Setiap user punya 10 tokens.
Refill 1 token tiap 1 jam.
Casual question = 1 token.
Burst/Foresight (multi-step) = 3 tokens.
```

**Pros**:
- Fair: query mahal cost lebih
- Burst tokens bisa "save up" — user fleksibel
- Industri standard (AWS, Stripe, dll)

**Cons**:
- Complex untuk user understand ("token apa?")
- Perlu UI khusus untuk show token balance
- Lebih banyak code

### Strategy 5: Time-based session

```
30 menit unlimited chat per hari → 4 jam cooldown → 30 menit lagi
```

**Pros**:
- Encourage focused use, bukan one-off questions
- Power user dapat deep-dive 30 menit

**Cons**:
- Bingung ("kok limited per waktu?")
- Cooldown frustrating
- Gaming-able (open at 23:30, 30 min, then reset midnight, another 30 min)

---

## Rekomendasi Eksekusi

### Phase 1 (NOW — Pivot 2026-04-26): Strategy 1 dengan limits naik
Sudah implemented:
- guest 3 → 5
- free 10 → 30
- sponsored 100 → 200
- whitelist unlimited (NEW tier)

### Phase 2 (Next sprint, kalau user feedback masih frustrating):
Implementasi **Strategy 2 (rolling 24h)** sebagai opt-in:
- Env var: `SIDIX_QUOTA_STRATEGY=rolling_24h | daily | token_bucket`
- Default: daily (backward compat)
- Storage migration script: convert daily counters → timestamp arrays

### Phase 3 (Lanjutan, kalau ada paid tier):
Hybrid: free tier rolling 24h, paid tier daily counter besar (1000+).

---

## Implementation Sketch (Strategy 2 Rolling 24h)

```python
# token_quota.py (future)
def check_quota_rolling(user_id, ip, email, window_hours=24):
    key = _user_key(user_id, ip)
    data = _load_rolling()
    timestamps = data.get(key, [])
    now = time.time()
    cutoff = now - window_hours * 3600
    # Filter timestamps within window
    timestamps = [t for t in timestamps if t >= cutoff]
    tier = _get_tier(user_id, email)
    limit = QUOTA_LIMITS[tier]
    if len(timestamps) >= limit:
        # Calculate when oldest timestamp falls outside window
        next_available = datetime.fromtimestamp(timestamps[0] + window_hours * 3600)
        return {
            "ok": False,
            "tier": tier,
            "used": len(timestamps),
            "limit": limit,
            "next_available_at": next_available.isoformat(),
            "message": f"Limit tercapai. Bisa chat lagi pada {next_available.strftime('%H:%M')}."
        }
    return {"ok": True, ...}

def record_usage_rolling(user_id, ip, email):
    key = _user_key(user_id, ip)
    data = _load_rolling()
    timestamps = data.get(key, [])
    timestamps.append(time.time())
    # Prune old to limit storage
    cutoff = time.time() - 24 * 3600
    data[key] = [t for t in timestamps if t >= cutoff]
    _save_rolling(data)
```

Storage file: `.data/rolling_quota.json` (atomic save dengan lock).

---

## Refs

- AWS Token Bucket: https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
- Stripe rate limiting: https://stripe.com/blog/rate-limiters
- ChatGPT free tier: ~50 GPT-4o/day (was 25), 80 GPT-4o-mini/3hr (rolling)
- Claude.ai free: ~30-40 turns/day rolling 24h
- Perplexity free: 5 Pro searches/day (daily counter)

## Decision Status

- **Phase 1**: ✅ DONE (limits naik + whitelist tier)
- **Phase 2**: ⏳ DEFER — observe Phase 1 user feedback for 1-2 weeks. Implement kalau ada laporan frustrating midnight reset.
- **Phase 3**: ⏳ TBD — ketika introducing paid tier
