# Pine-OS

App-first starter project for eventually branching into operating-system targets, including Raspberry Pi 5.

## Quick start

```bash
python3 app/pine_app.py new pine-demo --target rpi5 --dir .
python3 app/pine_app.py status --config ./pine-demo/pine.json
python3 app/pine_app.py package --config ./pine-demo/pine.json --format deb --out ./dist
python3 app/pine_app.py package --config ./pine-demo/pine.json --format exe --out ./dist
python3 app/pine_app.py rpi5-image --config ./pine-demo/pine.json --out ./dist
python3 app/pine_app.py rpi5-bootkit --config ./pine-demo/pine.json --out ./dist
```

## What you get today

- `.deb` artifact generated locally for app-layer distribution.
- `.exe` release marker locally, with real Windows `.exe` expected from CI/release workflow.
- `*.img` Raspberry Pi 5 image scaffold artifact for early flashing workflow validation.
- `rpi5-bootkit/` milestone assets with:
  - `boot/config.txt`
  - `boot/cmdline.txt`
  - `boot/initramfs.cpio.gz`
  - serial-console focused init script and flashing instructions.

## Current approach

1. Build the user application first.
2. Ship release artifacts (`.deb`, `.exe`, and `rpi5 .img`) from releases.
3. Use `rpi5-bootkit` to validate boot plumbing before full userspace.
4. Replace image scaffold with a fully bootable Raspberry Pi 5 image in next milestones.

## Release behavior

When you publish a GitHub Release, the workflow uploads these files **directly onto that Release**:

- `*.deb` (Linux package)
- `*.img` (RPi5 image scaffold)
- `*.exe` (Windows executable built on `windows-latest`)

No manual upload step is required.
