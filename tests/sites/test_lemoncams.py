"""Tests for LemonCams pagination and playback routing."""

from resources.lib.sites import lemoncams


def test_list_uses_real_pagination_and_adds_next_page(monkeypatch):
    added_links = []
    added_dirs = []

    def fake_api_get(params):
        assert params["function"] == "cams"
        assert params["provider"] == "stripchat"
        assert params["page"] == "1"
        return {
            "cams": [
                {
                    "username": "model1",
                    "provider": "stripchat",
                    "title": "test title",
                    "numberOfUsers": 12,
                    "imageUrl": "https://img.example/model1.jpg",
                }
            ],
            "maxPage": 3,
        }

    monkeypatch.setattr(lemoncams, "_api_get", fake_api_get)
    monkeypatch.setattr(
        lemoncams.site,
        "add_download_link",
        lambda name, url, mode, iconimage, desc, **kwargs: added_links.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
            }
        ),
    )
    monkeypatch.setattr(
        lemoncams.site,
        "add_dir",
        lambda name, url, mode, iconimage="", page=None, **kwargs: added_dirs.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "page": page,
            }
        ),
    )
    monkeypatch.setattr(lemoncams.utils, "eod", lambda: None)

    lemoncams.List("stripchat", page=1)

    assert added_links == [
        {
            "name": "model1 - test title",
            "url": "https://www.lemoncams.com/stripchat/model1",
            "mode": "Playvid",
        }
    ]
    assert added_dirs == [
        {
            "name": "Next Page (2/3)",
            "url": "stripchat",
            "mode": "List",
            "page": 2,
        }
    ]


def test_stripchat_folder_filters_non_stripchat_entries(monkeypatch):
    added_links = []
    added_dirs = []

    def fake_api_get(params):
        assert params["provider"] == "stripchat"
        return {
            "cams": [
                {
                    "username": "strip1",
                    "provider": "stripchat",
                    "title": "good",
                    "numberOfUsers": 12,
                },
                {
                    "username": "wrong1",
                    "provider": "bongacams",
                    "title": "should not appear",
                    "numberOfUsers": 99,
                },
            ],
            "maxPage": 5,
        }

    monkeypatch.setattr(lemoncams, "_api_get", fake_api_get)
    monkeypatch.setattr(
        lemoncams.site,
        "add_download_link",
        lambda name, url, mode, iconimage, desc, **kwargs: added_links.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
            }
        ),
    )
    monkeypatch.setattr(
        lemoncams.site,
        "add_dir",
        lambda name, url, mode, iconimage="", page=None, **kwargs: added_dirs.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "page": page,
            }
        ),
    )
    monkeypatch.setattr(lemoncams.utils, "eod", lambda: None)

    lemoncams.List("stripchat", page=2)

    assert added_links == [
        {
            "name": "strip1 - good",
            "url": "https://www.lemoncams.com/stripchat/strip1",
            "mode": "Playvid",
        }
    ]
    assert added_dirs == [
        {
            "name": "Next Page (3/5)",
            "url": "stripchat",
            "mode": "List",
            "page": 3,
        }
    ]


def test_playvid_routes_stripchat_models_through_stripchat_site(monkeypatch):
    calls = []

    from resources.lib.sites import stripchat

    monkeypatch.setattr(
        stripchat,
        "Playvid",
        lambda url, name: calls.append({"url": url, "name": name}),
    )

    lemoncams.Playvid("https://www.lemoncams.com/stripchat/miamellycious", "ignored")

    assert calls == [
        {
            "url": "https://stripchat.com/miamellycious",
            "name": "miamellycious",
        }
    ]
