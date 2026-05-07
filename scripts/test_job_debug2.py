#!/usr/bin/env python3
import sys, time, threading
sys.path.insert(0, "/opt/sidix/apps/brain_qa")

from brain_qa.agency_kit import AgencyKitRequest, create_agency_kit_job

req = AgencyKitRequest(business_name="QA", niche="Test", target_audience="Dev", budget="1jt")
print("BEFORE create_job", flush=True)
t0 = time.time()
job_id = create_agency_kit_job(req)
t1 = time.time()
print("AFTER create_job", int((t1-t0)*1000), "ms", flush=True)
print("job_id:", job_id, flush=True)
print("active threads:", threading.active_count(), flush=True)
print("DONE", flush=True)
