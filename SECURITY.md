# Security Policy

## Supported version

The latest code on `main` is the supported development version of this
prototype. Tagged releases will be listed here when the first public release is
published.

## Reporting a vulnerability

Do not publish credentials, connection strings, customer information or a
working exploit in a public issue. Contact the maintainers privately through
the repository owner, include steps to reproduce, expected impact and affected
versions, and allow time for validation before public disclosure.

## Secrets

Local SQL Server credentials belong only in `backend/.env`. JWT secrets belong
in environment configuration or the ignored development secret file. Neither
file may be committed.
