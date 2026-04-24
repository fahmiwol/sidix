"""Smoke test sensor hub."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "brain_qa"))

from brain_qa.sensor_hub import probe_all, health_summary, list_senses

result = probe_all()
print(f"Total senses: {result['total']}")
print(f"Active: {result['active']} | Inactive: {result['inactive']} | Broken: {result['broken']} | Unknown: {result['unknown']}")
print()
print("Body parts:")
for body, slugs in result["by_body"].items():
    print(f"  {body}: {slugs}")
print()
print("Per-sense detail:")
for s in result["senses"]:
    print(f"  [{s['status'].upper():8}] {s['slug']:20} ({s['body_part']:12}) -- {s['notes']}")
print()
print("Summary:", health_summary())
