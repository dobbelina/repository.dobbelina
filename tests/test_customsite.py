from resources.lib import customsite


def test_customsite_lazy_loads_and_exposes_fields(monkeypatch):
    calls = []
    image_calls = []

    def fake_get_custom_data(author, name):
        calls.append((author, name))
        return ("My Title", "thumb.png", "About text", "https://example.com")

    def fake_cum_image(filename, custom=False):
        image_calls.append((filename, custom))
        return f"converted:{filename}:{custom}"

    monkeypatch.setattr(customsite, "get_custom_data", fake_get_custom_data)
    monkeypatch.setattr(customsite.basics, "cum_image", fake_cum_image)

    site = customsite.CustomSite(author="author1", name="site1", webcam=True)
    assert site.testing is False

    # First property access triggers a single database load
    assert site.title == "My Title[COLOR white] - webcams[/COLOR]"
    assert site.image == "converted:thumb.png:True"
    assert site.about == "About text"
    assert site.url == "https://example.com"

    # Subsequent accesses reuse cached data
    assert site.title.startswith("My Title")
    assert calls == [("author1", "site1")]
    assert image_calls == [("thumb.png", True)]
