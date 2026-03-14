"""
Tests for adultsite.py
Testing the AdultSite base class
"""

import pytest


@pytest.fixture(autouse=True)
def clear_adultsite_instances():
    """Clear AdultSite instances before each test"""
    from resources.lib.adultsite import AdultSite

    AdultSite.instances.clear()
    AdultSite.clean_functions.clear()
    yield
    AdultSite.instances.clear()
    AdultSite.clean_functions.clear()


class TestAdultSiteInit:
    """Test AdultSite initialization"""

    def test_init_with_basic_params(self):
        """Test initialization with basic parameters"""
        from resources.lib.adultsite import AdultSite

        site = AdultSite("testsite", "Test Site", "https://test.com/")

        assert site.name == "testsite"
        assert "Test Site" in site.title
        assert site.url == "https://test.com/"
        assert not site.webcam
        assert not site.custom
        assert site.default_mode == ""

    def test_init_with_image(self):
        """Test initialization with custom image"""
        from resources.lib.adultsite import AdultSite

        site = AdultSite(
            "testsite", "Test Site", "https://test.com/", image="custom.png"
        )

        assert site.image is not None
        assert "custom.png" in site.image

    def test_init_with_webcam_true(self):
        """Test initialization with webcam=True adds webcam text"""
        from resources.lib.adultsite import AdultSite

        site = AdultSite("camsite", "Cam Site", "https://cam.com/", webcam=True)

        assert "webcams" in site.title
        assert site.webcam

    def test_init_with_about(self):
        """Test initialization with about parameter"""
        from resources.lib.adultsite import AdultSite

        site = AdultSite(
            "testsite", "Test Site", "https://test.com/", about="test_about"
        )

        assert site.about == "test_about"

    def test_init_adds_to_instances(self):
        """Test that initialization adds site to instances WeakSet"""
        from resources.lib.adultsite import AdultSite

        site = AdultSite("testsite", "Test Site", "https://test.com/")

        assert site in AdultSite.instances

    def test_init_inherits_url_dispatcher(self):
        """Test that AdultSite inherits from URL_Dispatcher"""
        from resources.lib.adultsite import AdultSite

        site = AdultSite("testsite", "Test Site", "https://test.com/")

        assert hasattr(site, "module_name")
        assert site.module_name == "testsite"
        assert hasattr(site, "register")

    def test_init_with_testing_true(self):
        """Test initialization supports testing-only sites"""
        from resources.lib.adultsite import AdultSite

        site = AdultSite(
            "testsite", "Test Site", "https://test.com/", testing=True
        )

        assert site.testing is True


class TestGetCleanTitle:
    """Test get_clean_title() method"""

    def test_get_clean_title_with_color_tags(self):
        """Test get_clean_title removes color formatting"""
        from resources.lib.adultsite import AdultSite

        site = AdultSite(
            "testsite", "[COLOR hotpink]Test Site[/COLOR]", "https://test.com/"
        )

        result = site.get_clean_title()

        assert "[COLOR" not in result
        assert "[/COLOR]" not in result

    def test_get_clean_title_no_formatting(self):
        """Test get_clean_title with plain title"""
        from resources.lib.adultsite import AdultSite

        site = AdultSite("testsite", "Plain Title", "https://test.com/")

        result = site.get_clean_title()

        assert result == "Plain Title"

    def test_get_clean_title_with_webcam_text(self):
        """Test get_clean_title handles webcam text"""
        from resources.lib.adultsite import AdultSite

        site = AdultSite(
            "camsite",
            "[COLOR hotpink]Cam Site[/COLOR]",
            "https://cam.com/",
            webcam=True,
        )

        result = site.get_clean_title()

        # Should extract text between tags
        assert "Cam Site" in result or "webcams" in result


class TestRegister:
    """Test register() decorator"""

    def test_register_function(self):
        """Test registering a basic function"""
        from resources.lib.adultsite import AdultSite

        site = AdultSite("testsite", "Test Site", "https://test.com/")

        @site.register()
        def test_function():
            return "result"

        mode = "testsite.test_function"
        assert mode in AdultSite.func_registry

    def test_register_with_default_mode_true(self):
        """Test registering function with default_mode=True"""
        from resources.lib.adultsite import AdultSite

        site = AdultSite("testsite", "Test Site", "https://test.com/")

        @site.register(default_mode=True)
        def Main():
            pass

        assert site.default_mode == "testsite.Main"

    def test_register_second_default_mode_raises_exception(self):
        """Test registering second default mode raises exception"""
        from resources.lib.adultsite import AdultSite

        site = AdultSite("testsite", "Test Site", "https://test.com/")

        @site.register(default_mode=True)
        def Main():
            pass

        with pytest.raises(Exception, match="default mode is already defined"):

            @site.register(default_mode=True)
            def AnotherMain():
                pass

    def test_register_with_clean_mode_true(self):
        """Test registering function with clean_mode=True"""
        from resources.lib.adultsite import AdultSite

        site = AdultSite("testsite", "Test Site", "https://test.com/")

        @site.register(clean_mode=True)
        def public_function():
            pass

        assert public_function in AdultSite.clean_functions

    def test_register_with_both_flags(self):
        """Test registering with both default_mode and clean_mode"""
        from resources.lib.adultsite import AdultSite

        site = AdultSite("testsite", "Test Site", "https://test.com/")

        @site.register(default_mode=True, clean_mode=True)
        def Main():
            pass

        assert site.default_mode == "testsite.Main"
        assert Main in AdultSite.clean_functions


