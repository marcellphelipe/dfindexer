import unittest
from cache.store import metadata_key
from core.enrichment import parse_cross_data
from scraper.torrentclaw import TorrentclawScraper

class CacheMigrationTests(unittest.TestCase):
    def test_metadata_uses_new_namespace(self):
        self.assertEqual(metadata_key('ABCD'), 'metadata:verified-v2:abcd')
    def test_new_tracker_fields_preserve_zero_and_unknown(self):
        parsed = parse_cross_data({b'tracker_seed_v2': b'0', b'tracker_leech_v2': b'invalid'})
        self.assertEqual(parsed['tracker_seed_v2'], 0)
        self.assertIsNone(parsed['tracker_leech_v2'])
    def test_legacy_tracker_fields_are_not_used_as_verified_counts(self):
        parsed = parse_cross_data({b'tracker_seed': b'0', b'tracker_leech': b'0'})
        self.assertNotIn('tracker_seed_v2', parsed)
        self.assertNotIn('tracker_leech_v2', parsed)
class TorrentclawTests(unittest.TestCase):
    def test_missing_seed_count_can_be_sorted(self):
        scraper = TorrentclawScraper.__new__(TorrentclawScraper)
        scraper._active_search_query = ''
        items = [{'has_pt_br_audio': True, 'seeders': None}, {'has_pt_br_audio': True, 'seeders': 2}]
        result = scraper._filter_items_by_query(items)
        self.assertEqual([v['seeders'] for v in result], [2, None])

if __name__ == '__main__': unittest.main()
