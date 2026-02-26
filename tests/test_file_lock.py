"""tests for scripts/file_lock.py"""
import json, pathlib, tempfile, os, sys

# Ensure scripts/ is importable
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'scripts'))

from file_lock import atomic_json_read, atomic_json_write, atomic_json_update


def test_write_and_read(tmp_path):
    p = tmp_path / 'test.json'
    data = {'hello': 'world', 'n': 42}
    atomic_json_write(p, data)
    assert p.exists()
    result = atomic_json_read(p, {})
    assert result == data


def test_read_missing_returns_default(tmp_path):
    p = tmp_path / 'nope.json'
    assert atomic_json_read(p, {'default': True}) == {'default': True}


def test_update_modifies_data(tmp_path):
    p = tmp_path / 'counter.json'
    atomic_json_write(p, {'count': 0})

    def increment(data):
        data['count'] += 1
        return data

    atomic_json_update(p, increment, {})
    assert atomic_json_read(p, {})['count'] == 1

    atomic_json_update(p, increment, {})
    assert atomic_json_read(p, {})['count'] == 2


def test_update_creates_file(tmp_path):
    p = tmp_path / 'new.json'

    def init(data):
        data['created'] = True
        return data

    atomic_json_update(p, init, {})
    assert atomic_json_read(p, {}) == {'created': True}


def test_write_atomic_no_partial(tmp_path):
    """Write should not leave partial content on disk."""
    p = tmp_path / 'atomic.json'
    big = {'items': list(range(1000))}
    atomic_json_write(p, big)
    result = json.loads(p.read_text())
    assert len(result['items']) == 1000


def test_unicode_roundtrip(tmp_path):
    p = tmp_path / 'unicode.json'
    data = {'name': '户部尚书', 'emoji': '🏛️'}
    atomic_json_write(p, data)
    result = atomic_json_read(p, {})
    assert result['name'] == '户部尚书'
    assert result['emoji'] == '🏛️'