class TestGetSites:
    """Test get_sites() class method"""

    def test_get_sites_returns_sites_with_default_mode(self):
        """Test get_sites returns only sites with default_mode set"""
        from resources.lib.adultsite import AdultSite

        site1 = AdultSite("site1", "Site 1", "https://site1.com/")
        site2 = AdultSite("site2", "Site 2", "https://site2.com/")

        @site1.register(default_mode=True)
        def Main1():
            pass

        @site2.register(default_mode=True)
        def Main2():
            pass

        sites = list(AdultSite.get_sites())

        assert len(sites) == 2
        assert site1 in sites
        assert site2 in sites

    def test_get_sites_excludes_sites_without_default_mode(self):
        """Test get_sites excludes sites without default_mode"""
        from resources.lib.adultsite import AdultSite

        site1 = AdultSite("site1", "Site 1", "https://site1.com/")
        site2 = AdultSite("site2", "Site 2", "https://site2.com/")

        @site1.register(default_mode=True)
        def Main1():
            pass

        # site2 has no default_mode

        sites = list(AdultSite.get_sites())

        assert len(sites) == 1
        assert site1 in sites
        assert site2 not in sites

    def test_get_sites_empty_when_no_sites(self):
        """Test get_sites returns empty when no sites registered"""
        from resources.lib.adultsite import AdultSite

        sites = list(AdultSite.get_sites())

        assert len(sites) == 0

    def test_get_sites_excludes_testing_sites(self):
        """Test get_sites excludes testing-only sites"""
        from resources.lib.adultsite import AdultSite

        site1 = AdultSite("site1", "Site 1", "https://site1.com/")
        site2 = AdultSite("site2", "Site 2", "https://site2.com/", testing=True)

        @site1.register(default_mode=True)
        def Main1():
            pass

        @site2.register(default_mode=True)
        def Main2():
            pass

        sites = list(AdultSite.get_sites())

        assert site1 in sites
        assert site2 not in sites


class TestGetTestingSites:
    """Test get_testing_sites() class method"""

    def test_get_testing_sites_returns_only_testing_sites(self):
        """Test get_testing_sites only returns testing-marked sites"""
        from resources.lib.adultsite import AdultSite

        site1 = AdultSite("site1", "Site 1", "https://site1.com/")
        site2 = AdultSite("site2", "Site 2", "https://site2.com/", testing=True)

        @site1.register(default_mode=True)
        def Main1():
            pass

        @site2.register(default_mode=True)
        def Main2():
            pass

        sites = list(AdultSite.get_testing_sites())

        assert site2 in sites
        assert site1 not in sites

    def test_get_testing_sites_requires_default_mode(self):
        """Test get_testing_sites requires default_mode"""
        from resources.lib.adultsite import AdultSite

        AdultSite("site2", "Site 2", "https://site2.com/", testing=True)

        sites = list(AdultSite.get_testing_sites())

        assert len(sites) == 0


class TestGetInternalSites:
    """Test get_internal_sites() class method"""

    def test_get_internal_sites_excludes_custom(self):
        """Test get_internal_sites excludes custom sites"""
        from resources.lib.adultsite import AdultSite

        site1 = AdultSite("internal", "Internal Site", "https://internal.com/")
        site2 = AdultSite("custom", "Custom Site", "https://custom.com/")

        @site1.register(default_mode=True)
        def Main1():
            pass

        @site2.register(default_mode=True)
        def Main2():
            pass

        site2.custom = True

        sites = list(AdultSite.get_internal_sites())

        assert len(sites) == 1
        assert site1 in sites
        assert site2 not in sites

    def test_get_internal_sites_requires_default_mode(self):
        """Test get_internal_sites requires default_mode"""
        from resources.lib.adultsite import AdultSite

        _site1 = AdultSite("site1", "Site 1", "https://site1.com/")

        # No default_mode registered

        sites = list(AdultSite.get_internal_sites())

        assert len(sites) == 0

    def test_get_internal_sites_excludes_testing_sites(self):
        """Test get_internal_sites excludes testing-only sites"""
        from resources.lib.adultsite import AdultSite

        site1 = AdultSite("internal", "Internal Site", "https://internal.com/")
        site2 = AdultSite("testing", "Testing Site", "https://testing.com/", testing=True)

        @site1.register(default_mode=True)
        def Main1():
            pass

        @site2.register(default_mode=True)
        def Main2():
            pass

        sites = list(AdultSite.get_internal_sites())

        assert site1 in sites
        assert site2 not in sites


