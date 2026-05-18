#!/usr/bin/env python3
import sys, time
sys.path.insert(0, "/opt/sidix/apps/brain_qa")

print("Importing...", flush=True)
t0 = time.time()
from brain_qa.agency_kit import AgencyKitRequest
print("Import done", int((time.time()-t0)*1000), "ms", flush=True)

print("Creating request...", flush=True)
t0 = time.time()
req = AgencyKitRequest(business_name="QA", niche="Test", target_audience="Dev", budget="1jt")
t1 = time.time()
print("Request done", int((t1-t0)*1000), "ms", flush=True)
print("Request:", req, flush=True)
