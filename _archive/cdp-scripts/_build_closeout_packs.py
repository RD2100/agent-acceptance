#!/usr/bin/env python3
"""Build ECS-A2 compliant evidence packs for REVIEW-A1 and FIX-A1.

Follows the same two-pass ZIP pattern as scripts/build_evidence_pack.py:
1. Write evidence-manifest.json with placeholder pack_info
2. First pass: create ZIP including manifest (placeholder values)
3. Patch manifest on disk with first-pass ZIP SHA256 + size
4. Second pass: rebuild ZIP with patched manifest
5. Report final ZIP SHA256 + size
6. Validate: manifest JSON parse, ZIP exists, required files present

Note: By design, manifest.pack_info.zip_sha256 records the FIRST-pass ZIP hash.
The second-pass ZIP (which includes the patched manifest) will have a different hash.
This matches the reference implementation in scripts/build_evidence_pack.py.
"""

import hashlib
import json
import os
import sys
import zipfile
from datetime import datetime, timezone, timedelta

TZ_CST = timezone(timedelta(hours=8))
REPO = r"D:\agent-acceptance"
NOW = datetime.now(TZ_CST).isoformat()

TASKS = [
    {
        "task_id": "LIVE-DISPATCH-READINESS-REVIEW-A1",
        "short": "LIVE_DISPATCH_REVIEW_A1",
        "evidence_dir": os.path.join(REPO, "_evidence", "LIVE-DISPATCH-READINESS-REVIEW-A1"),
        "zip_name": "EVIDENCE_PACK_LIVE_DISPATCH_REVIEW_A1.zip",
        "base_commit": "7ddb641f",
        "head_commit": "323fcbc",
        "commit_chain": [
            {"hash": "66ebc66fdcbee27e2b31eb8b6c45070e700b3c87", "author": "RD2100",
             "timestamp": "2026-06-12T12:29:45+08:00",
             "subject": "feat: LIVE-DISPATCH-READINESS-REVIEW-A1 - readiness verdict NOT_READY_NEEDS_FIXES"},
            {"hash": "323fcbc23f46509c366e867f6f60e1aa47932cd1", "author": "RD2100",
             "timestamp": "2026-06-12T12:56:14+08:00",
             "subject": "chore: LIVE-DISPATCH-READINESS-REVIEW-A1 - record GPT R1 verdict accepted_with_limitation"},
        ],
        "required_tier0": [
            "chain-evidence.json",
            "safety-report.json",
            "review.md",
            "review.yaml",
            "final-report.md",
            "deferred-files-register.yaml",
        ],
    },
    {
        "task_id": "LIVE-DISPATCH-READINESS-FIX-A1",
        "short": "LIVE_DISPATCH_FIX_A1",
        "evidence_dir": os.path.join(REPO, "_evidence", "LIVE-DISPATCH-READINESS-FIX-A1"),
        "zip_name": "EVIDENCE_PACK_LIVE_DISPATCH_FIX_A1.zip",
        "base_commit": "323fcbc",
        "head_commit": "35cb4db",
        "commit_chain": [
            {"hash": "018886b47bb335223ef045fe057e655b23ce5ed1", "author": "RD2100",
             "timestamp": "2026-06-12T14:02:59+08:00",
             "subject": "fix: LIVE-DISPATCH-READINESS-FIX-A1 - resolve blocking issues, upgrade verdict to READY"},
            {"hash": "35cb4db568b8bd2f8c383f0f96949eb0ab7b098a", "author": "RD2100",
             "timestamp": "2026-06-12T14:09:06+08:00",
             "subject": "chore: LIVE-DISPATCH-READINESS-FIX-A1 - record GPT R2 response (project status analysis)"},
        ],
        "required_tier0": [
            "chain-evidence.json",
            "safety-report.json",
            "review.md",
            "review.yaml",
            "final-report.md",
            "binding-fix-evidence.md",
            "DRY_RUN_DISPATCH_10_FRESH.json",
        ],
    },
]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_files(evidence_dir: str):
    """Collect all files in evidence dir, return sorted list of (relpath, abspath).
    Excludes evidence-manifest.json (will be regenerated)."""
    files = []
    for root, dirs, filenames in os.walk(evidence_dir):
        for fn in sorted(filenames):
            abspath = os.path.join(root, fn)
            relpath = os.path.relpath(abspath, evidence_dir)
            if fn == "evidence-manifest.json":
                continue
            files.append((relpath, abspath))
    files.sort(key=lambda x: x[0])
    return files


def compute_content_hash(files):
    """Compute content_sha256 over all files (excluding manifest)."""
    h = hashlib.sha256()
    for relpath, abspath in sorted(files, key=lambda x: x[0]):
        h.update(relpath.encode("utf-8"))
        with open(abspath, "rb") as f:
            h.update(f.read())
    return h.hexdigest()


def build_manifest(task_cfg, files):
    """Build evidence-manifest.json content with placeholder pack_info."""
    file_entries = []
    for relpath, abspath in files:
        size = os.path.getsize(abspath)
        content_hash = sha256_file(abspath)
        file_entries.append({
            "path": relpath,
            "size_bytes": size,
            "content_sha256": content_hash,
        })

    present_names = {e["path"] for e in file_entries}
    missing_tier0 = [f for f in task_cfg["required_tier0"] if f not in present_names]

    content_sha = compute_content_hash(files)

    manifest = {
        "schema_version": "evidence-manifest.v1",
        "task_id": task_cfg["task_id"],
        "pack_name": f"EVIDENCE_PACK_{task_cfg['short']}",
        "created_at": NOW,
        "base_commit": task_cfg["base_commit"],
        "head_commit": task_cfg["head_commit"],
        "commit_chain": task_cfg["commit_chain"],
        "file_count": len(file_entries),
        "files": file_entries,
        "required_files": {
            "tier_0": task_cfg["required_tier0"],
        },
        "files_present": sorted(present_names),
        "files_missing": {
            "tier_0": missing_tier0,
        },
        "safety": {
            "live_dispatch_executed": False,
            "no_functional_changes": True,
        },
        "pack_info": {
            "file_count": len(file_entries) + 1,  # +1 for manifest itself
            "zip_size_bytes": 0,
            "zip_sha256": "",
            "content_sha256": content_sha,
        },
    }
    return manifest


