from core.torrent_processor import QueryFilter


def _t(title, year='', original=''):
    return {'title_processed': title, 'original_title': original, 'year': year}


def test_rejects_same_name_other_year():
    f = QueryFilter.create_filter('Resident Evil 2026')
    assert not f(_t('Resident.Evil.Welcome.To.Raccoon.City.2021.WEB-DL.1080p', '2021'))
    assert not f(_t('Resident Evil Death Island 2023 WEB-DL 1080p', '2023'))
    assert not f(_t('Resident Evil 4 Remake 2023 WEB-DL', ''))


def test_accepts_matching_or_unknown_year():
    f = QueryFilter.create_filter('Resident Evil 2026')
    assert f(_t('Resident.Evil.2026.WEB-DL.1080p', '2026'))
    assert f(_t('Resident.Evil.WEB-DL.1080p', ''))
    assert f(_t('Resident Evil 2025 WEB-DL', '2025'))  # ±1 tolerance


def test_query_without_year_unaffected():
    f = QueryFilter.create_filter('Resident Evil')
    assert f(_t('Resident.Evil.Welcome.To.Raccoon.City.2021.WEB-DL.1080p', '2021'))
