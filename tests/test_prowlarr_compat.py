import unittest
from unittest.mock import patch
from flask import Flask
from api.handlers import register_routes

class ProwlarrCompatTests(unittest.TestCase):
    def test_null_counts_only_mapped_for_prowlarr(self):
        app=Flask(__name__); register_routes(app)
        result={'title':'Silo.S01E01','magnet_link':'magnet:?xt=urn:btih:'+'a'*40,'info_hash':'a'*40,'details':'https://example.test','seed_count':None,'leech_count':None}
        with patch('api.handlers._run_single_scraper',return_value=([result], None)):
            with app.test_client() as c:
                raw=c.get('/indexers/starck?q=Silo').get_json()['results'][0]
                compat=c.get('/indexers/starck?q=Silo&prowlarr_compat=true').get_json()['results'][0]
        self.assertIsNone(raw['seed_count']);self.assertIsNone(result['seed_count'])
        self.assertEqual(compat['seed_count'],0);self.assertEqual(compat['leech_count'],0)
if __name__=='__main__':unittest.main()
