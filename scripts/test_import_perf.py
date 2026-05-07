#!/usr/bin/env python3
import sys, time
sys.path.insert(0, "/opt/sidix/apps/brain_qa")
t0 = time.time()
print("Importing agency_kit...")
from brain_qa import agency_kit
t1 = time.time()
print("Import done in", int((t1-t0)*1000), "ms")
print("Module loaded:", agency_kit.__file__)
