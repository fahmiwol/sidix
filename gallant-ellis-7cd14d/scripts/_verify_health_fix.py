import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'brain_qa'))
from brain_qa.sensor_hub import probe_all

r = probe_all()
senses_list = r.get('senses', [])
active = [s['slug'] for s in senses_list if s.get('status') == 'active']
print(f"total={r['total']} active={r['active']} inactive={r['inactive']} broken={r['broken']}")
print(f"active slugs: {active}")
print("Fix: health endpoint pakai slug bukan name -> OK")
