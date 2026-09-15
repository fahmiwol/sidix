"""JSON command-line interface. Run from providers/quran-lab."""

import argparse
import json
import sys

from .provider import DISCLAIMER, get_study, principles, search, studies_for_verse
from .validate import validate


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("search")
    p.add_argument("query")
    p.add_argument("--k", type=int, default=5)
    p = commands.add_parser("get")
    p.add_argument("id")
    p = commands.add_parser("verse")
    p.add_argument("surah", type=int)
    p.add_argument("ayah", type=int)
    p = commands.add_parser("principles")
    p.add_argument("topic", nargs="?")
    commands.add_parser("validate")
    args = parser.parse_args(argv)
    code = 0
    try:
        if args.command == "search":
            result = search(args.query, args.k)
        elif args.command == "get":
            result = get_study(args.id)
        elif args.command == "verse":
            result = studies_for_verse(args.surah, args.ayah)
        elif args.command == "principles":
            result = principles(args.topic)
        else:
            result = validate()
            code = int(bool(result))
    except (KeyError, ValueError, OSError, TypeError) as exc:
        result = {"error": str(exc), "citations": [], "disclaimer": DISCLAIMER}
        code = 1
    # Escapes keep JSON portable on terminals with non-UTF-8 default encodings.
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
