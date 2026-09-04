# edict三省 Phase 1 Handover

Last updated: 2026-09-04

## Purpose

This document lets a new conversation continue the edict三省 Phase 1 desktop work without relying on prior chat context. It records the current implementation state, local build evidence, known gaps, repository risks, and the smallest recommended next steps.

## Product Scope Confirmed

- Product: edict三省 desktop control console.
- Platform: macOS 13 Ventura or later.
- Architectures: Apple Silicon (`arm64`) and Intel (`x64`).
- Desktop stack: Electron, React, TypeScript, Vite, Python sidecar.
- Desktop development port: `127.0.0.1:1517` only.
- Sidecar transport: stdin/stdout JSONL only; it must not listen on HTTP, TCP, or other network ports.
- Phase 1 exclusions: Developer ID Application signing, notarization, auto-update, release publishing, embedded Python runtime, remote deployment, desktop database, and automatic tool installation.

## Repository and Git Delivery State

- Repository root: `/Users/happy/Documents/crow5/edict`
- Current branch: `feat/edict-three-provinces-desktop`
- Desktop delivery commit: `a7ea8df` (`feat: add edict三省 desktop app migration`)
- The branch has been pushed to the `Logosss1/edict` fork.
- A direct push attempt to upstream `cft0808/edict` returned HTTP 403.
- GitHub pull request [#342](https://github.com/cft0808/edict/pull/342) is `OPEN` for `cft0808/edict:main <- Logosss1:feat/edict-three-provinces-desktop`.

The current delivery is already represented by the commit above. For any follow-up work, inspect the working tree and stage only intentionally changed files rather than using a broad add operation.

The generated DMG artifacts are local release outputs under the Git-ignored `project/frontend/release/` directory; they are not included in the source delivery commit.

## Required Project Layout

The following required directories exist:

```text
doc/                 Project documentation
prototype/           Product prototype and design artifacts
project/frontend/    Electron + React desktop application
project/backend/     Python sidecar
database/            Future database scripts; unused by desktop Phase 1
utils/               Future reusable project utilities
```

The legacy application remains in parallel and must not be confused with the new desktop Phase 1 application:

```text
dashboard/           Existing local HTTP dashboard, normally port 7891
edict/frontend/      Existing React Web dashboard
edict/backend/       Existing FastAPI, PostgreSQL, Redis, Alembic, workers
project/frontend/    New Electron desktop application
project/backend/     New Python JSONL sidecar
```

## Desktop Architecture

```text
React renderer
  -> Electron preload contextBridge
  -> Electron IPC
  -> Electron main process
  -> child_process stdin/stdout JSONL
  -> Python sidecar
```

Key files:

```text
project/frontend/electron/main.ts
project/frontend/electron/preload.cts
project/frontend/src/App.tsx
project/frontend/src/styles.css
project/frontend/package.json
project/backend/sidecar/main.py
project/backend/sidecar/service.py
project/backend/sidecar/protocol.py
project/backend/tests/test_sidecar_protocol.py
```

Security boundaries currently implemented:

- `contextIsolation: true`
- `nodeIntegration: false`
- `sandbox: true`
- The renderer uses only `window.edictDesktop` from `preload.cts`.
- The sidecar does not import or create a network listener.

## JSONL Protocol

Protocol version: `1.0`

Supported requests:

```json
{"requestId":"health-1","command":"health"}
{"requestId":"status-1","command":"status"}
{"requestId":"task-1","command":"task.submit","payload":{"title":"Prepare the alpha release"}}
```

Supported events:

- `status`
- `task.created`

Current sidecar behavior:

- `health` returns service, protocol, and `stdio-jsonl` transport details.
- `status` returns in-memory task state and also emits a `status` event.
- `task.submit` validates a non-empty title, creates an in-memory queued task, emits `task.created`, then emits `status`.
- Invalid JSON returns `invalid_json` without terminating the process.
- Unsupported commands return `unsupported_command`.
- Tasks are not persisted and are lost when the sidecar restarts.

## Current User Interface State

### New desktop app

`project/frontend/src/App.tsx` implements a compact desktop Alpha console with:

- Sidecar health and status display.
- Manual status refresh.
- Task title input and submit action.
- Status stream task list.
- Error feedback from failed sidecar calls.

The desktop stylesheet at `project/frontend/src/styles.css` is currently a dark blue Alpha visual treatment. It is functional but does not yet match the warmer product-grade visual direction used by the existing Web dashboard refresh.

### Existing Web dashboard refresh

`edict/frontend/src/App.tsx` and `edict/frontend/src/index.css` contain a separate refresh of the existing Web dashboard toward a warm-white and graphite workspace. It includes a sidebar, command menu, task composer, responsive behavior, and visual polish.

Important functional gap: the new Web composer currently clears the local form, switches to the edicts tab, and shows a toast. It does not call the real task creation API. Do not describe this interaction as a completed task creation feature until it is connected to the existing backend flow and verified.

### Real Electron verification coverage

- On the local arm64 macOS machine, a real Electron launch has verified the initial screen, the preload bridge, and the sidecar `health`/`status` flow in the browser window.
- Full acceptance is not complete: task submission through completion/failure, settings taking effect, filtering/search, responsive behavior, keyboard interactions, and launch on a real Intel machine remain unverified.

## Desktop Build Configuration

File: `project/frontend/package.json`

```text
Application name: edict三省
Application ID: io.edict.desktop
Application version: 0.1.0
Minimum macOS version: 13.0
Architectures: arm64 and x64
Packager: electron-builder 25.1.8
Electron: 33.4.11 installed locally

Custom application icon: project/frontend/assets/edict-three-provinces.icns
Vector source: project/frontend/assets/edict-three-provinces.svg
```

Relevant scripts:

```bash
cd project/frontend

npm ci
npm run dev
npm run typecheck
npm run test
npm run build
npm run verify
python3 -m unittest discover -s ../backend/tests -v
npm run package:mac
npm run dist:mac
```

Script intent:

- `npm run verify`: typecheck, Vitest, and production build.
- `npm run package:mac`: local `.app` directory for smoke checks.
- `npm run dist:mac`: produces local arm64 and x64 DMG test release packages under `release/`. These local release artifacts were not signed with a Developer ID Application signature and were not notarized; the embedded application-bundle signature states are recorded below.

## Build Evidence

The local macOS desktop build completed successfully; the evidence below describes the delivered desktop state.

Verified commands:

```bash
cd project/frontend
npm run verify
npm run dist:mac

hdiutil verify release/edict三省-0.1.0-arm64.dmg
hdiutil verify release/edict三省-0.1.0.dmg
```

Results:

```text
npm run verify: passed
  - TypeScript typecheck: passed
  - Vitest: 6 test files, 17 tests passed
  - Vite production build: passed

Python sidecar unittest: passed, 9/9
DMG integrity: arm64 and x64 passed hdiutil verify
Real Electron/browser verification on local arm64 macOS: initial screen, preload bridge, sidecar health/status passed
```

Generated DMG files:

| Architecture | File | Integrity |
| --- | --- | --- |
| arm64 | `project/frontend/release/edict三省-0.1.0-arm64.dmg` | `hdiutil verify` passed |
| x64 | `project/frontend/release/edict三省-0.1.0.dmg` | `hdiutil verify` passed |

Generated application bundles:

```text
project/frontend/release/mac-arm64/edict三省.app
project/frontend/release/mac/edict三省.app
```

Bundle metadata verified in the generated application packages:

- `Info.plist` display name: `edict三省`
- `CFBundleIdentifier`: `io.edict.desktop`
- `icon.icns` exists in the application bundle.

Only the following local application-bundle signature states have been confirmed:

- arm64 bundle: ad-hoc signed.
- x64 bundle: unsigned.
- The local bundles were not signed with a Developer ID Application signature, and the local release artifacts were not notarized.

The generated DMG files are ignored by Git and are not included in the source delivery commit.

## Local Environment Used for Verification

```text
Node.js: v24.19.0
npm: 11.17.0
Python: 3.13.15
Host architecture: arm64
Host macOS: 26.4.1
```

Target baseline remains Node 20+ and Python 3.12. Python 3.12 was not present on the verification machine. The standard-library sidecar passed tests on Python 3.13, but that does not replace target-device verification with Python 3.12.

## Known Risks and Blockers

### Runtime and product blockers

1. Python is not embedded in the DMG.
   - The package copies Python sidecar source only.
   - `project/frontend/electron/main.ts` defaults to `python3.12` unless `EDICT_PYTHON` is set.
   - A target Mac without a compatible Python interpreter may open the app but fail to start the sidecar.
   - Decide between a documented Python 3.12 prerequisite with clear detection/error UI, or packaging an embedded runtime/native sidecar.

2. The desktop sidecar is an in-memory proof of flow, not an integration with the legacy backend.
   - It has no persistence, authentication, database, orchestration, or existing task schema mapping.
   - Before expanding functionality, explicitly decide whether the desktop app should adapt the existing FastAPI system or grow an independent local sidecar domain.

3. Full Electron and product acceptance still needs end-to-end verification.
    - The renderer requests `health` and `status` immediately on mount.
    - The main process currently creates the window, then starts the sidecar and registers IPC handling.
    - Real arm64 macOS browser verification has covered the initial screen, preload bridge, and sidecar `health`/`status` flow.
    - A cold-start race, sidecar availability error, or IPC ordering problem still needs coverage beyond that initial flow.
    - Task submission through completion/failure, settings taking effect, filtering/search, responsive behavior, keyboard interactions, and real Intel-machine launch remain unverified.

4. The desktop frontend test suite is a baseline, not full acceptance coverage.
    - Current Vitest evidence is 6 test files with 17 tests passed.
    - Full UI/IPC coverage for task lifecycle, settings, filtering/search, responsive behavior, keyboard interactions, sidecar errors, and recovery remains pending.

### Distribution blockers

1. The local release artifacts were not signed with a Developer ID Application signature.
2. The local release artifacts have not been notarized.
3. The x64 artifact was built and verified as a DMG, but not manually launched on an Intel Mac.
4. `npm audit` did not complete within the local timeout during the previous review; do not claim a clean dependency audit without rerunning it.

Consequences:

- The DMG files are acceptable only as explicitly labeled local Alpha/test release packages that were not signed with a Developer ID Application signature and were not notarized. The only verified embedded application-bundle signature states are arm64 ad-hoc signed and x64 unsigned; do not generalize these states beyond the verified artifacts.
- Do not represent them as production-ready public releases.

## Repository Follow-ups

The desktop source delivery is represented by commit `a7ea8df`, and the branch has been pushed to the `Logosss1/edict` fork. The notes below separate completed source tracking from future repository maintenance.

### Completed source tracking

1. Completed in `a7ea8df`: `.gitignore` narrows `_*.py` to `/_*.py`, and `project/backend/sidecar/__init__.py` is tracked.
   - The root-only rule keeps temporary root scripts ignored without matching the sidecar package initializer.
   - Confirm the tracked initializer is not ignored:

   ```bash
   git check-ignore -v project/backend/sidecar/__init__.py
   ```

   The command should print nothing.

### Future source maintenance

1. For future source changes, deliberately stage the desktop source, tests, package lock, and documentation.
    - Relevant desktop paths include `project/frontend/**`, `project/backend/**`, and `project/README.md`.
    - Keep ignored build outputs out of source delivery: `node_modules/`, `dist-*`, `release/`, `.app`, `.dmg`, `.blockmap`, and Python caches.

2. Maintain existing desktop documentation.
   - `README.md`, `project/README.md`, and `project/frontend/README.md` already provide desktop startup, verification, and packaging guidance.
   - If broader documentation coverage is needed, mirror the verified workflow in `README_EN.md`, `README_JA.md`, and `CONTRIBUTING.md`.

3. Expand CI for actual release artifacts.
   - Existing `desktop-quality` in `.github/workflows/ci.yml` runs `npm run package:mac`, which creates only an `.app` directory.
   - Add a separate controlled release workflow later for `npm run dist:mac`, artifact upload, SHA-256 output, architecture verification, signing, notarization, and tag/version checks.

4. Add a release history document such as `CHANGELOG.md` before the first public release.

### Recommended repository improvements

1. Add `/project/frontend` to `.github/dependabot.yml` because the desktop `package.json` and lockfile are nested there.
2. Add explicit `/project/frontend/` and `/project/backend/` rules to `.github/CODEOWNERS`.
3. Change generic `.env` protection to safely ignore local variants while keeping examples trackable:

   ```gitignore
   .env
   .env.*
   !.env.example
   !.env.*.example
   ```

   Review `edict/frontend/.env.development` separately before applying a blanket rule because it currently contains only a public local API URL.

4. Add secret scanning such as Gitleaks and dependency audit checks to CI.
5. Generate `SHA256SUMS.txt` and publish release notes with future DMG assets.
6. Consider Git LFS or external hosting for `docs/Agent_video_Pippit_20260225121727.mp4` (about 38 MB). It is below GitHub's 100 MB hard limit but increases clone size.

### Sensitive information review

No recognizable real private key, GitHub token, cloud key, or API key was found during the prior static scan.

Known development/placeholder values include:

```text
edict_dev_2024
change-me-in-production
```

Relevant files:

```text
edict/.env.example
edict/docker-compose.yml
.github/workflows/ci.yml
```

These are development values, not verified production credentials. They must not be reused for real deployments. GitHub Actions references to `secrets.*` are normal secure references and do not expose secret values.

## Current Status and Recommended Next Steps

The current evidence supports a Phase 1 local-test desktop baseline without Developer ID Application signing or notarization: the `a7ea8df` delivery commit exists, the branch is available on the `Logosss1/edict` fork, the arm64 Electron initial-screen/bridge/sidecar health-status flow has been browser-verified, and the arm64/x64 DMGs pass `hdiutil verify`. GitHub pull request [#342](https://github.com/cft0808/edict/pull/342) is `OPEN` for `cft0808/edict:main <- Logosss1:feat/edict-three-provinces-desktop`.

The following items remain pending and are not described as completed:

1. Complete real Electron acceptance for task submission through completion/failure, settings taking effect, filtering/search, responsive behavior, and keyboard interactions.
2. Launch and exercise the x64 package on a real Intel Mac.
3. Expand UI/IPC tests around task lifecycle, settings, filtering/search, responsive behavior, keyboard interactions, sidecar errors, and recovery.
4. Decide whether the target Python 3.12 prerequisite should remain documented or be replaced by an embedded runtime/native sidecar.
5. Decide whether the desktop app should integrate with the existing backend or continue with an independent local sidecar domain, including a persistence strategy.

## Reproducible Validation Checklist

Run from repository root unless a command changes directory.

```bash
# Inspect changes and whitespace errors.
git status --short
git diff --check

# Confirm the tracked package initializer is not ignored.
git check-ignore -v project/backend/sidecar/__init__.py

# Install desktop dependencies from the lockfile and verify the implementation.
cd project/frontend
npm ci
npm run verify
python3.12 -m unittest discover -s ../backend/tests -v

# Build local macOS test artifacts without Developer ID Application signing or notarization.
npm run package:mac
npm run dist:mac

# Verify DMG integrity and record checksums.
hdiutil verify release/edict三省-0.1.0-arm64.dmg
hdiutil verify release/edict三省-0.1.0.dmg
shasum -a 256 release/edict三省-0.1.0-arm64.dmg release/edict三省-0.1.0.dmg

# Run dependency review. These may need network access and can take time.
npm audit --omit=dev
npm audit --audit-level=high

# Optional secret scan when gitleaks is installed.
cd ../..
gitleaks detect --source . --no-git --redact
```
