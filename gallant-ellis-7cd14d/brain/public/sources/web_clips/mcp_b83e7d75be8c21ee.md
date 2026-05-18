# crm-role-filter-dayofweek

**Sumber:** claude-chat  
**Tanggal:** 2026-04-17  
**Tags:** php, mysql, role-filter, dayofweek, crm  

## Konteks

Bagaimana cara filter dropdown user hanya tampilkan sales/supervisor (bukan direktur), dan filter FU berdasarkan hari dalam seminggu?

## Pengetahuan

1) Filter role: JOIN users dengan roles, WHERE COALESCE(r.level, 0) < 100 — eksklusi siapa pun dengan role_level >= 100 (full access / direktur). 2) Filter hari FU: pakai MySQL DAYOFWEEK() — 2=Senin, 3=Selasa, 4=Rabu, 5=Kamis, 6=Jumat. Query: EXISTS(SELECT 1 FROM lead_followups WHERE lead_id=leads.id AND completed_at IS NULL AND DAYOFWEEK(scheduled_at) = $day_num). Ini lebih fleksibel dari date-range karena menangkap semua jadwal FU di hari itu terlepas dari minggu keberapa.

---
*Diambil dari SIDIX MCP Knowledge Base*
