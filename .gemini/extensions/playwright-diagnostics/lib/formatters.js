/**
 * Formatters for Playwright diagnostics results.
 */

/**
 * Formats a smoke test result object into Markdown.
 * @param {Object} result - The result object from the smoke runner.
 * @returns {string} Markdown formatted result.
 */
function formatSmokeResult(result) {
  if (!result || typeof result !== 'object') {
    return 'Invalid smoke test result.';
  }

  const { site, url, status, standard_fetch, playwright_fetch, notes = [] } = result;
  
  const statusIcon = status && (status.includes('OK') || status === 'PASS') ? '✅' : '❌';
  
  let md = `### Smoke Test Result: ${site}\n\n`;
  md += `**Status:** ${statusIcon} ${status || 'UNKNOWN'}\n`;
  md += `**URL:** ${url || 'N/A'}\n`;
  md += `**Standard Fetch:** ${standard_fetch || 'N/A'}\n`;
  md += `**Playwright Fetch:** ${playwright_fetch || 'N/A'}\n\n`;
  
  if (notes.length > 0) {
    md += `**Notes:**\n`;
    notes.forEach(note => {
      md += `* ${note}\n`;
    });
  }
  
  return md;
}

module.exports = {
  formatSmokeResult
};
