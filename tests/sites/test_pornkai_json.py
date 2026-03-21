
import json
import pytest
from resources.lib.sites import pornkai

def test_extract_markup_and_meta():
    sample_json = {
        "html": "<div class='thumbnail'><a class='thumbnail_link' href='/view?key=v1'>Video 1</a></div>",
        "results_remaining": 100
    }
    html_str = json.dumps(sample_json)
    
    markup, results = pornkai._extract_markup_and_meta(html_str)
    
    assert "Video 1" in markup
    assert results == 100

def test_extract_markup_and_meta_nested():
    sample_json = {
        "data": {
            "markup": "<div class='thumbnail'>Nested Markup</div>",
            "meta": {
                "resultsRemaining": "50"
            }
        }
    }
    html_str = json.dumps(sample_json)
    
    markup, results = pornkai._extract_markup_and_meta(html_str)
    
    assert "Nested Markup" in markup
    assert results == 50

def test_extract_markup_and_meta_escaped():
    html_str = '{"html": "<div class=\\"thumbnail\\">Escaped \\/ Markup</div>"}'
    
    markup, _ = pornkai._extract_markup_and_meta(html_str)
    
    assert 'class="thumbnail"' in markup
    assert 'Escaped / Markup' in markup
