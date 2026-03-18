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

async function pwSniff({ url }) {
  try {
    const videoUrl = await PythonBridge.runScript('scripts/playwright_sniff_bridge.py', [
      url
    ]);
    
    const cleanedUrl = videoUrl.trim();
    if (!cleanedUrl || cleanedUrl === 'No video URL found') {
      return `No video stream found for: ${url}`;
    }
    
    return `**Found Video Stream:**\n\n` + 
           `\`\`\`\n${cleanedUrl}\n\`\`\`\n\n` +
           `_Tip: You can use this URL directly in VLC or other players for verification._`;
  } catch (err) {
    const errorMsg = err.error ? err.error.message : String(err);
    const stderr = err.stderr || '';
    return `Error sniffing URL: ${errorMsg}\n${stderr}`;
  }
}

async function pwTestEnv() {
  try {
    const stdout = await PythonBridge.runScript('scripts/playwright_test_env.py');
    return stdout;
  } catch (err) {
    const errorMsg = err.error ? err.error.message : String(err);
    const stderr = err.stderr || '';
    return `Error checking environment: ${errorMsg}\n${stderr}`;
  }
}

module.exports = {
  'pw-smoke': pwSmoke,
  'pw-sniff': pwSniff,
  'pw-test-env': pwTestEnv
};
