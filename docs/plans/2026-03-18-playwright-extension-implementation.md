# Playwright Testing & Debugging Extension Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Gemini CLI extension that automates live site verification and debugging using the project's existing Playwright infrastructure.

**Architecture:** A hybrid extension consisting of Node.js-based slash commands (acting as a bridge to Python scripts) and a specialized Agent Skill for deep diagnostic guidance.

**Tech Stack:** Node.js, Python 3, Playwright, Gemini CLI Extension API.

---

### Task 1: Extension Scaffolding & Manifest

**Files:**
- Create: `.gemini/extensions/playwright-diagnostics/gemini-extension.json`
- Create: `.gemini/extensions/playwright-diagnostics/package.json`
- Create: `.gemini/extensions/playwright-diagnostics/lib/bridge.js`

- [ ] **Step 1: Create the extension manifest**
```json
{
  "name": "playwright-diagnostics",
  "version": "1.0.0",
  "description": "Automated Playwright-based testing and debugging for Cumination.",
  "commands": [
    {
      "name": "pw-smoke",
      "description": "Run a live smoke test for a specific site.",
      "parameters": [
        {
          "name": "site",
          "description": "The name of the site module (e.g., anybunny)",
          "required": true
        }
      ]
    },
    {
      "name": "pw-sniff",
      "description": "Sniff the network for the first playable video URL.",
      "parameters": [
        {
          "name": "url",
          "description": "The URL of the video page",
          "required": true
        }
      ]
    }
  ],
  "skills": [
    {
      "name": "playwright-expert",
      "path": "skills/playwright-expert/SKILL.md"
    }
  ]
}
```

- [ ] **Step 2: Create the package.json**
```json
{
  "name": "playwright-diagnostics",
  "version": "1.0.0",
  "dependencies": {}
}
```

- [ ] **Step 3: Create the basic Node.js bridge logic**
```javascript
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
```

- [ ] **Step 4: Commit scaffolding**
```bash
git add .gemini/extensions/playwright-diagnostics/
git commit -m "feat(ext): scaffold playwright-diagnostics extension"
```

---

### Task 2: Implement `/pw-smoke` Command

**Files:**
- Modify: `.gemini/extensions/playwright-diagnostics/index.js` (or equivalent entry point)
- Test: Manual verification with `gemini /pw-smoke anybunny`

- [ ] **Step 1: Implement the command handler in the bridge**
- [ ] **Step 2: Connect handler to `scripts/playwright_smoke_runner.py`**
- [ ] **Step 3: Format the output as Markdown**
- [ ] **Step 4: Test and commit**

---

### Task 3: Implement `/pw-sniff` Command

**Files:**
- Create: `scripts/playwright_sniff_bridge.py` (New wrapper for `playwright_helper.sniff_video_url`)
- Modify: `.gemini/extensions/playwright-diagnostics/index.js`

- [ ] **Step 1: Create the Python sniffer bridge**
```python
import sys
import os
from pathlib import Path

# Add project paths
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "plugin.video.cumination"))

from resources.lib import playwright_helper

if __name__ == "__main__":
    url = sys.argv[1]
    os.environ["CUMINATION_ALLOW_PLAYWRIGHT"] = "1"
    video_url = playwright_helper.sniff_video_url(url)
    print(video_url if video_url else "No video URL found")
```

- [ ] **Step 2: Connect the `/pw-sniff` command to the new bridge script**
- [ ] **Step 3: Test and commit**

---

### Task 4: Create the "Playwright Expert" Skill

**Files:**
- Create: `.gemini/extensions/playwright-diagnostics/skills/playwright-expert/SKILL.md`

- [ ] **Step 1: Write the skill instructions**
Focus on:
- How to analyze Playwright network traces.
- Mapping live DOM elements to BeautifulSoup selectors.
- Handling Cloudflare challenges.
- Verification steps for images and playback.

- [ ] **Step 2: Commit the skill**

---

### Task 5: Final Validation & Environment Check

- [ ] **Step 1: Implement `/pw-test-env`**
- [ ] **Step 2: Run full verification across 3 sites**
- [ ] **Step 3: Final commit and cleanup**
