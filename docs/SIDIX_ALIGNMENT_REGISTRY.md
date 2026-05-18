# SIDIX Alignment Registry

Last verified: 2026-05-18

Purpose: single source of truth for keeping SIDIX local repo, GitHub, VPS backend, live apps, and Hugging Face artifacts aligned. This file must not contain secrets.

## Canonical Repo

- GitHub: https://github.com/fahmiwol/sidix
- Canonical branch: `main`
- Current GitHub `main`: `1eaf6875512dd6f876c755aa7222737e89d07e36`
- CI status: `brain_qa CI` green for latest `main`
- Rule: code and docs land in `main`; temporary worktrees are not production truth until merged.

## Local Workspace

- Path: `C:\SIDIX-AI`
- Branch: `main`
- Current local HEAD: `1eaf6875512dd6f876c755aa7222737e89d07e36`
- Alignment: local `main` equals GitHub `main` at verification time.

## Production VPS / Backend

- Host label: `trx.core`
- Public IP: `187.77.116.139`
- Production repo path: `/opt/sidix`
- Production branch target: `main`
- Process manager: `pm2`
- Primary backend process: `sidix-brain`
- Last confirmed production deploy from server console: fast-forward to `9c92759`, then `pm2 restart sidix-brain --update-env`.
- Current drift: GitHub is ahead by `1eaf687`, a documentation-only Living Log commit after production validation. Production-relevant code is aligned with the deployed `9c92759` state.
- SSH note: direct SSH audit from Codex local timed out on `187.77.116.139:22`; Hostinger console access is currently the reliable deploy path.

Production deploy command:

```bash
cd /opt/sidix
git pull --ff-only origin main
pm2 restart sidix-brain --update-env
pm2 status sidix-brain
```

Production audit command:

```bash
cd /opt/sidix
git rev-parse HEAD
git status --short
pm2 status sidix-brain
```

## Live Apps

- Backend/control API: https://ctrl.sidixlab.com
- User app: https://app.sidixlab.com
- Live app HTTP status: `200`
- Live health status: `ok`
- Engine: `SIDIX Inference Engine v0.1`
- `model_mode`: `sidix_local`
- `model_ready`: `true`
- Adapter path: `/opt/sidix/apps/brain_qa/models/sidix-lora-adapter`
- Adapter health: config present, weights present
- Adapter config SHA-256 prefix: `de3f5ee62efc0012`
- Tools available: `92`
- Corpus docs: `3952`
- Agent workspace root: `/opt/sidix/apps/brain_qa/agent_workspace`

Validated live UX checks after deploy:

- `makasih ya` returns natural greeting, no offline-model leak.
- `apa itu LLM? jawab singkat` returns concise definition.
- `berapa jarak bumi ke matahari? jawab singkat` returns grounded distance.
- `bikin contoh fungsi python tambah dua angka` returns usable Python snippet.
- `siapa presiden indonesia sekarang?` returns Prabowo Subianto.
- Follow-up `kalo wakilnya?` returns Gibran Rakabuming Raka in the same conversation.
- Personal memory set/recall works in the same conversation.

Known live gaps:

- Image intent no longer falls to offline-model error, but still returns a text prompt/fallback instead of an actual generated image attachment.
- Health output is slightly ambiguous: top-level `model_ready=true`, while nested `sidix_local_engine.ready=false`. Treat this as observability drift to fix, not proof that live chat is broken.

## Hugging Face

Canonical public model artifact:

- Repo: https://hf.co/Tiranyx/sidix-lora
- Role: SIDIX LoRA/PEFT adapter artifact for the own-stack inference line.
- Base model tag: `Qwen/Qwen2.5-7B-Instruct`
- Library tag: `peft`
- Task tag: `text-generation`
- License tag: `mit`
- Language tags: `id`, `en`, `ar`
- Last observed update: 2026-04-26

Experimental / secondary artifact:

- Repo: https://hf.co/Tiranyx/sidix-dora-persona-v1
- Role: persona/DoRA PEFT experiment, not the primary production adapter unless explicitly promoted.
- Base model tag: `Qwen/Qwen2.5-7B-Instruct`
- Library tag: `peft`
- Last observed update: 2026-04-29

Not canonical yet:

- SIDIX Hugging Face datasets: none found during registry check.
- SIDIX Hugging Face Spaces: none found during registry check.

Verification gap:

- The live adapter fingerprint has not been byte-compared against Hugging Face model files in this check. Do not claim Hugging Face weights equal live production weights until adapter file hashes are compared.

## Alignment Rules

1. GitHub `main` is the source of truth for SIDIX code and documentation.
2. VPS `/opt/sidix` must be updated by fast-forward pull from GitHub `main`; avoid long-lived production worktrees.
3. Live app is considered healthy only after `/health` plus user-experience smoke tests pass.
4. Hugging Face model repos are artifact mirrors, not the code source of truth.
5. Dataset or Space names are not canonical until created, verified, and recorded in this registry.
6. Any production drift, deploy, rollback, test result, or model artifact change must be appended to `docs/LIVING_LOG.md`.

