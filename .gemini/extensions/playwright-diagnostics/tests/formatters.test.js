const test = require('node:test');
const assert = require('node:assert');
const { formatSmokeResult } = require('../lib/formatters');

test('formatSmokeResult formats a successful result correctly', (t) => {
  const result = {
    site: 'anybunny',
    url: 'https://anybunny.tv',
    standard_fetch: 'OK',
    playwright_fetch: 'UNKNOWN',
    status: 'PASS',
    notes: []
  };
  
  const formatted = formatSmokeResult(result);
  
  assert.ok(formatted.includes('### Smoke Test Result: anybunny'));
  assert.ok(formatted.includes('**Status:** ✅ PASS'));
  assert.ok(formatted.includes('**URL:** https://anybunny.tv'));
  assert.ok(formatted.includes('**Standard Fetch:** OK'));
});

test('formatSmokeResult formats a failed result with notes correctly', (t) => {
  const result = {
    site: 'anybunny',
    url: 'https://anybunny.tv',
    standard_fetch: 'BLOCKED',
    playwright_fetch: 'OK',
    status: 'OK (PLAYWRIGHT ONLY)',
    notes: ['Blocked by Cloudflare in standard fetch.', 'Accessible via Playwright (JS required).']
  };
  
  const formatted = formatSmokeResult(result);
  
  assert.ok(formatted.includes('**Status:** ✅ OK (PLAYWRIGHT ONLY)'));
  assert.ok(formatted.includes('* Blocked by Cloudflare in standard fetch.'));
  assert.ok(formatted.includes('* Accessible via Playwright (JS required).'));
});