class TestGetSiteByName:
    """Test get_site_by_name() class method"""

    def test_get_site_by_name_finds_site(self):
        """Test get_site_by_name finds site by name"""
        from resources.lib.adultsite import AdultSite

        site1 = AdultSite("targetsite", "Target Site", "https://target.com/")

        @site1.register(default_mode=True)
        def Main():
            pass

        result = AdultSite.get_site_by_name("targetsite")

        assert result == site1

    def test_get_site_by_name_returns_none_when_not_found(self):
        """Test get_site_by_name returns None when not found"""
        from resources.lib.adultsite import AdultSite

        site1 = AdultSite("site1", "Site 1", "https://site1.com/")

        @site1.register(default_mode=True)
        def Main():
            pass

        result = AdultSite.get_site_by_name("nonexistent")

        assert result is None

    def test_get_site_by_name_requires_default_mode(self):
        """Test get_site_by_name only finds sites with default_mode"""
        from resources.lib.adultsite import AdultSite

        _site1 = AdultSite("site1", "Site 1", "https://site1.com/")
        # No default_mode

        result = AdultSite.get_site_by_name("site1")

        assert result is None


class TestGetSitesByName:
    """Test get_sites_by_name() class method"""

    def test_get_sites_by_name_finds_multiple(self):
        """Test get_sites_by_name finds multiple sites"""
        from resources.lib.adultsite import AdultSite

        site1 = AdultSite("site1", "Site 1", "https://site1.com/")
        site2 = AdultSite("site2", "Site 2", "https://site2.com/")
        site3 = AdultSite("site3", "Site 3", "https://site3.com/")

        @site1.register(default_mode=True)
        def Main1():
            pass

        @site2.register(default_mode=True)
        def Main2():
            pass

        @site3.register(default_mode=True)
        def Main3():
            pass

        sites = list(AdultSite.get_sites_by_name(["site1", "site3"]))

        assert len(sites) == 2
        assert site1 in sites
        assert site3 in sites
        assert site2 not in sites

    def test_get_sites_by_name_skips_nonexistent(self):
        """Test get_sites_by_name skips nonexistent sites"""
        from resources.lib.adultsite import AdultSite

        site1 = AdultSite("site1", "Site 1", "https://site1.com/")

        @site1.register(default_mode=True)
        def Main():
            pass

        sites = list(
            AdultSite.get_sites_by_name(["site1", "nonexistent", "alsononexistent"])
        )

        assert len(sites) == 1
        assert site1 in sites

    def test_get_sites_by_name_empty_list(self):
        """Test get_sites_by_name with empty list"""
        from resources.lib.adultsite import AdultSite

        sites = list(AdultSite.get_sites_by_name([]))

        assert len(sites) == 0


class TestGetCustomSites:
    """Test get_custom_sites() class method"""

    def test_get_custom_sites_returns_only_custom(self):
        """Test get_custom_sites returns only custom sites"""
        from resources.lib.adultsite import AdultSite

        site1 = AdultSite("internal", "Internal Site", "https://internal.com/")
        site2 = AdultSite("custom", "Custom Site", "https://custom.com/")

        @site1.register(default_mode=True)
        def Main1():
            pass

        @site2.register(default_mode=True)
        def Main2():
            pass

        site2.custom = True

        sites = list(AdultSite.get_custom_sites())

        assert len(sites) == 1
        assert site2 in sites
        assert site1 not in sites

    def test_get_custom_sites_requires_default_mode(self):
        """Test get_custom_sites requires default_mode"""
        from resources.lib.adultsite import AdultSite

        site1 = AdultSite("custom", "Custom Site", "https://custom.com/")
        site1.custom = True
        # No default_mode

        sites = list(AdultSite.get_custom_sites())

        assert len(sites) == 0

    def test_get_custom_sites_empty_when_none(self):
        """Test get_custom_sites returns empty when no custom sites"""
        from resources.lib.adultsite import AdultSite

        site1 = AdultSite("site1", "Site 1", "https://site1.com/")

        @site1.register(default_mode=True)
        def Main():
            pass

        sites = list(AdultSite.get_custom_sites())

        assert len(sites) == 0
