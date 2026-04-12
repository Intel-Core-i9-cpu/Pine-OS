# Pine-OS

App-first starter project for eventually branching into operating-system targets.

## Quick start

```bash
python3 app/pine_app.py new pine-demo --target desktop --dir .
python3 app/pine_app.py status --config ./pine-demo/pine.json
python3 app/pine_app.py package --config ./pine-demo/pine.json --format deb
```

## Current approach

1. Build the user application first.
2. Package as `.exe` or `.deb` for distribution.
3. Branch into target-specific work (including `rpi5`) after app features stabilize.
