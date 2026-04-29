from pathlib import Path


def test_model_provider_not_referenced():
    root = Path('server/app')
    for path in root.rglob('*.py'):
        assert 'MODEL_PROVIDER' not in path.read_text()
