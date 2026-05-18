#!/bin/bash
# Cek 4-label epistemik di draft terbaru
DRAFT_ID="${1:-draft_1776575790_curriculum_2026-04-19_coding_python}"

echo "=== Draft: $DRAFT_ID ==="
curl -s "http://localhost:8765/drafts/$DRAFT_ID" | python3 - <<'PYEOF'
import json, sys, re
d = json.load(sys.stdin)
draft = d.get("draft", {})
md = draft.get("markdown", "")
labels = re.findall(r"\[(FACT|OPINION|SPECULATION|UNKNOWN)\]", md)
print("Total label found:", len(labels))
print("Distribusi:", {l: labels.count(l) for l in set(labels)})
print("Status:", draft.get("status"))
print("Sanad:", "yes" if draft.get("sanad") else "no")
print("Epistemic info:", draft.get("epistemic"))
print("")
print("=== Narrative section snippet ===")
narr_match = re.search(r"## SIDIX Bercerita.*?\n\n_.*?_\n\n(.+?)\n\n## ", md, re.DOTALL)
if narr_match:
    print(narr_match.group(1)[:1000])
else:
    print("(no narrative section)")
PYEOF
