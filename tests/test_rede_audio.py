from bs4 import BeautifulSoup

from scraper.rede import RedeScraper, audio_from_download_label

_H = 'a' * 40


def _magnet(h, dn):
    return f'magnet:?xt=urn:btih:{h}&dn={dn}'


ROWS = [
    ('DOWNLOAD TORRENT DUBLADO DUAL AUDIO 5.1 MKV WEB-DL 1080P', '1' * 40,
     'BAIXARAPIDO.COM-.WEB-DL.1080P.MKV.5.1.-DUBLADO-DUAL-AUDIO-.A+Odisseia.2026.1080p.WEB-DL.x264.DUAL.5.1'),
    ('DOWNLOAD TORRENT DUBLADO 5.1 MKV WEB-DL 1080P (ÁUDIO 10 E VÍDEO 09)', '2' * 40,
     'BAIXARAPIDO.COM-.WEB-DL.1080P.MKV.5.1.-DUBLADO-.The.Odyssey.2026.1080p.WEBRip.Dublado.mkv'),
    ('DOWNLOAD TORRENT LEGENDADO 5.1 MKV WEB-DL 1080P', '3' * 40,
     'BAIXARAPIDO.COM-.WEB-DL.1080P.MKV.5.1.-LEGENDADO-.The+Odyssey+(2026)+[1080p]+[YTS.GG]'),
]

PAGE = f'''<html><body>
<h1 class="movie-title">A Odisseia Torrent (2026)</h1>
<p class="original-title">The Odyssey</p>
<time itemprop="datePublished" datetime="2026">2026</time>
<div class="spec-card-glass"><small>Idioma / Áudio</small><strong>Português / Inglês</strong></div>
<section class="download-section"><div class="download-list">
{''.join(f'<div class="download-row"><div class="download-name">{label}</div>'
         f'<a class="download-btn" href="{_magnet(h, dn)}">Download</a></div>' for label, h, dn in ROWS)}
</div></section></body></html>'''


def test_label_classification():
    assert audio_from_download_label('DOWNLOAD TORRENT DUBLADO DUAL AUDIO 5.1') == 'dual'
    assert audio_from_download_label('DOWNLOAD TORRENT DUBLADO 5.1 MKV') == 'português'
    assert audio_from_download_label('DOWNLOAD TORRENT LEGENDADO 5.1 MKV') == 'inglês'
    assert audio_from_download_label('DOWNLOAD TORRENT 1080P') is None
    assert audio_from_download_label('', _magnet(_H, 'X.-LEGENDADO-.The.Movie')) == 'inglês'


def _scrape(monkeypatch):
    scraper = RedeScraper.__new__(RedeScraper)
    scraper.base_url = 'https://redestorrents.com/'
    scraper._skip_metadata = True
    monkeypatch.setattr(scraper, 'get_document', lambda *a, **k: BeautifulSoup(PAGE, 'html.parser'), raising=False)
    monkeypatch.setattr(scraper, '_should_skip_page_by_query', lambda *a, **k: False, raising=False)
    monkeypatch.setattr(scraper, '_resolve_link', lambda href: href, raising=False)
    return {t['info_hash']: t['title_processed'] for t in scraper._get_torrents_from_page('a-odisseia/')}


def test_each_magnet_uses_its_own_audio_label(monkeypatch):
    titles = _scrape(monkeypatch)
    dual, dublado, legendado = titles['1' * 40], titles['2' * 40], titles['3' * 40]
    assert '[Brazilian]' in dual and '[Eng]' in dual
    assert '[Brazilian]' in dublado and '[Eng]' not in dublado
    assert '[Brazilian]' not in legendado and '[Eng]' in legendado