def build_zip(files, evidence_dir, zip_path, manifest=None):
    """Create ZIP from evidence files, optionally including manifest.
    Returns (size_bytes, sha256)."""
    zip_dir = os.path.dirname(zip_path)
    if zip_dir:
        os.makedirs(zip_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for relpath, abspath in files:
            zf.write(abspath, relpath)
        if manifest is not None:
            manifest_bytes = json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")
            zf.writestr("evidence-manifest.json", manifest_bytes)

    sha = sha256_file(zip_path)
    size = os.path.getsize(zip_path)
    return size, sha


def validate_pack(manifest_path, zip_path):
    """Validate the final pack."""
    errors = []

    # 1. Manifest parse
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        errors.append(f"Manifest parse failed: {e}")
        return errors, None

    # 2. ZIP exists
    if not os.path.exists(zip_path):
        errors.append(f"ZIP does not exist: {zip_path}")
        return errors, manifest

    # 3. pack_info populated (not zeros/empty)
    pi = manifest.get("pack_info", {})
    if not pi.get("zip_sha256"):
        errors.append("pack_info.zip_sha256 is empty")
    if not pi.get("zip_size_bytes"):
        errors.append("pack_info.zip_size_bytes is 0")
    if not pi.get("content_sha256"):
        errors.append("pack_info.content_sha256 is empty")

    # 4. Required files present
    missing_tier0 = manifest.get("files_missing", {}).get("tier_0", [])
    if missing_tier0:
        errors.append(f"Missing tier-0 files: {missing_tier0}")

    # 5. Verify ZIP contains all expected files
    with zipfile.ZipFile(zip_path, "r") as zf:
        zip_names = set(zf.namelist())
    for req in manifest.get("required_files", {}).get("tier_0", []):
        if req not in zip_names:
            errors.append(f"ZIP missing required file: {req}")
    if "evidence-manifest.json" not in zip_names:
        errors.append("ZIP missing evidence-manifest.json")

    return errors, manifest


def process_task(task_cfg):
    print(f"\n{'='*70}")
    print(f"Building evidence pack: {task_cfg['task_id']}")
    print(f"{'='*70}")

    evidence_dir = task_cfg["evidence_dir"]
    zip_path = os.path.join(REPO, "_evidence", task_cfg["zip_name"])
    manifest_path = os.path.join(evidence_dir, "evidence-manifest.json")

    # Step 1: Collect files
    files = collect_files(evidence_dir)
    print(f"\n  Found {len(files)} evidence files:")
    for relpath, abspath in files:
        size = os.path.getsize(abspath)
        print(f"    {relpath} ({size:,} bytes)")

    # Step 2: Build manifest with placeholder pack_info
    manifest = build_manifest(task_cfg, files)
    print(f"\n  Built manifest with {manifest['file_count']} evidence files")
    print(f"  Tier-0 missing: {manifest['files_missing']['tier_0']}")
    print(f"  Content SHA256: {manifest['pack_info']['content_sha256'][:16]}...")

    # Step 3: Write manifest to disk (with placeholder values)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"  Wrote manifest (placeholder): {manifest_path}")

    # Step 4: First pass ZIP (includes manifest with placeholders)
    size1, sha1 = build_zip(files, evidence_dir, zip_path, manifest=manifest)
    print(f"\n  First-pass ZIP: {size1:,} bytes, sha256={sha1[:16]}...")

    # Step 5: Patch manifest with first-pass ZIP metadata
    manifest["pack_info"]["zip_size_bytes"] = size1
    manifest["pack_info"]["zip_sha256"] = sha1
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"  Patched manifest: zip_size={size1}, zip_sha={sha1[:16]}...")

    # Step 6: Second pass ZIP (includes patched manifest)
    size2, sha2 = build_zip(files, evidence_dir, zip_path, manifest=manifest)
    print(f"\n  Final ZIP: {size2:,} bytes, sha256={sha2[:16]}...")
    print(f"  (Note: manifest records first-pass SHA {sha1[:16]}... ; final ZIP SHA differs by design)")

    # Step 7: Validate
    print(f"\n  Validating pack...")
    errors, loaded_manifest = validate_pack(manifest_path, zip_path)
    if errors:
        print(f"  VALIDATION FAILED:")
        for e in errors:
            print(f"    - {e}")
    else:
        print(f"  VALIDATION PASSED")

    print(f"\n  Results:")
    print(f"    Manifest: {manifest_path}")
    print(f"    ZIP:      {zip_path}")
    print(f"    Files:    {manifest['file_count']}")
    print(f"    Size:     {manifest['pack_info']['zip_size_bytes']:,} bytes")
    print(f"    SHA256:   {manifest['pack_info']['zip_sha256']}")
    print(f"    Content:  {manifest['pack_info']['content_sha256']}")

    return len(errors) == 0


if __name__ == "__main__":
    results = {}
    for task_cfg in TASKS:
        ok = process_task(task_cfg)
        results[task_cfg["task_id"]] = ok

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    for tid, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  {tid}: {status}")

    if all(results.values()):
        print("\nAll evidence packs built and validated successfully.")
        sys.exit(0)
    else:
        print("\nSome packs failed validation.")
        sys.exit(1)
