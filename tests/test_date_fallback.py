from core.enrichment import apply_date_fallback

def test_newer_torrent_creation_beats_old_catalog_date():
    t = {'date': '2026-02-11T00:00:00Z', '_metadata': {'creation_date': 1793000000}}  # 2026-10-26
    apply_date_fallback([t])
    assert t['date'].startswith('2026-10-2')

def test_keeps_page_date_when_torrent_older_or_missing():
    t = {'date': '2026-02-11T00:00:00Z', '_metadata': {'creation_date': 1700000000}}
    apply_date_fallback([t])
    assert t['date'] == '2026-02-11T00:00:00Z'
    t2 = {'date': '2026-02-11T00:00:00Z'}
    apply_date_fallback([t2])
    assert t2['date'] == '2026-02-11T00:00:00Z'

def test_no_date_uses_creation():
    t = {'date': '', '_metadata': {'creation_date': 1793000000}}
    apply_date_fallback([t])
    assert t['date'].startswith('2026-10-2')


def test_creation_date_from_cross_data(monkeypatch):
    import core.enrichment as e
    monkeypatch.setattr(e, 'bulk_get_cross_data', lambda hashes: {'a' * 40: {'creation_date': '1793000000'}})
    t = {'date': '2026-02-11T00:00:00Z', 'info_hash': 'a' * 40}
    e.apply_date_fallback([t])
    assert t['date'].startswith('2026-10-2')
