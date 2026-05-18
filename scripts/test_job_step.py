#!/usr/bin/env python3
import sys, time, threading, uuid
sys.path.insert(0, "/opt/sidix/apps/brain_qa")

from brain_qa.agency_kit import AgencyKitRequest

print("STEP 1: import done", flush=True)

req = AgencyKitRequest(business_name="QA", niche="Test", target_audience="Dev", budget="1jt")
print("STEP 2: request created", flush=True)

# Inline create_agency_kit_job logic
import brain_qa.agency_kit as ak

print("STEP 3: getting lock", flush=True)
job_id = str(uuid.uuid4())
req_dict = req.model_dump()
print("STEP 4: model_dump done", flush=True)

job = ak.AgencyKitJob(
    job_id=job_id,
    status="queued",
    progress=0,
    results={"_request": req_dict},
    created_at=ak._now_iso(),
)
print("STEP 5: job created", flush=True)

with ak._JOB_LOCK:
    print("STEP 6: inside lock", flush=True)
    ak._prune_jobs()
    print("STEP 7: prune done", flush=True)
    ak._JOB_STORE[job_id] = job
    print("STEP 8: store done", flush=True)

print("STEP 9: lock released", flush=True)
thread = threading.Thread(target=ak.run_agency_kit_pipeline, args=(job_id,), daemon=True)
print("STEP 10: thread created", flush=True)
thread.start()
print("STEP 11: thread started", flush=True)
print("job_id:", job_id, flush=True)
print("DONE", flush=True)
