# Madar Production Readiness

Madar touches operational workflows and ERPNext accounting documents. Production
launch requires a deliberate review beyond staging feature verification.

## Launch Gate

Before production:

- Run the full Python and Flutter test suites.
- Run `python3 scripts/check_security_rules.py`.
- Confirm only health is guest-accessible.
- Confirm Flutter does not call `/api/resource` or ERPNext DocTypes directly.
- Confirm no secrets are committed.
- Confirm dev bootstrap is disabled.
- Confirm staging credentials are not reused for production.

## Permission Review

Review production role assignments:

- Madar Admin: only trusted administrators.
- Madar Accountant: accounting users who may finalize ERP postings.
- Madar Cashier: cashbox review, no accounting final submit.
- Madar Driver: assigned delivery batches only.
- Madar Branch User and Supervisor: scoped branch operations only.
- Madar Employee: employee self-service and attendance only.

Confirm `accounting.finalize` is not granted to cashier, driver, branch,
supervisor, or regular employee users.

## ERP Posting Review

ERP posting actions are high-risk:

- Sales Invoice submit may create GL Entries.
- Payment Entry submit may create GL Entries.
- No finalization action should be automatic.
- Confirm accounting users understand the confirmation dialog and downstream
  ERPNext impact.

Before enabling production accounting finalization:

- Validate ERP accounts, modes of payment, customers, items, and price behavior.
- Confirm draft Sales Invoice and draft Payment Entry mappings with accounting.
- Confirm rollback/correction procedure outside Madar for posted ERP documents.

## Secret Handling

Never store these in Madar settings or Flutter:

- ERP API keys or API secrets.
- Database credentials.
- SSH credentials.
- Email passwords.
- WhatsApp/SMS tokens.
- Payment gateway secrets.

Use environment or managed secret storage outside the repository.

## Monitoring Checklist

Post-launch monitor:

- ERP sync failures.
- Payment sync failures.
- Accounting finalization failures.
- Cashbox return/approval backlog.
- Failed login spikes.
- Unexpected guest access errors.
- GL Entry count changes from finalization windows.
- Queue/background job failures if future jobs are added.

## Credential Rotation Reminder

Rotate credentials before production if they were ever shared in chat,
terminal history, screenshots, documentation, or staging scripts. Staging
passwords must not become production passwords.

## Known R10 Limitations

R10-T01 does not implement:

- External monitoring.
- SIEM/audit export.
- Rate limiting.
- Push notification security.
- Production secret manager integration.

These should be planned explicitly before production hardening is considered
complete.
