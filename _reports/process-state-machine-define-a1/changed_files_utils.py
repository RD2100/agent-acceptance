#!/usr/bin/env python3
"""
changed_files_utils.py — CHANGED_FILES_SCHEMA 生成/验证/摘要工具。

提供以下功能:
1. generate_changed_files_evidence(): 从 before/after 快照生成标准变更证明
2. validate_changed_files(): 验证变更证明是否符合 CHANGED_FILES_SCHEMA
3. summarize_changes(): 生成变更摘要
4. diff_snapshots(): 对比两个文件快照字典，返回变更列表

Usage:
    python changed_files_utils.py generate --task-id TASK_ID --before before.json --after after.json --output output.json
    python changed_files_utils.py validate --input changed_files.json [--schema CHANGED_FILES_SCHEMA.json]
    python changed_files_utils.py snapshot --dir DIRECTORY --output snapshot.json
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA = REPO / '_reports' / 'process-state-machine-define-a1' / 'CHANGED_FILES_SCHEMA.json'


def sha256_file(filepath: str | Path) -> str:
    """计算文件的 SHA-256 hash。"""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def take_snapshot(directory: str | Path, tracked_files: set[str] | None = None) -> dict[str, dict]:
    """对目录下的文件生成快照。

    Returns:
        dict mapping relative_path -> {sha256, size, tracked}
    """
    root = Path(directory)
    snapshot = {}
    for fp in sorted(root.rglob('*')):
        if fp.is_file():
            rel = fp.relative_to(root).as_posix()
            # Skip hidden directories and __pycache__
            if any(p.startswith('.') or p == '__pycache__' for p in fp.parts):
                continue
            is_tracked = True
            if tracked_files is not None:
                is_tracked = rel in tracked_files
            snapshot[rel] = {
                'sha256': sha256_file(fp),
                'size': fp.stat().st_size,
                'tracked': is_tracked,
            }
    return snapshot


def diff_snapshots(
    before: dict[str, dict],
    after: dict[str, dict],
) -> list[dict]:
    """对比两个快照，返回变更列表。

    Each change item: {path, change_type, sha256_before, sha256_after, size_before, size_after, tracked}
    """
    changes = []
    all_paths = set(before.keys()) | set(after.keys())

    for path in sorted(all_paths):
        in_before = path in before
        in_after = path in after

        if in_before and not in_after:
            changes.append({
                'path': path,
                'change_type': 'deleted',
                'sha256_before': before[path]['sha256'],
                'sha256_after': None,
                'size_before': before[path]['size'],
                'size_after': None,
                'tracked': before[path].get('tracked', True),
                'rename_from': None,
                'permission_before': None,
                'permission_after': None,
                'evidence_ref': None,
                'state_transition_ref': None,
            })
        elif not in_before and in_after:
            changes.append({
                'path': path,
                'change_type': 'added',
                'sha256_before': None,
                'sha256_after': after[path]['sha256'],
                'size_before': None,
                'size_after': after[path]['size'],
                'tracked': after[path].get('tracked', True),
                'rename_from': None,
                'permission_before': None,
                'permission_after': None,
                'evidence_ref': None,
                'state_transition_ref': None,
            })
        elif in_before and in_after:
            if before[path]['sha256'] != after[path]['sha256']:
                changes.append({
                    'path': path,
                    'change_type': 'modified',
                    'sha256_before': before[path]['sha256'],
                    'sha256_after': after[path]['sha256'],
                    'size_before': before[path]['size'],
                    'size_after': after[path]['size'],
                    'tracked': after[path].get('tracked', True),
                    'rename_from': None,
                    'permission_before': None,
                    'permission_after': None,
                    'evidence_ref': None,
                    'state_transition_ref': None,
                })

    return changes


def generate_changed_files_evidence(
    task_id: str,
    before_snapshot: dict[str, dict],
    after_snapshot: dict[str, dict],
    run_id: str | None = None,
    snapshot_before_time: str | None = None,
    snapshot_after_time: str | None = None,
    project_root: str | None = None,
) -> dict:
    """生成符合 CHANGED_FILES_SCHEMA 的变更证明。

    Args:
        task_id: 关联的任务 ID
        before_snapshot: 变更前快照 {path: {sha256, size, tracked}}
        after_snapshot: 变更后快照 {path: {sha256, size, tracked}}
        run_id: 可选的 run_id
        snapshot_before_time: 变更前时间戳 (ISO 8601)
        snapshot_after_time: 变更后时间戳 (ISO 8601)
        project_root: 项目根目录路径

    Returns:
        符合 CHANGED_FILES_SCHEMA 的 dict
    """
    changes = diff_snapshots(before_snapshot, after_snapshot)

    # Compute summary
    summary = {
        'total_added': sum(1 for c in changes if c['change_type'] == 'added'),
        'total_modified': sum(1 for c in changes if c['change_type'] == 'modified'),
        'total_deleted': sum(1 for c in changes if c['change_type'] == 'deleted'),
        'total_renamed': sum(1 for c in changes if c['change_type'] == 'renamed'),
        'total_permission_changed': sum(1 for c in changes if c['change_type'] == 'permission_changed'),
        'total_changes': len(changes),
    }

    now = datetime.now(timezone.utc).isoformat()

    evidence = {
        'schema_version': '1.0.0',
        'task_id': task_id,
        'run_id': run_id,
        'snapshot_before': snapshot_before_time or now,
        'snapshot_after': snapshot_after_time or now,
        'changes': changes,
        'summary': summary,
        'metadata': {
            'generator': 'changed_files_utils.py v1.0.0',
            'generated_at': now,
            'project_root': project_root or str(REPO),
        },
    }

    return evidence


def validate_changed_files(data: dict, schema_path: str | Path | None = None) -> dict:
    """验证变更证明是否符合 CHANGED_FILES_SCHEMA。

    Args:
        data: 待验证的变更证明 dict
        schema_path: schema 文件路径（默认使用项目内置路径）

    Returns:
        {valid: bool, errors: list[str], warnings: list[str]}
    """
    errors = []
    warnings = []

    # Basic structure validation
    required_fields = ['schema_version', 'task_id', 'snapshot_before', 'snapshot_after', 'changes']
    for field in required_fields:
        if field not in data:
            errors.append(f'missing required field: {field}')

    if errors:
        return {'valid': False, 'errors': errors, 'warnings': warnings}

    # schema_version check
    if data['schema_version'] != '1.0.0':
        errors.append(f'unsupported schema_version: {data["schema_version"]} (expected 1.0.0)')

    # task_id non-empty
    if not data['task_id']:
        errors.append('task_id must not be empty')

    # Validate changes array
    valid_change_types = {'added', 'modified', 'deleted', 'renamed', 'permission_changed'}
    for i, change in enumerate(data['changes']):
        prefix = f'changes[{i}]'

        if 'path' not in change:
            errors.append(f'{prefix}: missing path')
        if 'change_type' not in change:
            errors.append(f'{prefix}: missing change_type')
            continue

        ct = change['change_type']
        if ct not in valid_change_types:
            errors.append(f'{prefix}: invalid change_type: {ct}')
            continue

        # added: sha256_before must be null
        if ct == 'added' and change.get('sha256_before') is not None:
            errors.append(f'{prefix}: added files must have sha256_before=null')

        # deleted: sha256_after must be null
        if ct == 'deleted' and change.get('sha256_after') is not None:
            errors.append(f'{prefix}: deleted files must have sha256_after=null')

        # renamed: rename_from required
        if ct == 'renamed' and not change.get('rename_from'):
            errors.append(f'{prefix}: renamed files must have rename_from')

        # Validate sha256 format (if present)
        for hash_field in ('sha256_before', 'sha256_after'):
            val = change.get(hash_field)
            if val is not None and not (isinstance(val, str) and len(val) == 64 and all(c in '0123456789abcdef' for c in val)):
                errors.append(f'{prefix}: {hash_field} must be 64-char hex string or null')

    # Validate summary if present
    if 'summary' in data:
        summary = data['summary']
        actual_summary = {
            'total_added': sum(1 for c in data['changes'] if c['change_type'] == 'added'),
            'total_modified': sum(1 for c in data['changes'] if c['change_type'] == 'modified'),
            'total_deleted': sum(1 for c in data['changes'] if c['change_type'] == 'deleted'),
            'total_renamed': sum(1 for c in data['changes'] if c['change_type'] == 'renamed'),
            'total_permission_changed': sum(1 for c in data['changes'] if c['change_type'] == 'permission_changed'),
        }
        for key, expected in actual_summary.items():
            if key in summary and summary[key] != expected:
                warnings.append(f'summary.{key} mismatch: declared {summary[key]}, actual {expected}')

        total_changes = sum(actual_summary.values())
        if 'total_changes' in summary and summary['total_changes'] != total_changes:
            warnings.append(f'summary.total_changes mismatch: declared {summary["total_changes"]}, actual {total_changes}')

    # Try jsonschema validation if available
    schema_file = Path(schema_path) if schema_path else DEFAULT_SCHEMA
    if schema_file.exists():
        try:
            import jsonschema
            schema = json.loads(schema_file.read_text(encoding='utf-8'))
            # Remove $schema to avoid meta-schema fetch
            schema.pop('$schema', None)
            schema.pop('$id', None)
            try:
                jsonschema.validate(data, schema)
            except jsonschema.ValidationError as e:
                errors.append(f'jsonschema validation failed: {e.message}')
        except ImportError:
            warnings.append('jsonschema library not available, skipping JSON Schema validation')

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
    }


def summarize_changes(data: dict) -> str:
    """生成人类可读的变更摘要。"""
    summary = data.get('summary', {})
    lines = [
        f"Changed Files Evidence for {data.get('task_id', 'UNKNOWN')}",
        f"  Run ID: {data.get('run_id', 'N/A')}",
        f"  Snapshot before: {data.get('snapshot_before', 'N/A')}",
        f"  Snapshot after: {data.get('snapshot_after', 'N/A')}",
        f"",
        f"  Summary:",
        f"    Added:                {summary.get('total_added', 0)}",
        f"    Modified:             {summary.get('total_modified', 0)}",
        f"    Deleted:              {summary.get('total_deleted', 0)}",
        f"    Renamed:              {summary.get('total_renamed', 0)}",
        f"    Permission changed:   {summary.get('total_permission_changed', 0)}",
        f"    Total:                {summary.get('total_changes', 0)}",
        f"",
    ]

    if data.get('changes'):
        lines.append("  Details:")
        for c in data['changes']:
            ct = c['change_type']
            path = c['path']
            if ct == 'added':
                lines.append(f"    [+] {path}")
            elif ct == 'deleted':
                lines.append(f"    [-] {path}")
            elif ct == 'modified':
                lines.append(f"    [M] {path}")
            elif ct == 'renamed':
                lines.append(f"    [R] {c.get('rename_from', '?')} -> {path}")
            elif ct == 'permission_changed':
                lines.append(f"    [P] {path} ({c.get('permission_before')} -> {c.get('permission_after')})")

    return '\n'.join(lines)


def load_snapshot_file(path: str | Path) -> dict:
    """加载快照文件（JSON 格式: {path: {sha256, size, tracked}}）。"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description='Changed Files Evidence Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # generate command
    gen_parser = subparsers.add_parser('generate', help='Generate changed files evidence')
    gen_parser.add_argument('--task-id', required=True, help='Task ID')
    gen_parser.add_argument('--before', required=True, help='Before snapshot JSON file')
    gen_parser.add_argument('--after', required=True, help='After snapshot JSON file')
    gen_parser.add_argument('--run-id', help='Optional run ID')
    gen_parser.add_argument('--output', required=True, help='Output JSON file')
    gen_parser.add_argument('--project-root', help='Project root directory')

    # validate command
    val_parser = subparsers.add_parser('validate', help='Validate changed files evidence')
    val_parser.add_argument('--input', required=True, help='Input JSON file to validate')
    val_parser.add_argument('--schema', help='Schema JSON file (default: project built-in)')

    # snapshot command
    snap_parser = subparsers.add_parser('snapshot', help='Take a file snapshot')
    snap_parser.add_argument('--dir', required=True, help='Directory to snapshot')
    snap_parser.add_argument('--output', required=True, help='Output snapshot JSON file')

    args = parser.parse_args()

    if args.command == 'generate':
        before = load_snapshot_file(args.before)
        after = load_snapshot_file(args.after)
        evidence = generate_changed_files_evidence(
            task_id=args.task_id,
            before_snapshot=before,
            after_snapshot=after,
            run_id=args.run_id,
            project_root=args.project_root,
        )
        Path(args.output).write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"Generated: {args.output}")
        print(summarize_changes(evidence))

    elif args.command == 'validate':
        data = json.loads(Path(args.input).read_text(encoding='utf-8'))
        result = validate_changed_files(data, args.schema)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result['valid'] else 1)

    elif args.command == 'snapshot':
        snapshot = take_snapshot(args.dir)
        Path(args.output).write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"Snapshot: {len(snapshot)} files -> {args.output}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
