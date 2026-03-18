const { exec } = require('child_process');
const path = require('path');

class PythonBridge {
  static runScript(scriptPath, args = [], env = {}) {
    return new Promise((resolve, reject) => {
      const fullPath = path.resolve(__dirname, '../../../', scriptPath);
      const command = `python3 ${fullPath} ${args.join(' ')}`;
      const options = {
        env: { ...process.env, ...env, CUMINATION_ALLOW_PLAYWRIGHT: '1' }
      };

      exec(command, options, (error, stdout, stderr) => {
        if (error) {
          reject({ error, stdout, stderr });
        } else {
          resolve(stdout);
        }
      });
    });
  }
}

module.exports = PythonBridge;
