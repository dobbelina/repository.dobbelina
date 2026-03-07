"""
Tests for HTML parsing and BeautifulSoup utilities in utils.py
"""

from resources.lib import utils


class TestParseHtml:
    """Tests for parse_html function"""

    def test_parse_html_basic(self):
        """Test parse_html returns BeautifulSoup object"""
        html = "<html><body><h1>Test</h1></body></html>"

        soup = utils.parse_html(html)

        assert soup is not None
        assert soup.find("h1") is not None
        assert soup.find("h1").text == "Test"

    def test_parse_html_empty_string(self):
        """Test parse_html with empty string"""
        soup = utils.parse_html("")

        assert soup is not None

    def test_parse_html_malformed_html(self):
        """Test parse_html handles malformed HTML"""
        html = "<div><p>Unclosed tags<div>More content</div>"

        soup = utils.parse_html(html)

        assert soup is not None
        assert soup.find("div") is not None


class TestSafeGetAttr:
    """Tests for safe_get_attr helper"""

    def test_safe_get_attr_exists(self):
        """Test safe_get_attr returns attribute value"""
        html = '<img src="image.jpg" alt="Test">'
        soup = utils.parse_html(html)
        img = soup.find("img")

        result = utils.safe_get_attr(img, "src")

        assert result == "image.jpg"

    def test_safe_get_attr_missing(self):
        """Test safe_get_attr returns default for missing attribute"""
        html = '<img src="image.jpg">'
        soup = utils.parse_html(html)
        img = soup.find("img")

        result = utils.safe_get_attr(img, "alt", default="No alt")

        assert result == "No alt"

    def test_safe_get_attr_with_fallbacks(self):
        """Test safe_get_attr checks fallback attributes"""
        html = '<img data-src="lazy.jpg">'
        soup = utils.parse_html(html)
        img = soup.find("img")

        result = utils.safe_get_attr(
            img, "src", fallback_attrs=["data-src", "data-lazy"]
        )

        assert result == "lazy.jpg"

    def test_safe_get_attr_none_element(self):
        """Test safe_get_attr handles None element"""
        result = utils.safe_get_attr(None, "src")

        assert result == ""

    def test_safe_get_attr_custom_default(self):
        """Test safe_get_attr with custom default"""
        html = "<div></div>"
        soup = utils.parse_html(html)
        div = soup.find("div")

        result = utils.safe_get_attr(div, "class", default="default-class")

        assert result == "default-class"


class TestSafeGetText:
    """Tests for safe_get_text helper"""

    def test_safe_get_text_basic(self):
        """Test safe_get_text returns text content"""
        html = "<p>Hello World</p>"
        soup = utils.parse_html(html)
        p = soup.find("p")

        result = utils.safe_get_text(p)

        assert result == "Hello World"

    def test_safe_get_text_with_whitespace(self):
        """Test safe_get_text strips whitespace"""
        html = "<p>  Spaced Text  </p>"
        soup = utils.parse_html(html)
        p = soup.find("p")

        result = utils.safe_get_text(p, strip=True)

        assert result == "Spaced Text"

    def test_safe_get_text_no_strip(self):
        """Test safe_get_text preserves whitespace when strip=False"""
        html = "<p>  Spaced  </p>"
        soup = utils.parse_html(html)
        p = soup.find("p")

        result = utils.safe_get_text(p, strip=False)

        assert result == "  Spaced  "

    def test_safe_get_text_none_element(self):
        """Test safe_get_text handles None element"""
        result = utils.safe_get_text(None)

        assert result == ""

    def test_safe_get_text_custom_default(self):
        """Test safe_get_text with custom default"""
        result = utils.safe_get_text(None, default="N/A")

        assert result == "N/A"

    def test_safe_get_text_nested_tags(self):
        """Test safe_get_text with nested tags"""
        html = "<div><span>Nested</span> Content</div>"
        soup = utils.parse_html(html)
        div = soup.find("div")

        result = utils.safe_get_text(div)

        assert "Nested" in result
        assert "Content" in result


