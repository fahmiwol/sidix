"""
builtin_apps.py — SIDIX Built-in Applications Registry

Mendaftarkan semua kapabilitas built-in SIDIX sebagai tool yang bisa dipanggil
oleh agent, user, atau modul lain tanpa API eksternal.

Kategori:
  - math       : kalkulator, statistik, konverter satuan
  - datetime   : waktu, tanggal, hijriah
  - text       : format, encode, hash
  - web        : stub pencarian, Wikipedia lookup
  - data       : JSON/YAML formatter, CSV parser
  - islamic    : waktu shalat, kalkulator zakat, arah kiblat
  - utility    : generator password, UUID, QR stub

Cara gunakan:
    from brain_qa.builtin_apps import list_apps, call_app, search_apps, get_app_categories

    # Tampilkan semua app
    apps = list_apps()

    # Panggil satu app
    result = call_app("calculator", expression="2 + 2 * 3")

    # Cari app
    matches = search_apps("zakat")

    # Kelompokkan per kategori
    cats = get_app_categories()
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import re
import statistics
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable


# ──────────────────────────────────────────────────────────────────────────────
# Tipe data dasar
# ──────────────────────────────────────────────────────────────────────────────

AppResult = dict[str, Any]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers internal
# ──────────────────────────────────────────────────────────────────────────────

def _ok(data: Any, note: str = "") -> AppResult:
    """Bungkus hasil sukses."""
    r: AppResult = {"ok": True, "result": data}
    if note:
        r["note"] = note
    return r


def _err(msg: str) -> AppResult:
    """Bungkus hasil error."""
    return {"ok": False, "error": msg}


# ──────────────────────────────────────────────────────────────────────────────
# HANDLERS — satu fungsi per app
# ──────────────────────────────────────────────────────────────────────────────

# --- MATH ---

def _calc_handler(expression: str = "", **kwargs) -> AppResult:
    """
    Hitung ekspresi matematika dasar (+ - * / ** % sqrt log).
    Hanya fungsi aman yang diizinkan — tidak ada eval() terhadap kode sembarangan.

    Args:
        expression: string ekspresi, e.g. "2 + 3 * 4" atau "sqrt(16)"
    """
    if not expression:
        return _err("Parameter 'expression' wajib diisi.")

    allowed_names = {
        "sqrt": math.sqrt,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "atan2": math.atan2,
        "pi": math.pi,
        "e": math.e,
        "abs": abs,
        "round": round,
        "pow": pow,
        "floor": math.floor,
        "ceil": math.ceil,
        "factorial": math.factorial,
        "inf": math.inf,
    }

    # Tolak karakter berbahaya sebelum eval
    forbidden = re.compile(r"(__|\bimport\b|\bexec\b|\bopen\b|\beval\b|os\.|sys\.)")
    if forbidden.search(expression):
        return _err("Ekspresi mengandung kata kunci yang tidak diizinkan.")

    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)  # noqa: S307
        return _ok(result, f"Ekspresi: {expression}")
    except ZeroDivisionError:
        return _err("Pembagian dengan nol.")
    except Exception as exc:
        return _err(f"Gagal mengevaluasi ekspresi: {exc}")


def _statistics_handler(
    data: list | str = None,
    mode: str = "summary",
    **kwargs
) -> AppResult:
    """
    Hitung statistik deskriptif dari daftar angka.

    Args:
        data : list angka, atau string dipisah koma "1,2,3,4,5"
        mode : "summary" | "mean" | "median" | "stdev" | "variance" | "min" | "max"
    """
    if data is None:
        return _err("Parameter 'data' wajib diisi (list atau string dipisah koma).")

    if isinstance(data, str):
        try:
            nums = [float(x.strip()) for x in data.split(",") if x.strip()]
        except ValueError:
            return _err("Data tidak valid. Gunakan angka dipisah koma.")
    elif isinstance(data, list):
        try:
            nums = [float(x) for x in data]
        except (ValueError, TypeError):
            return _err("List harus berisi angka.")
    else:
        return _err("Parameter 'data' harus list atau string.")

    if not nums:
        return _err("Data kosong.")

    try:
        summary = {
            "count": len(nums),
            "mean": statistics.mean(nums),
            "median": statistics.median(nums),
            "min": min(nums),
            "max": max(nums),
            "range": max(nums) - min(nums),
            "sum": sum(nums),
        }
        if len(nums) >= 2:
            summary["stdev"] = statistics.stdev(nums)
            summary["variance"] = statistics.variance(nums)

        if mode == "summary":
            return _ok(summary)
        elif mode in summary:
            return _ok({mode: summary[mode]})
        else:
            return _err(f"Mode tidak dikenal: {mode}. Pilih: {list(summary.keys())}")
    except Exception as exc:
        return _err(f"Error statistik: {exc}")


def _unit_converter_handler(
    value: float = None,
    from_unit: str = "",
    to_unit: str = "",
    **kwargs
) -> AppResult:
    """
    Konversi satuan panjang, berat, suhu, dan volume.

    Args:
        value     : nilai angka
        from_unit : satuan asal (m, km, ft, in, kg, lb, g, oz, C, F, K, L, mL, gallon)
        to_unit   : satuan tujuan
    """
    if value is None:
        return _err("Parameter 'value' wajib diisi.")
    if not from_unit or not to_unit:
        return _err("Parameter 'from_unit' dan 'to_unit' wajib diisi.")

    # Tabel konversi ke satuan dasar SI
    length_to_m = {
        "m": 1.0, "km": 1000.0, "cm": 0.01, "mm": 0.001,
        "ft": 0.3048, "in": 0.0254, "yd": 0.9144, "mi": 1609.344,
        "nm": 1852.0,  # nautical mile
    }
    weight_to_kg = {
        "kg": 1.0, "g": 0.001, "mg": 1e-6, "lb": 0.453592,
        "oz": 0.0283495, "ton": 1000.0, "quintal": 100.0,
    }
    volume_to_L = {
        "L": 1.0, "mL": 0.001, "gallon": 3.78541, "qt": 0.946353,
        "pt": 0.473176, "cup": 0.236588, "fl_oz": 0.0295735, "tbsp": 0.0147868,
        "tsp": 0.00492892, "m3": 1000.0, "cm3": 0.001,
    }

    fu = from_unit.lower()
    tu = to_unit.lower()

    # Suhu — kasus khusus
    temp_units = {"c", "f", "k"}
    if fu in temp_units or tu in temp_units:
        try:
            if fu == "c":
                celsius = float(value)
            elif fu == "f":
                celsius = (float(value) - 32) * 5 / 9
            elif fu == "k":
                celsius = float(value) - 273.15
            else:
                return _err(f"Satuan suhu tidak dikenal: {from_unit}")

            if tu == "c":
                result = celsius
            elif tu == "f":
                result = celsius * 9 / 5 + 32
            elif tu == "k":
                result = celsius + 273.15
            else:
                return _err(f"Satuan suhu tidak dikenal: {to_unit}")

            return _ok({"value": value, "from": from_unit, "to": to_unit, "result": round(result, 6)})
        except Exception as exc:
            return _err(f"Error konversi suhu: {exc}")

    # Panjang
    if fu in length_to_m and tu in length_to_m:
        result = float(value) * length_to_m[fu] / length_to_m[tu]
        return _ok({"value": value, "from": from_unit, "to": to_unit, "result": round(result, 8)})

    # Berat
    if fu in weight_to_kg and tu in weight_to_kg:
        result = float(value) * weight_to_kg[fu] / weight_to_kg[tu]
        return _ok({"value": value, "from": from_unit, "to": to_unit, "result": round(result, 8)})

    # Volume
    if fu in volume_to_L and tu in volume_to_L:
        result = float(value) * volume_to_L[fu] / volume_to_L[tu]
        return _ok({"value": value, "from": from_unit, "to": to_unit, "result": round(result, 8)})

    return _err(
        f"Tidak bisa mengkonversi '{from_unit}' ke '{to_unit}'. "
        "Pastikan keduanya dalam kategori yang sama (panjang/berat/volume/suhu)."
    )


def _equation_solver_handler(
    a: float = None,
    b: float = None,
    c: float = None,
    mode: str = "quadratic",
    **kwargs
) -> AppResult:
    """
    Selesaikan persamaan kuadrat ax² + bx + c = 0.

    Args:
        a, b, c : koefisien
        mode    : saat ini hanya "quadratic"
    """
    if a is None or b is None or c is None:
        return _err("Parameter a, b, c wajib diisi untuk persamaan kuadrat.")

    a, b, c = float(a), float(b), float(c)
    if a == 0:
        if b == 0:
            return _err("Bukan persamaan (a=0, b=0). Tidak ada solusi.")
        x = -c / b
        return _ok({"type": "linear", "x": x, "equation": f"{b}x + {c} = 0"})

    discriminant = b ** 2 - 4 * a * c
    if discriminant > 0:
        x1 = (-b + math.sqrt(discriminant)) / (2 * a)
        x2 = (-b - math.sqrt(discriminant)) / (2 * a)
        return _ok({
            "type": "quadratic",
            "discriminant": discriminant,
            "roots": "real dan berbeda",
            "x1": round(x1, 8),
            "x2": round(x2, 8),
            "equation": f"{a}x² + {b}x + {c} = 0",
        })
    elif discriminant == 0:
        x = -b / (2 * a)
        return _ok({
            "type": "quadratic",
            "discriminant": 0,
            "roots": "kembar",
            "x": round(x, 8),
            "equation": f"{a}x² + {b}x + {c} = 0",
        })
    else:
        real_part = -b / (2 * a)
        imag_part = math.sqrt(abs(discriminant)) / (2 * a)
        return _ok({
            "type": "quadratic",
            "discriminant": discriminant,
            "roots": "kompleks",
            "x1": f"{round(real_part, 6)} + {round(imag_part, 6)}i",
            "x2": f"{round(real_part, 6)} - {round(imag_part, 6)}i",
            "equation": f"{a}x² + {b}x + {c} = 0",
        })


# --- DATETIME ---

def _datetime_handler(
    mode: str = "now",
    timezone_offset: int = 7,
    date_str: str = "",
    **kwargs
) -> AppResult:
    """
    Informasi tanggal dan waktu.

    Args:
        mode           : "now" | "timestamp" | "diff" | "add_days" | "weekday" | "hijri_approx"
        timezone_offset: offset UTC dalam jam (default 7 = WIB)
        date_str       : tanggal dalam format YYYY-MM-DD (untuk mode diff, add_days, weekday, hijri)
    """
    tz = timezone(timedelta(hours=timezone_offset))
    now = datetime.now(tz)

    if mode == "now":
        return _ok({
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": now.strftime("%A"),
            "timezone": f"UTC+{timezone_offset}",
        })

    elif mode == "timestamp":
        return _ok({
            "unix_timestamp": int(now.timestamp()),
            "iso8601": now.isoformat(),
        })

    elif mode == "weekday":
        if not date_str:
            d = now
        else:
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=tz)
            except ValueError:
                return _err("Format tanggal tidak valid. Gunakan YYYY-MM-DD.")
        hari_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        return _ok({
            "date": d.strftime("%Y-%m-%d"),
            "weekday_en": d.strftime("%A"),
            "weekday_id": hari_indo[d.weekday()],
        })

    elif mode == "add_days":
        days = int(kwargs.get("days", 1))
        if date_str:
            try:
                base = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=tz)
            except ValueError:
                return _err("Format tanggal tidak valid. Gunakan YYYY-MM-DD.")
        else:
            base = now
        result_date = base + timedelta(days=days)
        return _ok({
            "base": base.strftime("%Y-%m-%d"),
            "days_added": days,
            "result": result_date.strftime("%Y-%m-%d"),
        })

    elif mode == "diff":
        date2 = kwargs.get("date2", "")
        if not date_str or not date2:
            return _err("Butuh 'date_str' dan 'date2' untuk mode 'diff'.")
        try:
            d1 = datetime.strptime(date_str, "%Y-%m-%d")
            d2 = datetime.strptime(date2, "%Y-%m-%d")
        except ValueError:
            return _err("Format tanggal tidak valid. Gunakan YYYY-MM-DD.")
        diff = abs((d2 - d1).days)
        return _ok({"date1": date_str, "date2": date2, "diff_days": diff, "diff_weeks": round(diff / 7, 2)})

    elif mode == "hijri_approx":
        # Konversi masehi ke hijriah (aproksimasi — cukup untuk use case umum)
        if date_str:
            try:
                greg = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return _err("Format tanggal tidak valid. Gunakan YYYY-MM-DD.")
        else:
            greg = now

        # Rumus aproksimasi Julian Day → Hijriah
        jd = (
            367 * greg.year
            - int(7 * (greg.year + int((greg.month + 9) / 12)) / 4)
            + int(275 * greg.month / 9)
            + greg.day
            + 1721013.5
        )
        # Konversi JD ke Hijriah (algoritma Fliegel-Van Flandern yang disederhanakan)
        z = int(jd + 0.5)
        a = int((z - 1867216.25) / 36524.25)
        b = z + 1 + a - int(a / 4) + 1524
        c = int((b - 122.1) / 365.25)
        d_val = int(365.25 * c)
        e = int((b - d_val) / 30.6001)

        day_g = b - d_val - int(30.6001 * e)
        month_g = e - 1 if e < 14 else e - 13
        year_g = c - 4716 if month_g > 2 else c - 4715

        # Hijriah dari Julian Day (rumus Khalid Shaukat yang disederhanakan)
        l_val = z - 1948440 + 10632
        n = int((l_val - 1) / 10631)
        l_val -= 10631 * n + 354
        j = int((10985 - l_val) / 5316) * int(50 * l_val / 17719) + int(l_val / 5670) * int(43 * l_val / 15238)
        l_val -= int((30 - j) / 15) * int(17719 * j / 50) + int(j / 16) * int(15238 * j / 43)
        i_val = int(8 * l_val / 2480)
        hijri_day = l_val - int(2951 * i_val / 80)
        k = int(i_val / 12)
        hijri_month = i_val + 1 - 12 * k
        hijri_year = n * 30 + k - 671

        bulan_hijri = [
            "Muharram", "Safar", "Rabi'ul Awwal", "Rabi'ul Akhir",
            "Jumadal Ula", "Jumadal Akhirah", "Rajab", "Sya'ban",
            "Ramadan", "Syawal", "Dzulqa'dah", "Dzulhijjah"
        ]
        nama_bulan = bulan_hijri[hijri_month - 1] if 1 <= hijri_month <= 12 else "?"

        return _ok({
            "gregorian": greg.strftime("%Y-%m-%d"),
            "hijri_day": hijri_day,
            "hijri_month": hijri_month,
            "hijri_month_name": nama_bulan,
            "hijri_year": hijri_year,
            "hijri_formatted": f"{hijri_day} {nama_bulan} {hijri_year} H",
            "catatan": "Hasil adalah aproksimasi. Konfirmasi dengan ru'yatul hilal.",
        })

    return _err(f"Mode tidak dikenal: {mode}. Pilih: now, timestamp, weekday, add_days, diff, hijri_approx")


# --- TEXT TOOLS ---

def _text_tools_handler(
    text: str = "",
    operation: str = "info",
    **kwargs
) -> AppResult:
    """
    Berbagai operasi teks.

    Args:
        text      : teks input
        operation : "info" | "wordcount" | "uppercase" | "lowercase" | "title" |
                    "reverse" | "slug" | "strip" | "count_sentences"
    """
    if not text and operation != "info":
        return _err("Parameter 'text' wajib diisi.")

    ops = {
        "info": lambda t: {
            "char_count": len(t),
            "word_count": len(t.split()),
            "line_count": t.count("\n") + 1,
            "is_empty": not t.strip(),
        },
        "wordcount": lambda t: {"word_count": len(t.split()), "char_count": len(t), "char_no_spaces": len(t.replace(" ", ""))},
        "uppercase": lambda t: t.upper(),
        "lowercase": lambda t: t.lower(),
        "title": lambda t: t.title(),
        "reverse": lambda t: t[::-1],
        "slug": lambda t: re.sub(r"[^a-z0-9]+", "-", t.lower().strip()).strip("-"),
        "strip": lambda t: t.strip(),
        "count_sentences": lambda t: {"sentence_count": len(re.split(r"[.!?]+", t.strip())) },
        "capitalize_words": lambda t: " ".join(w.capitalize() for w in t.split()),
    }

    if operation not in ops:
        return _err(f"Operasi tidak dikenal: '{operation}'. Pilih: {', '.join(ops.keys())}")

    try:
        result = ops[operation](text)
        return _ok(result)
    except Exception as exc:
        return _err(f"Error operasi teks: {exc}")


def _base64_handler(
    text: str = "",
    operation: str = "encode",
    **kwargs
) -> AppResult:
    """
    Encode/decode Base64.

    Args:
        text      : string yang akan di-encode atau di-decode
        operation : "encode" | "decode"
    """
    if not text:
        return _err("Parameter 'text' wajib diisi.")

    if operation == "encode":
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
        return _ok({"original": text, "encoded": encoded})
    elif operation == "decode":
        try:
            decoded = base64.b64decode(text.encode("ascii")).decode("utf-8")
            return _ok({"encoded": text, "decoded": decoded})
        except Exception as exc:
            return _err(f"Gagal decode Base64: {exc}")
    else:
        return _err("Operasi harus 'encode' atau 'decode'.")


def _hash_handler(
    text: str = "",
    algorithm: str = "sha256",
    **kwargs
) -> AppResult:
    """
    Buat hash kriptografi dari teks.

    Args:
        text      : teks yang akan di-hash
        algorithm : "md5" | "sha1" | "sha256" | "sha512"
    """
    if not text:
        return _err("Parameter 'text' wajib diisi.")

    supported = {"md5", "sha1", "sha256", "sha512", "sha224", "sha384"}
    algo = algorithm.lower()
    if algo not in supported:
        return _err(f"Algoritma tidak didukung: {algorithm}. Pilih: {supported}")

    h = hashlib.new(algo, text.encode("utf-8")).hexdigest()
    return _ok({"text": text, "algorithm": algo, "hash": h})


def _json_formatter_handler(
    json_str: str = "",
    indent: int = 2,
    operation: str = "format",
    **kwargs
) -> AppResult:
    """
    Format atau validasi JSON.

    Args:
        json_str  : string JSON
        indent    : indentasi (default 2)
        operation : "format" | "validate" | "minify"
    """
    if not json_str:
        return _err("Parameter 'json_str' wajib diisi.")

    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as exc:
        return {"ok": False, "valid": False, "error": f"JSON tidak valid: {exc}"}

    if operation == "validate":
        return _ok({"valid": True, "keys_at_root": list(parsed.keys()) if isinstance(parsed, dict) else None})
    elif operation == "format":
        formatted = json.dumps(parsed, indent=indent, ensure_ascii=False)
        return _ok({"formatted": formatted})
    elif operation == "minify":
        minified = json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)
        return _ok({"minified": minified})
    else:
        return _err(f"Operasi tidak dikenal: {operation}. Pilih: format, validate, minify")


def _uuid_generator_handler(count: int = 1, version: int = 4, **kwargs) -> AppResult:
    """
    Generate UUID.

    Args:
        count   : jumlah UUID yang dibuat (1-100)
        version : versi UUID (4 untuk random, 1 untuk timestamp-based)
    """
    count = min(max(int(count), 1), 100)
    results = []
    for _ in range(count):
        if version == 1:
            results.append(str(uuid.uuid1()))
        else:
            results.append(str(uuid.uuid4()))
    return _ok({"uuids": results, "count": count, "version": version})


# --- WEB TOOLS (STUBS) ---

def _web_search_handler(query: str = "", **kwargs) -> AppResult:
    """
    Stub pencarian web. Mengembalikan petunjuk cara integrasi pencarian.
    Koneksi nyata memerlukan API (SerpAPI, DuckDuckGo, etc).

    Args:
        query: kata kunci pencarian
    """
    if not query:
        return _err("Parameter 'query' wajib diisi.")

    return _ok({
        "query": query,
        "status": "stub",
        "note": (
            "Tool ini adalah stub. Untuk pencarian nyata, integrasikan dengan "
            "DuckDuckGo Instant Answer API (gratis) atau SerpAPI. "
            "Lihat: https://api.duckduckgo.com/?q={query}&format=json"
        ),
        "duckduckgo_url": f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1",
    })


def _wikipedia_handler(topic: str = "", lang: str = "id", **kwargs) -> AppResult:
    """
    Cari ringkasan Wikipedia untuk suatu topik.
    Menggunakan Wikipedia API (tidak memerlukan API key).

    Args:
        topic : topik yang dicari
        lang  : kode bahasa ("id" = Indonesia, "en" = Inggris, "ar" = Arab)
    """
    import urllib.request
    import urllib.parse

    if not topic:
        return _err("Parameter 'topic' wajib diisi.")

    try:
        encoded = urllib.parse.quote(topic)
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "SIDIX-AI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        return _ok({
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "extract": data.get("extract", "")[:800],  # batasi 800 karakter
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "lang": lang,
        })
    except Exception as exc:
        return _err(f"Gagal mengambil data Wikipedia: {exc}")


# --- DATA TOOLS ---

def _csv_parser_handler(
    csv_text: str = "",
    delimiter: str = ",",
    has_header: bool = True,
    **kwargs
) -> AppResult:
    """
    Parse teks CSV menjadi struktur data.

    Args:
        csv_text   : konten CSV sebagai string
        delimiter  : pemisah kolom (default ",")
        has_header : apakah baris pertama adalah header
    """
    if not csv_text:
        return _err("Parameter 'csv_text' wajib diisi.")

    import csv
    import io

    try:
        reader = csv.reader(io.StringIO(csv_text), delimiter=delimiter)
        rows = list(reader)

        if not rows:
            return _err("CSV kosong.")

        if has_header:
            headers = rows[0]
            data = [dict(zip(headers, row)) for row in rows[1:]]
        else:
            data = rows

        return _ok({
            "row_count": len(data),
            "column_count": len(rows[0]) if rows else 0,
            "headers": headers if has_header else None,
            "data": data[:20],  # tampilkan maks 20 baris
            "truncated": len(data) > 20,
        })
    except Exception as exc:
        return _err(f"Gagal parse CSV: {exc}")


def _password_generator_handler(
    length: int = 16,
    include_uppercase: bool = True,
    include_digits: bool = True,
    include_symbols: bool = True,
    **kwargs
) -> AppResult:
    """
    Generate password acak yang kuat.

    Args:
        length            : panjang password (8-128)
        include_uppercase : sertakan huruf besar
        include_digits    : sertakan angka
        include_symbols   : sertakan simbol
    """
    import secrets
    import string

    length = min(max(int(length), 8), 128)
    chars = string.ascii_lowercase
    if include_uppercase:
        chars += string.ascii_uppercase
    if include_digits:
        chars += string.digits
    if include_symbols:
        chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"

    pwd = "".join(secrets.choice(chars) for _ in range(length))
    entropy_bits = length * math.log2(len(chars))

    return _ok({
        "password": pwd,
        "length": length,
        "entropy_bits": round(entropy_bits, 1),
        "strength": "Sangat Kuat" if entropy_bits > 60 else ("Kuat" if entropy_bits > 40 else "Sedang"),
    })


# --- ISLAMIC TOOLS ---

def _zakat_calculator_handler(
    asset_type: str = "maal",
    total_assets: float = None,
    nisab_gold_grams: float = 85.0,
    gold_price_per_gram: float = 1000000.0,
    **kwargs
) -> AppResult:
    """
    Kalkulator zakat maal dan zakat fitrah.

    Args:
        asset_type          : "maal" | "fitrah" | "pertanian" | "perdagangan"
        total_assets        : total harta dalam Rupiah (untuk zakat maal/perdagangan)
        nisab_gold_grams    : nisab emas dalam gram (default 85 gram — standar Ulama)
        gold_price_per_gram : harga emas per gram dalam Rupiah

    Nisab: 85 gram emas (standar MUI dan jumhur ulama kontemporer)
    Kadar zakat maal: 2.5%
    Haul: 1 tahun kepemilikan penuh
    """
    if asset_type == "fitrah":
        # Zakat fitrah — perkiraan berdasarkan harga beras 2024
        harga_beras_per_kg = kwargs.get("harga_beras_per_kg", 15000)
        takaran_liter = 2.5  # 1 sha' ≈ 2.5 kg beras
        fitrah_beras_kg = takaran_liter
        fitrah_uang = fitrah_beras_kg * harga_beras_per_kg

        return _ok({
            "jenis": "Zakat Fitrah",
            "takaran_beras": f"{takaran_liter} kg beras (1 sha')",
            "setara_uang": f"Rp {fitrah_uang:,.0f}",
            "harga_beras_dipakai": f"Rp {harga_beras_per_kg:,.0f}/kg",
            "catatan": (
                "Nilai setara uang bersifat perkiraan. "
                "Konfirmasi dengan Baznas atau lembaga zakat setempat. "
                "Dibayarkan sebelum shalat Idul Fitri."
            ),
        })

    if total_assets is None:
        return _err("Parameter 'total_assets' wajib diisi untuk zakat maal/perdagangan/pertanian.")

    nisab_rupiah = nisab_gold_grams * gold_price_per_gram

    if asset_type in ("maal", "perdagangan"):
        kadar = 0.025  # 2.5%
        tipe_label = "Zakat Maal" if asset_type == "maal" else "Zakat Perdagangan"

        if total_assets < nisab_rupiah:
            return _ok({
                "jenis": tipe_label,
                "total_harta": f"Rp {total_assets:,.0f}",
                "nisab": f"Rp {nisab_rupiah:,.0f} (setara {nisab_gold_grams}g emas @ Rp {gold_price_per_gram:,.0f}/g)",
                "status": "Belum wajib zakat",
                "keterangan": f"Harta Anda belum mencapai nisab. Kurang Rp {nisab_rupiah - total_assets:,.0f}",
            })

        zakat = total_assets * kadar
        return _ok({
            "jenis": tipe_label,
            "total_harta": f"Rp {total_assets:,.0f}",
            "nisab": f"Rp {nisab_rupiah:,.0f}",
            "kadar_zakat": "2.5%",
            "jumlah_zakat": f"Rp {zakat:,.0f}",
            "status": "Wajib zakat (jika sudah haul 1 tahun)",
            "catatan": (
                "Pastikan harta sudah dimiliki penuh selama 1 tahun haul. "
                "Termasuk: tabungan, investasi, emas, piutang yang bisa ditagih, stok dagangan. "
                "Dikurangi: hutang jangka pendek."
            ),
        })

    elif asset_type == "pertanian":
        kadar_tadah_hujan = 0.10   # 10% — pertanian tadah hujan
        kadar_irigasi = 0.05       # 5% — pertanian irigasi
        irigasi = kwargs.get("irigasi", False)
        kadar = kadar_irigasi if irigasi else kadar_tadah_hujan

        # Nisab pertanian: 5 wasaq = ±653 kg gabah kering
        nisab_kg_gabah = 653.0
        berat_hasil_kg = total_assets  # dianggap dalam kg

        if berat_hasil_kg < nisab_kg_gabah:
            return _ok({
                "jenis": "Zakat Pertanian",
                "hasil_panen": f"{berat_hasil_kg} kg",
                "nisab": f"{nisab_kg_gabah} kg (5 wasaq)",
                "status": "Belum wajib zakat",
            })

        zakat_kg = berat_hasil_kg * kadar
        return _ok({
            "jenis": "Zakat Pertanian",
            "hasil_panen": f"{berat_hasil_kg} kg",
            "nisab": f"{nisab_kg_gabah} kg (5 wasaq)",
            "sistem_pengairan": "Irigasi (5%)" if irigasi else "Tadah hujan (10%)",
            "kadar_zakat": f"{kadar*100:.0f}%",
            "jumlah_zakat": f"{zakat_kg} kg (atau setara uang)",
            "status": "Wajib zakat",
            "catatan": "Zakat pertanian dikeluarkan setiap panen, tidak perlu menunggu haul.",
        })

    return _err(f"Jenis zakat tidak dikenal: {asset_type}. Pilih: maal, fitrah, perdagangan, pertanian")


def _prayer_times_handler(
    latitude: float = None,
    longitude: float = None,
    date_str: str = "",
    method: str = "MWL",
    **kwargs
) -> AppResult:
    """
    Hitung waktu shalat (Fajr, Syuruq, Dhuhr, Ashr, Maghrib, Isha).
    Menggunakan algoritma astronomi murni — tidak memerlukan API eksternal.

    Args:
        latitude  : lintang (contoh: -6.2088 untuk Jakarta)
        longitude : bujur (contoh: 106.8456 untuk Jakarta)
        date_str  : tanggal YYYY-MM-DD (default: hari ini)
        method    : "MWL" (Muslim World League) | "ISNA" | "Egypt" | "Makkah" | "Karachi" | "UOIF"

    Metode koreksi sudut fajr/isha:
        MWL    : Fajr 18°, Isha 17° (digunakan di sebagian besar Asia, Eropa)
        ISNA   : Fajr 15°, Isha 15° (Amerika Utara)
        Egypt  : Fajr 19.5°, Isha 17.5°
        Makkah : Fajr 18.5°, Isha 90 menit setelah Maghrib
        Karachi: Fajr 18°, Isha 18°
        UOIF   : Fajr 12°, Isha 12° (Eropa/UOIF)
    """
    if latitude is None or longitude is None:
        return _err(
            "Parameter 'latitude' dan 'longitude' wajib diisi. "
            "Contoh Jakarta: latitude=-6.2088, longitude=106.8456"
        )

    lat = float(latitude)
    lon = float(longitude)

    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return _err("Format tanggal tidak valid. Gunakan YYYY-MM-DD.")
    else:
        target_date = datetime.now()

    # Parameter sudut per metode
    methods = {
        "MWL":     {"fajr": 18.0, "isha": 17.0},
        "ISNA":    {"fajr": 15.0, "isha": 15.0},
        "Egypt":   {"fajr": 19.5, "isha": 17.5},
        "Makkah":  {"fajr": 18.5, "isha": None},  # None = 90 menit setelah Maghrib
        "Karachi": {"fajr": 18.0, "isha": 18.0},
        "UOIF":    {"fajr": 12.0, "isha": 12.0},
    }
    m = methods.get(method.upper(), methods["MWL"])

    def _deg2rad(d): return d * math.pi / 180
    def _rad2deg(r): return r * 180 / math.pi

    year = target_date.year
    month = target_date.month
    day = target_date.day

    # Julian Day Number
    a = int((14 - month) / 12)
    y = year + 4800 - a
    m_val = month + 12 * a - 3
    jdn = day + int((153 * m_val + 2) / 5) + 365 * y + int(y / 4) - int(y / 100) + int(y / 400) - 32045
    jd = jdn - 0.5  # noon Julian Date

    # Julian centuries dari J2000.0
    T = (jd - 2451545.0) / 36525.0

    # Solar declination dan equation of time
    L0 = 280.46646 + 36000.76983 * T
    M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
    M_rad = _deg2rad(M % 360)
    C = (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M_rad)
    C += (0.019993 - 0.000101 * T) * math.sin(2 * M_rad)
    C += 0.000289 * math.sin(3 * M_rad)

    sun_lon = L0 + C
    omega = 125.04 - 1934.136 * T
    apparent_lon = sun_lon - 0.00569 - 0.00478 * math.sin(_deg2rad(omega))
    epsilon = 23.439291 - 0.013004 * T
    decl = _rad2deg(math.asin(math.sin(_deg2rad(epsilon)) * math.sin(_deg2rad(apparent_lon))))

    # Equation of time (dalam menit)
    y2 = math.tan(_deg2rad(epsilon / 2)) ** 2
    eot = (
        y2 * math.sin(2 * _deg2rad(L0))
        - 2 * 0.016708634 * math.sin(M_rad)
        + 4 * 0.016708634 * y2 * math.sin(M_rad) * math.cos(2 * _deg2rad(L0))
        - 0.5 * y2 * y2 * math.sin(4 * _deg2rad(L0))
        - 1.25 * 0.016708634 ** 2 * math.sin(2 * M_rad)
    )
    eot_min = _rad2deg(eot) * 4

    # Transit (Dzuhur) dalam jam WAKTU LOKAL (bujur-based)
    # Solar noon lokal = 12 jam - equation of time (menit→jam)
    # Semua waktu berikutnya dihitung dalam waktu lokal bujur
    transit_local = 12.0 - eot_min / 60.0

    def _hour_angle(angle_deg, decl_deg, lat_deg):
        """
        Hitung hour angle untuk sudut altitude matahari tertentu.
        Formula: cos(H) = (sin(alt) - sin(lat)*sin(decl)) / (cos(lat)*cos(decl))
        """
        num = math.sin(_deg2rad(angle_deg)) - math.sin(_deg2rad(lat_deg)) * math.sin(_deg2rad(decl_deg))
        den = math.cos(_deg2rad(lat_deg)) * math.cos(_deg2rad(decl_deg))
        if den == 0:
            return None
        ratio = num / den
        if abs(ratio) > 1:
            return None  # matahari tidak terbenam/terbit (polar atau musim ekstrem)
        return _rad2deg(math.acos(ratio))

    def _to_time_str(hours_local):
        """
        Format jam waktu lokal (float) ke string HH:MM:SS.
        Waktu sudah dalam zona lokal berdasarkan bujur.
        """
        h_local = hours_local % 24
        h = int(h_local)
        m_t = int((h_local - h) * 60)
        s = int(((h_local - h) * 60 - m_t) * 60)
        return f"{h:02d}:{m_t:02d}:{s:02d}"

    # Ashr — mazhab Syafi'i/Maliki/Hanbali (shadow = 1x tinggi benda + shadow noon)
    # Ketinggian matahari saat transit
    decl_rad = _deg2rad(decl)
    lat_rad = _deg2rad(lat)
    noon_altitude = _rad2deg(math.asin(
        math.sin(lat_rad) * math.sin(decl_rad) + math.cos(lat_rad) * math.cos(decl_rad)
    ))
    # Formula Ashr: cot(ashr_alt) = 1 + cot(noon_alt)
    # => ashr_alt = atan(1 / (1 + cos(noon_alt)/sin(noon_alt)))
    noon_alt_rad = _deg2rad(abs(noon_altitude))
    cot_noon = math.cos(noon_alt_rad) / math.sin(noon_alt_rad) if math.sin(noon_alt_rad) != 0 else 0
    ashr_angle = _rad2deg(math.atan(1.0 / (1.0 + cot_noon)))

    ha_sunrise = _hour_angle(-0.833, decl, lat)
    ha_ashr = _hour_angle(ashr_angle, decl, lat) if noon_altitude > 0 else None
    ha_fajr = _hour_angle(-m["fajr"], decl, lat)
    ha_isha = _hour_angle(-m["isha"], decl, lat) if m["isha"] else None

    # Hitung waktu lokal (berdasarkan transit_local)
    times = {}

    if ha_sunrise:
        sunrise_local = transit_local - ha_sunrise / 15
        sunset_local = transit_local + ha_sunrise / 15
        times["Syuruq (Sunrise)"] = _to_time_str(sunrise_local)
        times["Maghrib"] = _to_time_str(sunset_local)
        # Isya 90 menit setelah Maghrib untuk metode Makkah
        if m["isha"] is None:
            times["Isya"] = _to_time_str(sunset_local + 1.5)

    times["Dzuhur"] = _to_time_str(transit_local)

    if ha_ashr:
        times["Ashr"] = _to_time_str(transit_local + ha_ashr / 15)

    if ha_fajr:
        times["Subuh (Fajr)"] = _to_time_str(transit_local - ha_fajr / 15)

    if ha_isha and m["isha"]:
        times["Isya"] = _to_time_str(transit_local + ha_isha / 15)

    # Urutkan
    ordered_keys = ["Subuh (Fajr)", "Syuruq (Sunrise)", "Dzuhur", "Ashr", "Maghrib", "Isya"]
    ordered_times = {k: times.get(k, "N/A") for k in ordered_keys}

    return _ok({
        "tanggal": target_date.strftime("%Y-%m-%d"),
        "lokasi": {"latitude": lat, "longitude": lon},
        "metode": method.upper(),
        "waktu_shalat": ordered_times,
        "deklinasi_matahari": round(decl, 4),
        "catatan": (
            "Waktu ditampilkan dalam waktu lokal berdasarkan bujur. "
            "Selisih beberapa menit mungkin terjadi — konfirmasi dengan jadwal Kemenag RI. "
            "Untuk akurasi tinggi gunakan library PrayTimes.js atau adhan-python."
        ),
    })


def _qiblat_handler(
    latitude: float = None,
    longitude: float = None,
    **kwargs
) -> AppResult:
    """
    Hitung arah kiblat (Ka'bah Mekkah) dari suatu titik koordinat.
    Menggunakan formula Great Circle (Vincenty-simple).

    Args:
        latitude  : lintang lokasi Anda (contoh: -6.2088 untuk Jakarta)
        longitude : bujur lokasi Anda (contoh: 106.8456 untuk Jakarta)
    """
    if latitude is None or longitude is None:
        return _err("Parameter 'latitude' dan 'longitude' wajib diisi.")

    lat = float(latitude)
    lon = float(longitude)

    # Koordinat Ka'bah Mekkah (presisi tinggi)
    MECCA_LAT = 21.4225
    MECCA_LON = 39.8262

    def _deg2rad(d): return d * math.pi / 180
    def _rad2deg(r): return r * 180 / math.pi

    lat1 = _deg2rad(lat)
    lon1 = _deg2rad(lon)
    lat2 = _deg2rad(MECCA_LAT)
    lon2 = _deg2rad(MECCA_LON)

    delta_lon = lon2 - lon1

    x = math.sin(delta_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
    bearing = _rad2deg(math.atan2(x, y))
    bearing = (bearing + 360) % 360  # normalisasi 0-360

    # Jarak ke Mekkah (Great Circle, km)
    a = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    distance_km = 6371.0 * c  # radius bumi

    # Arah kompas
    directions = [
        "Utara (U)", "Timur Laut (TL)", "Timur (T)", "Tenggara (TG)",
        "Selatan (S)", "Barat Daya (BD)", "Barat (B)", "Barat Laut (BL)"
    ]
    compass = directions[int((bearing + 22.5) / 45) % 8]

    return _ok({
        "lokasi": {"latitude": lat, "longitude": lon},
        "arah_kiblat": {
            "derajat_dari_utara": round(bearing, 2),
            "arah_kompas": compass,
            "keterangan": f"Putar {round(bearing, 1)}° dari arah Utara (searah jarum jam)",
        },
        "jarak_ke_mekkah": {
            "km": round(distance_km, 2),
            "miles": round(distance_km * 0.621371, 2),
        },
        "koordinat_kabah": {"latitude": MECCA_LAT, "longitude": MECCA_LON},
        "catatan": (
            "Arah kiblat dihitung menggunakan formula Great Circle. "
            "Untuk presisi tinggi di lokasi polar, gunakan azimuth dari database BMKG/Kemenag."
        ),
    })


def _asmaul_husna_handler(
    number: int = None,
    query: str = "",
    **kwargs
) -> AppResult:
    """
    Cari informasi Asmaul Husna (99 Nama Allah).

    Args:
        number : nomor 1-99 (opsional)
        query  : kata kunci Arab/Indonesia untuk dicari (opsional)
    """
    asmaul_husna = [
        (1, "الرَّحْمَنُ", "Ar-Rahman", "Yang Maha Pengasih"),
        (2, "الرَّحِيمُ", "Ar-Rahim", "Yang Maha Penyayang"),
        (3, "الْمَلِكُ", "Al-Malik", "Yang Maha Merajai/Memiliki"),
        (4, "الْقُدُّوسُ", "Al-Quddus", "Yang Maha Suci"),
        (5, "السَّلاَمُ", "As-Salam", "Yang Maha Memberi Keselamatan"),
        (6, "الْمُؤْمِنُ", "Al-Mu'min", "Yang Maha Memberi Keamanan"),
        (7, "الْمُهَيْمِنُ", "Al-Muhaymin", "Yang Maha Mengawasi"),
        (8, "الْعَزِيزُ", "Al-'Aziz", "Yang Maha Perkasa"),
        (9, "الْجَبَّارُ", "Al-Jabbar", "Yang Maha Memiliki Kekuatan"),
        (10, "الْمُتَكَبِّرُ", "Al-Mutakabbir", "Yang Maha Megah"),
        (11, "الْخَالِقُ", "Al-Khaliq", "Yang Maha Pencipta"),
        (12, "الْبَارِئُ", "Al-Bari'", "Yang Maha Melepaskan"),
        (13, "الْمُصَوِّرُ", "Al-Musawwir", "Yang Maha Membentuk Rupa"),
        (14, "الْغَفَّارُ", "Al-Ghaffar", "Yang Maha Pengampun"),
        (15, "الْقَهَّارُ", "Al-Qahhar", "Yang Maha Menundukkan"),
        (16, "الْوَهَّابُ", "Al-Wahhab", "Yang Maha Pemberi"),
        (17, "الرَّزَّاقُ", "Ar-Razzaq", "Yang Maha Pemberi Rezeki"),
        (18, "الْفَتَّاحُ", "Al-Fattah", "Yang Maha Membuka Rahmat"),
        (19, "اَلْعَلِيمُ", "Al-'Alim", "Yang Maha Mengetahui"),
        (20, "الْقَابِضُ", "Al-Qabidh", "Yang Maha Menyempitkan"),
        (21, "الْبَاسِطُ", "Al-Basith", "Yang Maha Melapangkan"),
        (22, "الْخَافِضُ", "Al-Khafidh", "Yang Maha Merendahkan"),
        (23, "الرَّافِعُ", "Ar-Rafi'", "Yang Maha Meninggikan"),
        (24, "الْمُعِزُّ", "Al-Mu'izz", "Yang Maha Memuliakan"),
        (25, "الْمُذِلُّ", "Al-Mudzill", "Yang Maha Menghinakan"),
        (26, "السَّمِيعُ", "As-Sami'", "Yang Maha Mendengar"),
        (27, "الْبَصِيرُ", "Al-Bashir", "Yang Maha Melihat"),
        (28, "الْحَكَمُ", "Al-Hakam", "Yang Maha Menetapkan"),
        (29, "الْعَدْلُ", "Al-'Adl", "Yang Maha Adil"),
        (30, "اللَّطِيفُ", "Al-Lathif", "Yang Maha Lembut"),
        (31, "الْخَبِيرُ", "Al-Khabir", "Yang Maha Mengenal"),
        (32, "الْحَلِيمُ", "Al-Halim", "Yang Maha Penyantun"),
        (33, "الْعَظِيمُ", "Al-'Azhim", "Yang Maha Agung"),
        (34, "الْغَفُورُ", "Al-Ghafur", "Yang Maha Pengampun"),
        (35, "الشَّكُورُ", "Asy-Syakur", "Yang Maha Mensyukuri"),
        (36, "الْعَلِيُّ", "Al-'Ali", "Yang Maha Tinggi"),
        (37, "الْكَبِيرُ", "Al-Kabir", "Yang Maha Besar"),
        (38, "الْحَفِيظُ", "Al-Hafizh", "Yang Maha Memelihara"),
        (39, "الْمُقِيتُ", "Al-Muqit", "Yang Maha Pemberi Kecukupan"),
        (40, "الْحَسِيبُ", "Al-Hasib", "Yang Maha Membuat Perhitungan"),
        (41, "الْجَلِيلُ", "Al-Jalil", "Yang Maha Mulia"),
        (42, "الْكَرِيمُ", "Al-Karim", "Yang Maha Mulia"),
        (43, "الرَّقِيبُ", "Ar-Raqib", "Yang Maha Mengawasi"),
        (44, "الْمُجِيبُ", "Al-Mujib", "Yang Maha Mengabulkan"),
        (45, "الْوَاسِعُ", "Al-Wasi'", "Yang Maha Luas"),
        (46, "الْحَكِيمُ", "Al-Hakim", "Yang Maha Bijaksana"),
        (47, "الْوَدُودُ", "Al-Wadud", "Yang Maha Mencintai"),
        (48, "الْمَجِيدُ", "Al-Majid", "Yang Maha Mulia"),
        (49, "الْبَاعِثُ", "Al-Ba'ith", "Yang Maha Membangkitkan"),
        (50, "الشَّهِيدُ", "Asy-Syahid", "Yang Maha Menyaksikan"),
        (51, "الْحَقُّ", "Al-Haqq", "Yang Maha Benar"),
        (52, "الْوَكِيلُ", "Al-Wakil", "Yang Maha Memelihara"),
        (53, "الْقَوِيُّ", "Al-Qawiyy", "Yang Maha Kuat"),
        (54, "الْمَتِينُ", "Al-Matin", "Yang Maha Kokoh"),
        (55, "الْوَلِيُّ", "Al-Waliyy", "Yang Maha Melindungi"),
        (56, "الْحَمِيدُ", "Al-Hamid", "Yang Maha Terpuji"),
        (57, "الْمُحْصِي", "Al-Muhshi", "Yang Maha Menghitung"),
        (58, "الْمُبْدِئُ", "Al-Mubdi'", "Yang Maha Memulai"),
        (59, "الْمُعِيدُ", "Al-Mu'id", "Yang Maha Mengembalikan Kehidupan"),
        (60, "الْمُحْيِي", "Al-Muhyi", "Yang Maha Menghidupkan"),
        (61, "الْمُمِيتُ", "Al-Mumit", "Yang Maha Mematikan"),
        (62, "الْحَيُّ", "Al-Hayy", "Yang Maha Hidup"),
        (63, "الْقَيُّومُ", "Al-Qayyum", "Yang Maha Mandiri"),
        (64, "الْوَاجِدُ", "Al-Wajid", "Yang Maha Penemu"),
        (65, "الْمَاجِدُ", "Al-Majid", "Yang Maha Mulia"),
        (66, "الْوَاحِدُ", "Al-Wahid", "Yang Maha Tunggal"),
        (67, "اَلاَحَدُ", "Al-Ahad", "Yang Maha Esa"),
        (68, "الصَّمَدُ", "As-Shamad", "Yang Maha Dibutuhkan"),
        (69, "الْقَادِرُ", "Al-Qadir", "Yang Maha Menentukan"),
        (70, "الْمُقْتَدِرُ", "Al-Muqtadir", "Yang Maha Berkuasa"),
        (71, "الْمُقَدِّمُ", "Al-Muqaddim", "Yang Maha Mendahulukan"),
        (72, "الْمُؤَخِّرُ", "Al-Mu'akhkhir", "Yang Maha Mengakhirkan"),
        (73, "الأوَّلُ", "Al-Awwal", "Yang Maha Awal"),
        (74, "الآخِرُ", "Al-Akhir", "Yang Maha Akhir"),
        (75, "الظَّاهِرُ", "Azh-Zhahir", "Yang Maha Nyata"),
        (76, "الْبَاطِنُ", "Al-Bathin", "Yang Maha Ghaib"),
        (77, "الْوَالِي", "Al-Wali", "Yang Maha Memerintah"),
        (78, "الْمُتَعَالِي", "Al-Muta'ali", "Yang Maha Tinggi"),
        (79, "الْبَرُّ", "Al-Barr", "Yang Maha Penderma"),
        (80, "التَّوَّابُ", "At-Tawwab", "Yang Maha Penerima Tobat"),
        (81, "الْمُنْتَقِمُ", "Al-Muntaqim", "Yang Maha Pemberi Azab"),
        (82, "الْعَفُوُّ", "Al-'Afuww", "Yang Maha Pemaaf"),
        (83, "الرَّؤُوفُ", "Ar-Ra'uf", "Yang Maha Pengasih"),
        (84, "مَالِكُ الْمُلْكِ", "Malikul Mulk", "Yang Maha Penguasa Kerajaan"),
        (85, "ذُو الْجَلاَلِ وَالإِكْرَامِ", "Dzul Jalali Wal Ikram", "Yang Maha Pemilik Kebesaran"),
        (86, "الْمُقْسِطُ", "Al-Muqsith", "Yang Maha Pemberi Keadilan"),
        (87, "الْجَامِعُ", "Al-Jami'", "Yang Maha Mengumpulkan"),
        (88, "الْغَنِيُّ", "Al-Ghani", "Yang Maha Kaya"),
        (89, "الْمُغْنِي", "Al-Mughni", "Yang Maha Pemberi Kekayaan"),
        (90, "الْمَانِعُ", "Al-Mani'", "Yang Maha Mencegah"),
        (91, "الضَّارُّ", "Adh-Dharr", "Yang Maha Memberi Derita"),
        (92, "النَّافِعُ", "An-Nafi'", "Yang Maha Memberi Manfaat"),
        (93, "النُّورُ", "An-Nur", "Yang Maha Bercahaya"),
        (94, "الْهَادِي", "Al-Hadi", "Yang Maha Pemberi Petunjuk"),
        (95, "الْبَدِيعُ", "Al-Badi'", "Yang Maha Pencipta"),
        (96, "اَلْبَاقِي", "Al-Baqi", "Yang Maha Kekal"),
        (97, "الْوَارِثُ", "Al-Warith", "Yang Maha Pewaris"),
        (98, "الرَّشِيدُ", "Ar-Rasyid", "Yang Maha Pandai"),
        (99, "الصَّبُورُ", "As-Shabur", "Yang Maha Sabar"),
    ]

    if number is not None:
        n = int(number)
        if 1 <= n <= 99:
            entry = asmaul_husna[n - 1]
            return _ok({
                "nomor": entry[0],
                "arab": entry[1],
                "latin": entry[2],
                "arti": entry[3],
            })
        return _err("Nomor harus antara 1-99.")

    if query:
        q = query.lower()
        results = [
            {"nomor": e[0], "arab": e[1], "latin": e[2], "arti": e[3]}
            for e in asmaul_husna
            if q in e[1].lower() or q in e[2].lower() or q in e[3].lower()
        ]
        if results:
            return _ok({"query": query, "hasil": results})
        return _ok({"query": query, "hasil": [], "pesan": "Tidak ditemukan."})

    # Tampilkan semua
    return _ok({
        "total": 99,
        "daftar": [
            {"nomor": e[0], "arab": e[1], "latin": e[2], "arti": e[3]}
            for e in asmaul_husna
        ],
    })


# ──────────────────────────────────────────────────────────────────────────────
# REGISTRY UTAMA
# ──────────────────────────────────────────────────────────────────────────────

BUILTIN_APPS: dict[str, dict] = {
    # --- MATH ---
    "calculator": {
        "description": "Hitung ekspresi matematika (+ - * / ** sqrt log sin cos tan pi e dll)",
        "handler": _calc_handler,
        "category": "math",
        "params": {"expression": "string ekspresi matematika"},
        "example": {"expression": "sqrt(144) + 2**8"},
    },
    "statistics": {
        "description": "Hitung statistik deskriptif: mean, median, stdev, min, max dari daftar angka",
        "handler": _statistics_handler,
        "category": "math",
        "params": {
            "data": "list angka atau string dipisah koma",
            "mode": "summary | mean | median | stdev | variance | min | max",
        },
        "example": {"data": "10,20,30,40,50", "mode": "summary"},
    },
    "equation_solver": {
        "description": "Selesaikan persamaan kuadrat ax² + bx + c = 0",
        "handler": _equation_solver_handler,
        "category": "math",
        "params": {"a": "koefisien a", "b": "koefisien b", "c": "koefisien c"},
        "example": {"a": 1, "b": -5, "c": 6},
    },
    "unit_converter": {
        "description": "Konversi satuan: panjang (m/km/ft/in/yd/mi), berat (kg/g/lb/oz), volume (L/mL/gallon), suhu (C/F/K)",
        "handler": _unit_converter_handler,
        "category": "math",
        "params": {
            "value": "nilai angka",
            "from_unit": "satuan asal",
            "to_unit": "satuan tujuan",
        },
        "example": {"value": 100, "from_unit": "C", "to_unit": "F"},
    },
    # --- DATETIME ---
    "datetime_tool": {
        "description": "Informasi tanggal/waktu: sekarang, timestamp, hari, tambah hari, selisih hari, konversi Hijriah",
        "handler": _datetime_handler,
        "category": "datetime",
        "params": {
            "mode": "now | timestamp | weekday | add_days | diff | hijri_approx",
            "timezone_offset": "offset UTC dalam jam (default 7 = WIB)",
            "date_str": "YYYY-MM-DD (opsional)",
        },
        "example": {"mode": "hijri_approx", "date_str": "2026-04-18"},
    },
    # --- TEXT ---
    "text_tools": {
        "description": "Operasi teks: wordcount, uppercase, lowercase, title, reverse, slug, strip, count_sentences",
        "handler": _text_tools_handler,
        "category": "text",
        "params": {
            "text": "teks input",
            "operation": "info | wordcount | uppercase | lowercase | title | reverse | slug | strip",
        },
        "example": {"text": "Halo Dunia SIDIX", "operation": "slug"},
    },
    "base64": {
        "description": "Encode atau decode teks menggunakan Base64",
        "handler": _base64_handler,
        "category": "text",
        "params": {
            "text": "string input",
            "operation": "encode | decode",
        },
        "example": {"text": "Bismillah", "operation": "encode"},
    },
    "hash_generator": {
        "description": "Buat hash kriptografi: md5, sha1, sha256, sha512",
        "handler": _hash_handler,
        "category": "text",
        "params": {
            "text": "teks yang akan di-hash",
            "algorithm": "md5 | sha1 | sha256 | sha512",
        },
        "example": {"text": "sidix-ai", "algorithm": "sha256"},
    },
    "json_formatter": {
        "description": "Format, validasi, atau minify JSON",
        "handler": _json_formatter_handler,
        "category": "data",
        "params": {
            "json_str": "string JSON",
            "indent": "indentasi (default 2)",
            "operation": "format | validate | minify",
        },
        "example": {"json_str": '{"nama":"sidix","versi":1}', "operation": "format"},
    },
    "csv_parser": {
        "description": "Parse teks CSV menjadi struktur data (JSON)",
        "handler": _csv_parser_handler,
        "category": "data",
        "params": {
            "csv_text": "konten CSV sebagai string",
            "delimiter": "pemisah kolom (default ',')",
            "has_header": "apakah baris pertama header (True/False)",
        },
        "example": {"csv_text": "nama,usia\nUser,25\nSIDIX,1", "delimiter": ","},
    },
    "uuid_generator": {
        "description": "Generate UUID v4 (random) atau v1 (timestamp-based)",
        "handler": _uuid_generator_handler,
        "category": "utility",
        "params": {
            "count": "jumlah UUID (1-100)",
            "version": "versi UUID: 4 (random) atau 1 (timestamp)",
        },
        "example": {"count": 3, "version": 4},
    },
    "password_generator": {
        "description": "Generate password acak yang kuat dengan pengukur entropi",
        "handler": _password_generator_handler,
        "category": "utility",
        "params": {
            "length": "panjang password (8-128, default 16)",
            "include_uppercase": "sertakan huruf besar (True/False)",
            "include_digits": "sertakan angka (True/False)",
            "include_symbols": "sertakan simbol (True/False)",
        },
        "example": {"length": 20, "include_symbols": True},
    },
    # --- WEB ---
    "web_search": {
        "description": "Stub pencarian web — mengembalikan URL DuckDuckGo API untuk integrasi",
        "handler": _web_search_handler,
        "category": "web",
        "params": {"query": "kata kunci pencarian"},
        "example": {"query": "epistemologi Islam SIDIX"},
    },
    "wikipedia": {
        "description": "Ambil ringkasan Wikipedia untuk suatu topik (mendukung bahasa id/en/ar)",
        "handler": _wikipedia_handler,
        "category": "web",
        "params": {
            "topic": "topik yang dicari",
            "lang": "kode bahasa: id | en | ar (default: id)",
        },
        "example": {"topic": "Ibnu Khaldun", "lang": "id"},
    },
    # --- ISLAMIC ---
    "prayer_times": {
        "description": "Hitung waktu shalat (Subuh, Syuruq, Dzuhur, Ashr, Maghrib, Isya) berdasarkan koordinat — algoritma astronomi murni",
        "handler": _prayer_times_handler,
        "category": "islamic",
        "params": {
            "latitude": "lintang lokasi (contoh: -6.2088 untuk Jakarta)",
            "longitude": "bujur lokasi (contoh: 106.8456 untuk Jakarta)",
            "date_str": "YYYY-MM-DD (opsional, default hari ini)",
            "method": "MWL | ISNA | Egypt | Makkah | Karachi | UOIF",
        },
        "example": {"latitude": -6.2088, "longitude": 106.8456, "method": "MWL"},
    },
    "zakat_calculator": {
        "description": "Kalkulator zakat: maal (2.5%), fitrah, perdagangan, pertanian — dengan nisab dan haul",
        "handler": _zakat_calculator_handler,
        "category": "islamic",
        "params": {
            "asset_type": "maal | fitrah | perdagangan | pertanian",
            "total_assets": "total harta dalam Rupiah (atau kg untuk pertanian)",
            "nisab_gold_grams": "nisab emas dalam gram (default 85g)",
            "gold_price_per_gram": "harga emas per gram dalam Rupiah",
        },
        "example": {"asset_type": "maal", "total_assets": 100_000_000, "gold_price_per_gram": 1_200_000},
    },
    "qiblat": {
        "description": "Hitung arah kiblat (Ka'bah) dan jarak ke Mekkah menggunakan formula Great Circle",
        "handler": _qiblat_handler,
        "category": "islamic",
        "params": {
            "latitude": "lintang lokasi Anda",
            "longitude": "bujur lokasi Anda",
        },
        "example": {"latitude": -6.2088, "longitude": 106.8456},
    },
    "asmaul_husna": {
        "description": "Cari dan tampilkan Asmaul Husna (99 Nama Allah) — bisa per nomor atau pencarian kata kunci",
        "handler": _asmaul_husna_handler,
        "category": "islamic",
        "params": {
            "number": "nomor 1-99 (opsional)",
            "query": "kata kunci Arab/Indonesia untuk dicari (opsional)",
        },
        "example": {"number": 1},
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ──────────────────────────────────────────────────────────────────────────────

def list_apps() -> list[dict]:
    """
    Kembalikan daftar semua builtin apps beserta metadata.

    Returns:
        List dict: [{"name": ..., "description": ..., "category": ..., "params": ...}, ...]
    """
    return [
        {
            "name": name,
            "description": meta["description"],
            "category": meta["category"],
            "params": meta.get("params", {}),
            "example": meta.get("example", {}),
        }
        for name, meta in BUILTIN_APPS.items()
    ]


def call_app(name: str, **kwargs) -> AppResult:
    """
    Panggil satu builtin app berdasarkan nama.

    Args:
        name   : nama app (key di BUILTIN_APPS)
        **kwargs: parameter yang diteruskan ke handler

    Returns:
        dict dengan key "ok", "result" atau "error"

    Contoh:
        result = call_app("calculator", expression="2 ** 10")
        result = call_app("prayer_times", latitude=-6.2088, longitude=106.8456)
        result = call_app("zakat_calculator", asset_type="maal", total_assets=50_000_000)
    """
    if name not in BUILTIN_APPS:
        available = ", ".join(sorted(BUILTIN_APPS.keys()))
        return _err(f"App '{name}' tidak ditemukan. App yang tersedia: {available}")

    handler: Callable = BUILTIN_APPS[name]["handler"]
    try:
        return handler(**kwargs)
    except TypeError as exc:
        return _err(f"Parameter tidak valid untuk '{name}': {exc}")
    except Exception as exc:
        return _err(f"Error saat menjalankan '{name}': {exc}")


def search_apps(query: str) -> list[dict]:
    """
    Cari builtin app berdasarkan kata kunci (nama, deskripsi, atau kategori).

    Args:
        query: kata kunci pencarian

    Returns:
        List dict app yang cocok, diurutkan berdasarkan relevansi
    """
    q = query.lower()
    results = []
    for name, meta in BUILTIN_APPS.items():
        score = 0
        if q in name.lower():
            score += 3
        if q in meta["description"].lower():
            score += 2
        if q in meta["category"].lower():
            score += 1
        if score > 0:
            results.append({
                "name": name,
                "description": meta["description"],
                "category": meta["category"],
                "relevance": score,
            })

    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results


def get_app_categories() -> dict[str, list[dict]]:
    """
    Kelompokkan semua builtin apps berdasarkan kategori.

    Returns:
        dict: {"math": [...], "datetime": [...], "text": [...], ...}
    """
    categories: dict[str, list] = {}
    for name, meta in BUILTIN_APPS.items():
        cat = meta["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "name": name,
            "description": meta["description"],
        })
    return categories


def get_app_info(name: str) -> AppResult:
    """
    Tampilkan detail satu app termasuk params dan contoh penggunaan.

    Args:
        name: nama app

    Returns:
        dict info lengkap atau error
    """
    if name not in BUILTIN_APPS:
        return _err(f"App '{name}' tidak ditemukan.")

    meta = BUILTIN_APPS[name]
    return _ok({
        "name": name,
        "description": meta["description"],
        "category": meta["category"],
        "params": meta.get("params", {}),
        "example": meta.get("example", {}),
        "usage": f"call_app('{name}', **{meta.get('example', {})})",
    })
