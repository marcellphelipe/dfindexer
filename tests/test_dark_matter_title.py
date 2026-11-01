import unittest
from core.torrent_builder import disambiguate_dark_matter_2024 as fix
from core.torrent_processor import TorrentProcessor

class TitleTests(unittest.TestCase):
    def test_second_season_retains_release_year(self):
        self.assertEqual(fix('Dark.Matter.S02E02.2026.WEB-DL.1080p [Brazilian] [Eng]', 'Dark Matter', 'Matéria Escura', '2026', 'Matéria Escura S02E02'), 'Dark.Matter.2024.S02E02.2026.WEB-DL.1080p [Brazilian] [Eng]')
    def test_rede_season_alias(self):
        self.assertEqual(fix('Dark.Matter.S02E02.2024.WEB-DL.1080p', 'Dark Matter S02', 'Matéria Escura - 2ª Temporada', '2026', 'Dark Matter 2024 S02E02'), 'Dark.Matter.2024.S02E02.2024.WEB-DL.1080p')
    def test_multiple_episodes(self):
        self.assertEqual(fix('Dark.Matter.S01E01-02.2024.WEB-DL.1080p', 'Dark Matter S01', 'Matéria Escura - 1ª Temporada', '2024', ''), 'Dark.Matter.2024.S01E01-02.2024.WEB-DL.1080p')
    def test_season_pack(self):
        self.assertEqual(fix('Dark.Matter.S01.2024.1080p', 'Dark Matter', 'Matéria Escura', '2024', ''), 'Dark.Matter.2024.S01.2024.1080p')
    def test_does_not_relabel_old_or_unrelated_series(self):
        for original, translated, year, magnet in [('Dark Matter','Dark Matter','2015',''), ('Dark Matter','Matéria Escura','2015',''), ('Silo','Matéria Escura','2024',''), ('Dark Matter','Matéria Escura','2024','Dark Matter 2015 S01')]:
            title='Dark.Matter.S01E01.2015.720p'
            self.assertEqual(fix(title,original,translated,year,magnet), title)
    def test_finalization_restores_metadata_rewrite(self):
        torrent={'title_processed':'Dark.Matter.S02E02.2024.WEB-DL.1080p', 'original_title':'Dark Matter S02', 'title_translated_processed':'Matéria Escura - 2ª Temporada', 'year':'2026', 'magnet_original':'Dark.Matter.2024.S02E02', 'magnet_link':'magnet:?xt=urn:btih:'+'a'*40, 'info_hash':'a'*40, 'details':'https://example.com'}
        TorrentProcessor.remove_internal_fields([torrent])
        self.assertEqual(torrent['title'], 'Dark.Matter.2024.S02E02.2024.WEB-DL.1080p')
    def test_idempotent_and_films_unchanged(self):
        for title in ['Dark.Matter.2024.S01E01.1080p', 'Dark.Matter.2024.1080p']:
            self.assertEqual(fix(title,'Dark Matter','Matéria Escura','2024',''), title)
if __name__ == '__main__': unittest.main()
