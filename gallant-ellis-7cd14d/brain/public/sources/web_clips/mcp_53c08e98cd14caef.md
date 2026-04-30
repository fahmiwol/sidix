# brain_qa — QA pairs + Milestone M2 completion

**Sumber:** claude-code  
**Tanggal:** 2026-04-16  
**Tags:** brain_qa, qa_pairs, milestone, m2, sidix  

## Konteks

Bagaimana cara melengkapi Milestone M2 SIDIX brain_qa dan format qa_pairs.jsonl yang benar?

## Pengetahuan

qa_pairs.jsonl disimpan di brain/datasets/qa_pairs.jsonl. Format per baris (JSONL): {"id":"qa-001","question":"...","ideal_answer":"...","rubric":"...","tags":["..."]}. Required fields: id, question, ideal_answer, rubric, tags. Strict mode: id harus format qa-NNN. M2 butuh minimal 10 QA pairs. Sesi ini menambah 5 QA pairs baru (qa-008 s/d qa-012) ke 7 yang sudah ada → total 12 pairs, M2 100% selesai. Topik yang dicoverage: RAG multimodal, epistemologi+AI, privasi by default, information theory+LLM, hadis+corpus. Untuk validasi: python -m brain_qa qa (dari venv).

---
*Diambil dari SIDIX MCP Knowledge Base*
