# -*- coding: utf-8 -*-
"""
Generator skrip mini satu file.

CLI:
    python gen_script.py --name my_tool --description "Deskripsi tool" --output output.py

Menghasilkan template Python minimal yang aman dengan:
- argparse
- logging
- main()
- guard if __name__ == "__main__"
"""

import argparse
import logging
import os
import sys
from datetime import date

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Template ───────────────────────────────────────────────────────────────────
SCRIPT_TEMPLATE = '''\
# -*- coding: utf-8 -*-
"""
{name} — {description}

Dibuat oleh: gen_script.py
Tanggal    : {date}
"""

import argparse
import logging
import sys

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Fungsi utama ───────────────────────────────────────────────────────────────
def main(args: argparse.Namespace) -> int:
    """Entry point utama. Kembalikan 0 jika sukses, non-zero jika gagal."""
    logger.info("Memulai {name} ...")

    # TODO: implementasi logika utama di sini
    logger.info("Selesai.")
    return 0


# ── CLI ────────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="{name}",
        description="{description}",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Aktifkan output verbose (DEBUG level)",
    )
    # TODO: tambahkan argumen sesuai kebutuhan
    return parser


if __name__ == "__main__":
    _parser = build_parser()
    _args = _parser.parse_args()

    if _args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    sys.exit(main(_args))
'''


# ── Fungsi pembuat skrip ───────────────────────────────────────────────────────
def generate(name: str, description: str, output: str, overwrite: bool = False) -> None:
    """Buat file skrip Python dari template."""
    if os.path.exists(output) and not overwrite:
        logger.error(
            "File sudah ada: %s  (gunakan --overwrite untuk menimpa)", output
        )
        sys.exit(1)

    rendered = SCRIPT_TEMPLATE.format(
        name=name,
        description=description,
        date=date.today().isoformat(),
    )

    output_dir = os.path.dirname(os.path.abspath(output))
    os.makedirs(output_dir, exist_ok=True)

    with open(output, "w", encoding="utf-8") as fh:
        fh.write(rendered)

    logger.info("Skrip berhasil dibuat: %s", output)
    logger.info("Jalankan dengan: python %s --help", output)


# ── CLI ────────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gen_script",
        description="Generator skrip mini satu file untuk SIDIX/Mighan.",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Nama skrip/tool (digunakan sebagai prog name dan judul docstring)",
    )
    parser.add_argument(
        "--description",
        required=True,
        help="Deskripsi singkat tool yang akan di-generate",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path file output (default: <name>.py di direktori saat ini)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Timpa file output jika sudah ada",
    )
    return parser


def main(args: argparse.Namespace) -> int:
    output = args.output or f"{args.name}.py"
    generate(
        name=args.name,
        description=args.description,
        output=output,
        overwrite=args.overwrite,
    )
    return 0


if __name__ == "__main__":
    _parser = build_parser()
    _args = _parser.parse_args()
    sys.exit(main(_args))