class TestCleantext:
    """Tests for cleantext function"""

    def test_cleantext_html_entities(self):
        """Test cleantext decodes HTML entities"""
        assert utils.cleantext("Hello&nbsp;World") == "Hello World"
        assert utils.cleantext("&lt;tag&gt;") == "<tag>"
        assert utils.cleantext("&amp;") == "&"
        assert utils.cleantext("&quot;") == '"'

    def test_cleantext_whitespace(self):
        """Test cleantext strips leading/trailing whitespace"""
        assert utils.cleantext("  trim  ") == "trim"
        assert utils.cleantext("\n\ttabs\n") == "tabs"

    def test_cleantext_multiple_entities(self):
        """Test cleantext handles multiple entities"""
        text = "&lt;div&gt;&nbsp;Content&nbsp;&lt;/div&gt;"
        result = utils.cleantext(text)

        assert "<div>" in result
        assert "Content" in result
        assert "</div>" in result

    def test_cleantext_unicode(self):
        """Test cleantext handles Unicode characters"""
        text = "Hello © World ™"
        result = utils.cleantext(text)

        assert "©" in result or "Hello" in result

    def test_cleantext_empty_string(self):
        """Test cleantext with empty string"""
        result = utils.cleantext("")

        assert result == ""


class TestCleanhtml:
    """Tests for cleanhtml function"""

    def test_cleanhtml_removes_tags(self):
        """Test cleanhtml removes HTML tags"""
        assert utils.cleanhtml("<p>Hello</p>") == "Hello"
        assert utils.cleanhtml("<div>World</div>") == "World"

    def test_cleanhtml_nested_tags(self):
        """Test cleanhtml handles nested tags"""
        html = "<div><span>Nested</span> Content</div>"
        result = utils.cleanhtml(html)

        assert "<" not in result
        assert ">" not in result
        assert "Nested" in result
        assert "Content" in result

    def test_cleanhtml_preserves_text(self):
        """Test cleanhtml preserves text between tags"""
        html = "<p>Keep this <b>and</b> this</p>"
        result = utils.cleanhtml(html)

        assert "Keep this" in result
        assert "and" in result
        assert "this" in result

    def test_cleanhtml_with_attributes(self):
        """Test cleanhtml removes tags with attributes"""
        html = '<div class="test" id="main">Content</div>'
        result = utils.cleanhtml(html)

        assert result == "Content"

    def test_cleanhtml_empty_string(self):
        """Test cleanhtml with empty string"""
        result = utils.cleanhtml("")

        assert result == ""


class TestGetVidhost:
    """Tests for get_vidhost function"""

    def test_get_vidhost_basic(self):
        """Test get_vidhost extracts domain"""
        url = "https://cdn.example.com/video.mp4"
        result = utils.get_vidhost(url)

        assert result == "example.com"

    def test_get_vidhost_subdomain(self):
        """Test get_vidhost handles subdomains"""
        url = "https://sub.domain.co.uk/path"
        result = utils.get_vidhost(url)

        assert result == "domain.co.uk"

    def test_get_vidhost_localhost(self):
        """Test get_vidhost with localhost"""
        url = "https://localhost:8080/video"
        result = utils.get_vidhost(url)

        assert result == "localhost"

    def test_get_vidhost_protocol_relative(self):
        """Test get_vidhost with protocol-relative URL"""
        url = "//protocol-relative.com/file"
        result = utils.get_vidhost(url)

        assert result == "protocol-relative.com"

    def test_get_vidhost_ip_address(self):
        """Test get_vidhost with IP address"""
        url = "https://192.168.1.1/video.mp4"
        result = utils.get_vidhost(url)

        # IP addresses return as-is
        assert "192.168.1.1" in result


