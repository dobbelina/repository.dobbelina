const PythonBridge = require('./lib/bridge');
const { formatSmokeResult } = require('./lib/formatters');

async function pwSmoke({ site }) {
  try {
    const stdout = await PythonBridge.runScript('scripts/playwright_smoke_runner.py', [
      '--site', site,
      '--json'
    ]);
    
    let result;
    try {
      result = JSON.parse(stdout.trim());
    } catch (parseError) {
      return `Error parsing smoke test result: ${parseError.message}\n\nRaw output:\n${stdout}`;
    }
    
    return formatSmokeResult(result);
  } catch (err) {
    const errorMsg = err.error ? err.error.message : String(err);
    const stderr = err.stderr || '';
    return `Error running smoke test: ${errorMsg}\n${stderr}`;
  }
}

module.exports = {
  'pw-smoke': pwSmoke
};
