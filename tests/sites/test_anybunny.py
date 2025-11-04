from resources.lib.sites import anybunny
from tests.conftest import read_fixture


def test_list_populates_download_links(monkeypatch):
    html = read_fixture('anybunny_list.html')
    captured_downloads = []
    captured_dirs = []

    def fake_get_html(url, headers):
        return html

    def capture_download(name, url, mode, iconimage, desc='', *args, **kwargs):
        captured_downloads.append({
            'name': name,
            'url': url,
            'mode': anybunny.site.get_full_mode(mode),
            'icon': iconimage,
        })

    def capture_dir(name, url, mode, *args, **kwargs):
        captured_dirs.append({
            'name': name,
            'url': url,
            'mode': anybunny.site.get_full_mode(mode),
        })

    monkeypatch.setattr(anybunny.utils, 'getHtml', fake_get_html)
    monkeypatch.setattr(anybunny.site, 'add_download_link', capture_download)
    monkeypatch.setattr(anybunny.site, 'add_dir', capture_dir)
    monkeypatch.setattr(anybunny.utils, 'eod', lambda *args, **kwargs: None)

    anybunny.List('http://anybunny.org/new/?p=1')

    assert captured_downloads == [
        {
            'name': 'First Video Title',
            'url': 'http://anybunny.org/videos/first-video',
            'mode': 'anybunny.Playvid',
            'icon': '//cdn.anybunny.org/thumb-first.jpg',
        },
        {
            'name': 'Second Video Title',
            'url': 'http://anybunny.org/videos/second-video',
            'mode': 'anybunny.Playvid',
            'icon': '//cdn.anybunny.org/thumb-second.jpg',
        },
    ]

    assert captured_dirs == [
        {
            'name': 'Next Page',
            'url': 'http://anybunny.org/new/?p=2',
            'mode': 'anybunny.List',
        }
    ]
