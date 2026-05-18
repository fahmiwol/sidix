"""
runpod_pod_orchestrator.py — Sprint 13 Phase 3b RunPod Pod orchestration.

Spin up RunPod Pod dengan T4/L4 GPU, transfer training script + dataset,
run training, monitor, download adapter, terminate Pod.

Reads RUNPOD_API_KEY + HF_TOKEN dari env (atau /opt/sidix/.env.kaggle_hf).

Pod selection priority (cost ascending):
1. RTX A4000 16GB (~$0.20/hr) — cheapest, CC 8.6
2. RTX 3090 24GB (~$0.30/hr) — capable, CC 8.6
3. L4 24GB (~$0.40/hr) — modern, CC 8.9 (kalau bos prefer fastest cheapest)
4. V100 16GB (~$0.40/hr) — proven CC 7.0
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import runpod


PREFERRED_GPU_PRIORITY = [
    "NVIDIA RTX A4000",          # 16GB, ~$0.20/hr, CC 8.6
    "NVIDIA GeForce RTX 3090",   # 24GB, ~$0.30/hr, CC 8.6
    "NVIDIA L4",                 # 24GB, ~$0.40/hr, CC 8.9
    "Tesla V100-PCIE-16GB",      # 16GB, ~$0.40/hr, CC 7.0
]


def find_gpu_id(preferred: list[str]) -> str | None:
    """Pick first available GPU type from preferred list."""
    gpus = runpod.get_gpus()
    available = {g["id"]: g for g in gpus}
    for name in preferred:
        if name in available:
            return name
    return None


def create_pod(gpu_id: str, name: str = "sidix-dora-train") -> dict:
    """Create Pod dengan PyTorch image."""
    pod = runpod.create_pod(
        name=name,
        image_name="runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04",
        gpu_type_id=gpu_id,
        gpu_count=1,
        volume_in_gb=30,
        container_disk_in_gb=20,
        cloud_type="SECURE",  # vs "COMMUNITY" — secure has stricter SLA
        ports="22/tcp,8888/http",  # SSH + Jupyter
        volume_mount_path="/workspace",
        env={
            "HF_TOKEN": os.environ.get("HF_TOKEN", ""),
            "TRANSFORMERS_CACHE": "/workspace/.cache",
        },
    )
    return pod


def wait_pod_ready(pod_id: str, timeout: int = 300) -> dict:
    """Poll pod status sampai RUNNING."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        pod = runpod.get_pod(pod_id)
        status = pod.get("desiredStatus", "?")
        runtime = pod.get("runtime", {})
        ready = bool(runtime and runtime.get("podCompleted") is False)
        print(f"[{int(time.time() - t0)}s] status={status} ready={ready}")
        if status == "RUNNING" and runtime:
            return pod
        time.sleep(10)
    raise TimeoutError(f"Pod {pod_id} not ready after {timeout}s")


def main():
    parser = argparse.ArgumentParser(description="RunPod orchestrator Sprint 13")
    parser.add_argument("--action", choices=["create", "list", "terminate", "status"],
                        default="create", help="Pod action")
    parser.add_argument("--pod-id", help="Pod ID (untuk terminate/status)")
    parser.add_argument("--gpu", default=None, help="Force GPU type (skip auto-pick)")
    parser.add_argument("--name", default="sidix-dora-train")
    args = parser.parse_args()

    api_key = os.environ.get("RUNPOD_API_KEY")
    if not api_key:
        print("FATAL: RUNPOD_API_KEY not set")
        sys.exit(1)
    runpod.api_key = api_key

    if args.action == "list":
        pods = runpod.get_pods()
        print(json.dumps([{
            "id": p["id"],
            "name": p["name"],
            "status": p.get("desiredStatus"),
            "gpu": p.get("machine", {}).get("gpuTypeId"),
        } for p in pods], indent=2))
        return

    if args.action == "status":
        if not args.pod_id:
            print("FATAL: --pod-id required")
            sys.exit(1)
        pod = runpod.get_pod(args.pod_id)
        print(json.dumps(pod, indent=2, default=str))
        return

    if args.action == "terminate":
        if not args.pod_id:
            print("FATAL: --pod-id required")
            sys.exit(1)
        result = runpod.terminate_pod(args.pod_id)
        print(json.dumps({"ok": True, "pod_id": args.pod_id, "result": str(result)},
                          indent=2))
        return

    # Default: create
    gpu_id = args.gpu or find_gpu_id(PREFERRED_GPU_PRIORITY)
    if not gpu_id:
        print("FATAL: no preferred GPU available")
        sys.exit(1)
    print(f">>> Using GPU: {gpu_id}")

    pod = create_pod(gpu_id, name=args.name)
    pod_id = pod["id"]
    print(f">>> Pod created: {pod_id}")
    print(json.dumps(pod, indent=2, default=str))

    print(">>> Waiting for ready...")
    ready_pod = wait_pod_ready(pod_id, timeout=600)
    print(">>> Pod RUNNING. SSH info:")
    runtime = ready_pod.get("runtime", {})
    print(json.dumps(runtime, indent=2, default=str))

    print()
    print("=== Next steps (manual or auto-script) ===")
    print(f"1. Get SSH info: python {sys.argv[0]} --action status --pod-id {pod_id}")
    print(f"2. SSH ke pod, cd /workspace")
    print(f"3. Upload training script + dataset (scp via SSH)")
    print(f"4. Run: python runpod_train_lora.py --use-dora --train-data <path> --val-data <path>")
    print(f"5. Adapter auto-upload ke HF (HF_TOKEN sudah di pod env)")
    print(f"6. Terminate pod: python {sys.argv[0]} --action terminate --pod-id {pod_id}")


if __name__ == "__main__":
    main()
