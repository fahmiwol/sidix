#!/usr/bin/env python3
import sys, time
sys.path.insert(0, "/opt/sidix/apps/brain_qa")
from brain_qa.agency_kit import AgencyKitRequest, create_agency_kit_job, get_job_status

req = AgencyKitRequest(business_name="QA", niche="Test", target_audience="Dev", budget="1jt")
print("Creating job...")
t0 = time.time()
job_id = create_agency_kit_job(req)
t1 = time.time()
print("job_id:", job_id)
print("duration_ms:", int((t1-t0)*1000))
print("job_status:", get_job_status(job_id))
