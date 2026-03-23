from scripts import live_smoke_test


def test_default_site_profile_exposes_all_core_steps():
    profile = live_smoke_test.get_site_profile("nonexistent-site")

    assert profile["supports"]["main"] is True
    assert profile["supports"]["list"] is True
    assert profile["supports"]["categories"] is True
    assert profile["supports"]["search"] is True
    assert profile["supports"]["play"] is True
    assert profile["content_type"] == "video"


def test_site_profile_merges_site_specific_overrides():
    profile = live_smoke_test.get_site_profile("chaturbate")

    assert profile["content_type"] == "cam"
    assert profile["supports"]["main"] is True
    assert profile["supports"]["categories"] is False
    assert profile["supports"]["play"] is False
    assert profile["harness"]["playback_not_testable"] is True
    assert profile["harness"]["search_results_optional"] is True


def test_requires_flaresolverr_flag_is_present_for_seeded_sites():
    profile = live_smoke_test.get_site_profile("missav")

    assert profile["requires_flaresolverr"] is True
