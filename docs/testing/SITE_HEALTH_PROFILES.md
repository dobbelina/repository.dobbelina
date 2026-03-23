# Site Health Profiles

`config/site_profiles.json` defines per-site expectations for the live smoke runner.

## Purpose

The smoke runner is generic, but site modules are not. Profiles reduce false positives by
describing what a site is expected to support and what the harness can or cannot verify.

## Schema

```json
{
  "default": {
    "supports": {
      "main": true,
      "list": true,
      "categories": true,
      "search": true,
      "play": true
    },
    "content_type": "video",
    "requires_flaresolverr": false,
    "harness": {
      "playback_not_testable": false,
      "search_results_optional": false,
      "categories_optional": false
    }
  },
  "sites": {
    "example": {
      "tier": 1,
      "content_type": "cam",
      "requires_flaresolverr": true,
      "supports": {
        "search": false,
        "play": false
      },
      "harness": {
        "playback_not_testable": true
      }
    }
  }
}
```

## Field meanings

- `supports`
  - Whether the site should expose a meaningful implementation for each smoke step.
- `content_type`
  - `video`, `cam`, or another classification you want the harness to reason about.
- `requires_flaresolverr`
  - Marks sites where Cloudflare bypass infrastructure is expected.
- `harness.playback_not_testable`
  - Use for sites where the smoke harness cannot realistically validate playback.
- `harness.search_results_optional`
  - Use where empty or weak search results are not a reliable failure signal.
- `harness.categories_optional`
  - Use where categories are absent or unstable and should not create noise.
- `tier`
  - Priority marker for future rollout and alerting.

## Rollout guidance

1. Add profiles for high-value or historically noisy sites first.
2. Keep the profile narrowly factual; do not encode temporary bugs as permanent expectations.
3. When a site is fixed, tighten the profile rather than letting the exception live forever.
