"""Static pytest filename candidates, never collection or safe-skip proof."""
from pathlib import PurePosixPath


def is_test_file(path):
    """Pytest defaults: test_*.py and *_test.py. Helpers/conftest are not tests."""
    name = PurePosixPath(path).name
    return name.endswith('.py') and (name.startswith('test_') or name.endswith('_test.py'))


def selection_receipt(paths, deleted_paths=()):
    candidates = sorted({p for p in paths if is_test_file(p)})
    deleted = set(deleted_paths)
    return {'candidate_test_files': candidates,
            'runnable_candidate_test_files': [p for p in candidates if p not in deleted],
            'deleted_candidate_test_files': [p for p in candidates if p in deleted],
            'classification_basis': 'PYTEST_DEFAULT_FILENAME_PATTERNS_NOT_COLLECTED',
            'custom_collection': 'UNKNOWN', 'safe_to_skip_other_tests': False}
