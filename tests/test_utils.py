from resources.lib import utils
from tests.conftest import read_fixture


def test_parse_html_and_safe_get_attr_handles_fallbacks():
    soup = utils.parse_html(read_fixture('sample_listing.html'))
    anchors = soup.select('a.video-link')
    assert len(anchors) == 2

    first_img = anchors[0].select_one('img')
    # src attribute missing, should fall back to data-src
    thumbnail = utils.safe_get_attr(first_img, 'src', ['data-src'])
    assert thumbnail == '//cdn.example.com/thumb-alpha.jpg'

    second_img = anchors[1].select_one('img')
    # src attribute present, primary lookup should succeed
    assert utils.safe_get_attr(second_img, 'src', ['data-src']) == '//cdn.example.com/thumb-beta.jpg'


def test_safe_get_text_strips_whitespace():
    soup = utils.parse_html(read_fixture('sample_listing.html'))
    anchor = soup.select_one('a.video-link:last-of-type')
    assert utils.safe_get_text(anchor) == 'Beta Video'


def test_safe_get_helpers_return_defaults_when_missing():
    assert utils.safe_get_attr(None, 'href', ['data-href'], default='missing') == 'missing'
    assert utils.safe_get_text(None, default='missing') == 'missing'
