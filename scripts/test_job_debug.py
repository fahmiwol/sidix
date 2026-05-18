#!/usr/bin/env python3
import sys, time, threading
sys.path.insert(0, "/opt/sidix/apps/brain_qa")

print("step 1: import")
t0 = time.time()
from brain_qa.agency_kit import AgencyKitRequest, create_agency_kit_job
print("step 1 done", int((time.time()-t0)*1000), "ms")

print("step 2: create request")
t0 = time.time()
req = AgencyKitRequest(business_name="QA", niche="Test", target_audience="Dev", budget="1jt")
print("step 2 done", int((time.time()-t0)*1000), "ms")

print("step 3: create job")
t0 = time.time()
job_id = create_agency_kit_job(req)
print("step 3 done", int((time.time()-t0)*1000), "ms")
print("job_id:", job_id)
print("active threads:", threading.active_count())
