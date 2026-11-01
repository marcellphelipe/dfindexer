import hashlib
import unittest
from unittest.mock import patch, Mock
from concurrent.futures import ThreadPoolExecutor
from tracker.service import TrackerService
from magnet.parser import parse_bencode_size
from core.enrichment import apply_size_fallback

class IntegrityTests(unittest.TestCase):
    def test_single_file_and_hash(self):
        info=b'd6:lengthi1234567e4:name5:a.mkve'
        data=b'd4:info'+info+b'e'
        self.assertEqual(parse_bencode_size(data,hashlib.sha1(info).hexdigest()),1234567)
        self.assertIsNone(parse_bencode_size(data,'0'*40))
    def test_multifile_sums_and_ignores_unrelated_length(self):
        info=b'd5:filesld6:lengthi45e4:pathl5:a.txteed6:lengthi123456789e4:pathl5:b.mkveee4:name4:teste'
        data=b'd4:info'+info+b'e'
        self.assertEqual(parse_bencode_size(data,hashlib.sha1(info).hexdigest()),123456834)
        self.assertIsNone(parse_bencode_size(data[:-4]))
    @patch('cache.store.MetadataCache')
    def test_verified_metadata_cache_is_used_even_when_fetch_was_skipped(self, cache_class):
        cache_class.return_value.get.return_value = {'size': 4694831036}
        torrent={'info_hash':'a'*40,'magnet_link':'magnet:?xt=urn:btih:'+'a'*40,'size':'untrusted'}
        apply_size_fallback([torrent],cross_data_by_hash={'a'*40:{'size':'wrong'}})
        self.assertEqual(torrent['size'],'4.37 GB')
    def test_size_does_not_trust_cache_or_html_and_uses_metadata(self):
        ts=[{'info_hash':'a'*40,'magnet_link':'magnet:?xt=urn:btih:'+'a'*40,'size':'45 B'}, {'info_hash':'b'*40,'magnet_link':'magnet:?xt=urn:btih:'+'b'*40,'_metadata':{'size':1073741824}}]
        apply_size_fallback(ts,cross_data_by_hash={'a'*40:{'size':'9 GB'}})
        self.assertEqual(ts[0]['size'],'')
        self.assertEqual(ts[1]['size'],'1.00 GB')
class TrackerTests(unittest.TestCase):
    def test_failed_tracker_is_unknown_and_real_zero_is_preserved(self):
        service = TrackerService.__new__(TrackerService)
        service._executor = ThreadPoolExecutor(max_workers=2)
        service._list_provider = Mock()
        service._list_provider.get_trackers.return_value = []
        service._get_cached = Mock(return_value=None)
        service._store_cache = Mock()
        service._scrape_info_hash = Mock(side_effect=lambda h, *_: None if h == 'a' else (0, 0))
        try:
            self.assertEqual(service.get_peers_bulk({'a': [], 'b': []}), {'b': (0, 0)})
        finally:
            service._executor.shutdown()

if __name__=='__main__': unittest.main()
