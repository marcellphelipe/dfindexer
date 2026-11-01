import unittest
from unittest.mock import patch
from flask import Flask
from api.episode_filter import episode_request, matches_episode
from api.handlers import register_routes


class EpisodeFilterTests(unittest.TestCase):
    def test_release_variants(self):
        cases = {
            'Dark.Matter.2024.S02E01.1080p': True,
            'Dark.Matter.S02E02': False,
            'Dark.Matter.S01E01': False,
            'Dark.Matter.S02E01E02': True,
            'Dark.Matter.S02E01-02': True,
            'Dark.Matter.S02E01-E02': True,
            'Dark.Matter.2x01': True,
            'Dark.Matter.S02.Completa': True,
            'Dark.Matter.Temporada 2 Completa': True,
            'Dark.Matter.S01.Completa': False,
            'Dark.Matter.Sem identificação': True,
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(matches_episode(title, 2, 1), expected)
        for title in ('Show.S02E01E02', 'Show.S02E01-02', 'Show.S02E01-E02'):
            self.assertTrue(matches_episode(title, 2, 2), title)
            self.assertFalse(matches_episode(title, 2, 3), title)

    def test_ambiguous_queries_do_not_filter(self):
        self.assertIsNone(episode_request('2', '', 'show S02'))
        self.assertIsNone(episode_request('2', '2024-01-01', 'show'))
        self.assertEqual(episode_request('2', '1', ''), (2, 1))
        self.assertEqual(episode_request('', '', 'show S02E01'), (2, 1))
        self.assertIsNone(episode_request('', '', 'show S02E01-02'))

    def test_endpoint_filter_and_regular_search(self):
        app = Flask(__name__)
        register_routes(app)
        def result(title, char):
            return {'title': title, 'magnet_link': 'magnet:?xt=urn:btih:' + char * 40,
                    'info_hash': char * 40, 'details': 'https://example.test',
                    'seed_count': 1, 'leech_count': 1}
        results = [result('Show.S02E01', 'a'), result('Show.S02E02', 'b'),
                   result('Show.S02E01-02', 'c'), result('Show.S02.Completa', 'd')]
        with patch('api.handlers._run_single_scraper', return_value=(results, None)):
            with app.test_client() as client:
                response = client.get('/indexers/starck?q=show&season=2&ep=1').get_json()
                self.assertEqual([x['title'] for x in response['results']], [results[i]['title'] for i in (0, 2, 3)])
                self.assertEqual(client.get('/indexers/starck?q=show').get_json()['count'], 4)

if __name__ == '__main__':
    unittest.main()
