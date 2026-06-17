# Chrome / Chromium Extension Support — Design

Date: 2026-06-17
Status: Approved (implementation)

## Goal

Make the Cove browser extension work on Chromium browsers (Chrome, Edge,
Brave, Vivaldi, Opera, Chromium) with the same download-interception
behavior it already has on Firefox. Distribution target: Chrome Web Store.

The Firefox extension is live on AMO as Manifest V2 and must keep working
unchanged. Chrome dropped MV2, so Chrome needs a Manifest V3 variant. The
native messaging host registration must also learn the Chromium format and
locations (Firefox uses `allowed_extensions`; Chromium uses
`allowed_origins` with `chrome-extension://<id>/`).

## Approach (chosen: A — shared code, per-browser manifest)

All extension logic stays shared in `extension/`. Only the manifest differs
per browser, assembled by a build step. This keeps one `background.js` and
leaves the published MV2 Firefox addon untouched (zero regression risk).

### Extension files

- `extension/manifest.json` — UNCHANGED. Firefox MV2.
- `extension/manifest.chrome.json` — NEW. Manifest V3:
  - `manifest_version: 3`
  - `action` (replaces `browser_action`)
  - `background: { "service_worker": "background.js" }` (no `persistent`)
  - `permissions`: downloads, cookies, contextMenus, nativeMessaging,
    notifications, storage
  - `host_permissions: ["<all_urls>"]` (split out of `permissions` in MV3)
  - `content_security_policy: { "extension_pages": "script-src 'self'; object-src 'self'" }`
  - `key`: pinned public key (below) so the unpacked dev ID is stable
  - no `browser_specific_settings`
  - same `commands`, `options_ui` (drop Firefox-only `browser_style`), `icons`
- `extension/background.js` — three backward-compatible edits (all no-ops in
  Firefox MV2, so the shared file keeps working in both):
  1. `const browser = globalThis.browser || globalThis.chrome;`
  2. badge via `const action = browser.action || browser.browserAction;`
  3. move `contextMenus.create(...)` into `runtime.onInstalled` (required for
     MV3 service workers; valid in MV2 too)
- `popup/`, `options/`, `icons/` — shared, untouched.

Only one-shot `runtime.sendNativeMessage` is used (no long-lived port), so
the MV3 service-worker lifecycle needs no special handling.

### Build step

- `scripts/build_extension.py` (cross-platform; runs on Windows) →
  - `dist/firefox/` = copy of `extension/` (manifest.json already correct)
  - `dist/chrome/`  = copy of `extension/` with `manifest.chrome.json`
    written as `manifest.json` and `manifest.chrome.json` removed
  - zips each as `dist/cove-firefox-<ver>.zip`, `dist/cove-chrome-<ver>.zip`
  - never copies `chrome-key.pem`

### Extension ID

Generated RSA-2048 keypair (one-time):
- `extension/chrome-key.pem` — private, gitignored, never committed.
- Pinned dev extension ID: `jnemjlhecpicblbjjhbhjbbbmjhplfal`
- The base64 public key is embedded as `key` in `manifest.chrome.json`.

The native host whitelists a LIST of Chrome IDs. The dev ID is included now.
After the Chrome Web Store item is created, its assigned ID is appended to
`_CHROME_EXTENSION_IDS` (one-line follow-up) and a new build/release shipped.

## Native host (`cove/native_host_install.py`)

`native_messaging.py` (the runtime/protocol) needs NO changes — identical
across browsers.

- `_CHROME_EXTENSION_IDS: list[str]` — pinned dev ID now; Web Store ID later.
- `_chrome_manifest()` — like `_manifest()` but with
  `"allowed_origins": ["chrome-extension://<id>/" for each id]` instead of
  `allowed_extensions`.
- POSIX (`_install_posix`): in addition to the Mozilla dirs, write the Chrome
  manifest + reuse the existing bash wrapper to each Chromium browser's
  `~/.config/<browser>/NativeMessagingHosts/`:
  google-chrome, chromium, microsoft-edge, BraveSoftware/Brave-Browser,
  vivaldi, opera. Extend the Flatpak override list with Chromium flatpak IDs.
- Windows (`_install_windows`): in addition to the Mozilla registry key,
  write a Chrome-format manifest and create per-browser registry keys
  pointing at the same `.bat` launcher:
  `SOFTWARE\Google\Chrome\NativeMessagingHosts\<host>`,
  `SOFTWARE\Microsoft\Edge\NativeMessagingHosts\<host>`,
  `SOFTWARE\Chromium\NativeMessagingHosts\<host>`,
  `SOFTWARE\BraveSoftware\Brave-Browser\NativeMessagingHosts\<host>`,
  `SOFTWARE\Vivaldi\NativeMessagingHosts\<host>`,
  `SOFTWARE\Opera Software\NativeMessagingHosts\<host>`.

Both Firefox and Chromium hosts are registered on every app launch, matching
existing Firefox behavior (idempotent refresh).

## Versioning

- App: `cove/__init__.py` 1.4.5 → 1.5.0 (feature).
- Extension: bump `version` in both manifests.

## Tests

Extend `tests/test_native_host_install.py`:
- `_chrome_manifest()` uses `allowed_origins` with the pinned ID.
- POSIX writes Chromium manifests to the expected per-browser dirs.
- Windows writes the Chrome-format manifest and creates each Chromium
  registry key (mocked `winreg`).
- Dispatch still routes win32 vs posix.

JS has no test harness in this repo; the extension is verified manually
(load `dist/chrome` unpacked, register host, Test Connection) plus build-
script output validation. Host side verified end-to-end as before
(registry/manifest written, ping round-trips through the `.bat`).

## Docs

- README "Browser Extension" section: add Chrome/Chromium, note the build
  step and the Web Store publish + `allowed_origins` ID follow-up.

## Out of scope

- `release.yml` changes (Web Store publishing is a separate manual flow).
- Migrating the Firefox addon to MV3.
- Edge Add-ons / other stores (extension is Web-Store-distributed; the same
  build loads unpacked elsewhere).