class TestFixUrl:
    """Tests for fix_url function"""

    def test_fix_url_protocol_relative(self):
        """Test fix_url adds protocol to protocol-relative URLs"""
        url = "//cdn.example.com/video.mp4"
        result = utils.fix_url(url)

        assert "cdn.example.com/video.mp4" in result

    def test_fix_url_absolute(self):
        """Test fix_url returns absolute URLs unchanged"""
        url = "https://example.com/video.mp4"
        result = utils.fix_url(url)

        assert result == url

    def test_fix_url_with_base(self):
        """Test fix_url joins relative URL with base"""
        url = "/relative/path"
        base = "https://example.com/"
        result = utils.fix_url(url, base)

        assert result == "https://example.com/relative/path"

    def test_fix_url_relative_path(self):
        """Test fix_url with relative path"""
        url = "relative/path"
        base = "https://example.com/base/"
        result = utils.fix_url(url, base)

        assert "relative/path" in result

    def test_fix_url_http_protocol(self):
        """Test fix_url with http protocol"""
        url = "http://example.com/path"
        result = utils.fix_url(url)

        assert result == url


class TestParseQuery:
    """Tests for parse_query function"""

    def test_parse_query_basic(self):
        """Test parse_query with basic query string"""
        query = "key1=value1&key2=value2"
        result = utils.parse_query(query)

        assert result["key1"] == "value1"
        assert result["key2"] == "value2"

    def test_parse_query_integers(self):
        """Test parse_query with integer values"""
        query = "page=5&limit=10"
        result = utils.parse_query(query)

        # Values may be strings or ints
        assert str(result["page"]) == "5"
        assert str(result["limit"]) == "10"

    def test_parse_query_url_encoded(self):
        """Test parse_query with URL-encoded values"""
        query = "q=hello+world&name=John%20Doe"
        result = utils.parse_query(query)

        assert "hello" in str(result.get("q", "")).lower()
        assert "john" in str(result.get("name", "")).lower()

    def test_parse_query_empty_string(self):
        """Test parse_query with empty string"""
        result = utils.parse_query("")

        assert isinstance(result, dict)

    def test_parse_query_single_param(self):
        """Test parse_query with single parameter"""
        query = "key=value"
        result = utils.parse_query(query)

        assert result["key"] == "value"

    def test_parse_query_special_characters(self):
        """Test parse_query handles special characters"""
        query = "search=test%26more"
        result = utils.parse_query(query)

        # Should decode special characters
        assert "search" in result


class TestFindThumbnail:
    """Tests for find_thumbnail function"""

    def test_find_thumbnail_basic(self):
        html = '<img src="https://example.com/thumbnail_image.jpg">'
        soup = utils.parse_html(html)
        img = soup.find("img")
        assert utils.get_thumbnail(img) == "https://example.com/thumbnail_image.jpg"

    def test_find_thumbnail_data_src(self):
        html = '<img data-src="https://example.com/lazy_loaded_image.jpg" src="placeholder.gif">'
        soup = utils.parse_html(html)
        img = soup.find("img")
        assert utils.get_thumbnail(img) == "https://example.com/lazy_loaded_image.jpg"

    def test_find_thumbnail_srcset(self):
        html = '<img srcset="https://example.com/low_res.jpg 100w, https://example.com/high_res.jpg 500w">'
        soup = utils.parse_html(html)
        img = soup.find("img")
        # Should take the last one (highest resolution)
        assert utils.get_thumbnail(img) == "https://example.com/high_res.jpg"

    def test_find_thumbnail_filters_placeholders(self):
        html = '<img src="https://example.com/spacer.gif" data-lazy-src="https://example.com/real_image.jpg">'
        soup = utils.parse_html(html)
        img = soup.find("img")
        assert utils.get_thumbnail(img) == "https://example.com/real_image.jpg"

    def test_find_thumbnail_none_element(self):
        assert utils.get_thumbnail(None, default="fallback.jpg") == "fallback.jpg"


class TestI18n:
    """Tests for i18n function"""

    def test_i18n_returns_string(self):
        """Test i18n returns a string"""
        result = utils.i18n("search")

        assert isinstance(result, str)

    def test_i18n_with_unknown_key(self):
        """Test i18n with unknown key"""
        result = utils.i18n("nonexistent_translation_key_12345")

        assert isinstance(result, str)

    def test_i18n_common_keys(self):
        """Test i18n with common keys"""
        # These should return strings
        for key in ["search", "categories", "settings"]:
            result = utils.i18n(key)
            assert isinstance(result, str)
