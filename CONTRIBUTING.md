# Contributing to DX-Lab Core

DX-Lab Core welcomes bug reports, documentation improvements and focused code
contributions.

## Development workflow

1. Create an issue describing the bug or proposed change.
2. Create a short-lived branch from `main`.
3. Keep frontend, backend and database changes in clearly scoped commits.
4. Run the frontend build and backend test suite before requesting review.
5. Open a pull request that explains the behavior change and verification.

## Source and licensing requirements

- New source files must carry `SPDX-License-Identifier: MIT` in a supported
  comment format.
- Only introduce dependencies or adapted code with a clear license compatible
  with this project's MIT license.
- Record new third-party components in `THIRD_PARTY_NOTICES.md` and
  `docs/OPEN_SOURCE_COMPONENTS.md`.
- Preserve upstream copyright and license notices for adapted code.
- Never commit passwords, access tokens, `.env`, database backups containing
  personal data, `node_modules` or Python virtual environments.

## Commit guidance

Use concise messages such as `feat:`, `fix:`, `docs:`, `test:` and `chore:`.
Do not combine unrelated formatting changes with a functional change.
