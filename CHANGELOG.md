# Changelog

All notable changes to DX-Lab Core are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- MIT project license and open-source governance documents.
- SQL Server-backed administrator and sales workflows.
- Authentication, role checks, persistent sessions and transactional checkout.
- React Router, TanStack Query, TanStack Table and Recharts integrations.
- Idempotent paid-order creation and immutable product-name snapshots.
- Unit and non-destructive integration smoke tests.
- Separate backend/frontend guides and an open-source compliance checklist.
- Project structure and team ownership documentation.

### Changed

- Frontend and backend are maintained as separate application directories.
- Administrator and sales screens now read operational data from backend APIs.
- Backend validates configuration and SQL Server schema during startup.
- Initial prototype for the DX-Lab Core digital commerce workspace.
- Legacy plaintext account passwords are upgraded to PBKDF2 after a valid login.
- Renamed the backend database helper to `db.py` and moved frontend navigation
  constants to `src/config/navigation.js` to remove ambiguous module names.
- First-time frontend installation now uses the lockfile through `npm ci`.
- Local secrets and generated directories are hidden from the shared VS Code
  Explorer while remaining available to the applications.
