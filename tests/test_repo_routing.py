import json, pytest
from pathlib import Path

SCHEMA = Path(__file__).resolve().parent.parent / 'schemas' / 'SUBMISSION_TARGET.schema.json'

def test_schema_loads():
    data = json.loads(SCHEMA.read_text(encoding='utf-8'))
    assert data['title'] == 'SubmissionTarget'

def test_valid_minimal_target():
    from jsonschema import validate
    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    target = {
        'task_id': 'test-001',
        'primary_repo': 'agent-acceptance',
        'repos': {
            'agent-acceptance': {'allowed': ['schemas/','contracts/'], 'blocked': ['runs/'], 'commit_required': True}
        },
        'evidence_binding': {'git_tree_sha_per_repo': True, 'gpt_accepted_binds_all_repos': True}
    }
    validate(target, schema)

def test_missing_primary_repo_fails():
    from jsonschema import validate, ValidationError
    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    target = {'task_id': 'test-002', 'repos': {}}
    with pytest.raises(ValidationError):
        validate(target, schema)

def test_invalid_primary_repo_fails():
    from jsonschema import validate, ValidationError
    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    target = {'task_id': 'test-003', 'primary_repo': 'nonexistent', 'repos': {}}
    with pytest.raises(ValidationError):
        validate(target, schema)
