# Private Investment Dashboard — Security Model

## Threat model

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Stolen login credentials | Low | Critical | MFA, rate limiting, session timeouts, audit logging |
| Leaked Supabase keys | Low | Critical | Service key in server-only env vars, never in client code |
| Insecure RLS | Medium | Critical | All tables have owner_id RLS; tested in CI |
| Cross-portfolio data access | Low | Critical | owner_id on every portfolio row |
| Malicious CSV upload | Medium | Medium | Client + server validation, column whitelist, row limits |
| Model-import tampering | Low | High | Integrity hash verification on import |
| Replayed imports | Low | Medium | Idempotency keys on snapshot_id |
| Duplicate transactions | Medium | Medium | Idempotency keys, UNIQUE(idempotency_key) |
| Stale prices | Medium | Low | Timestamp on every price observation |
| Accidental snapshot replacement | Low | Medium | Immutable after PUBLISHED; SUPERSEDED status |
| Sensitive logging | Medium | Medium | No PII in logs, structured logging only |
| Dependency compromise | Low | Critical | Dependabot, lockfile, minimal dependencies |

## Security controls

### Authentication
- Single Supabase Auth user
- Email/password or magic link
- Optional TOTP MFA (enforced for admin operations)
- Session timeout: 24 hours (configurable)
- Rate limiting: 5 login attempts per minute

### Authorization
- RLS on every table
- owner_id column on all private rows
- Service-role operations restricted to server-side code
- Server actions validate session before mutation

### Data integrity
- Model snapshot integrity hash verified on import
- Transaction idempotency keys prevent duplicates
- Immutable after PUBLISHED status
- Correction events preserve audit trail
- CHECK constraints on status transitions

### Input validation
- All user inputs validated on client and server
- CSV import: column whitelist, max 1000 rows
- Monetary values: NUMERIC(14,2) in database
- Quantities: NUMERIC(14,6) with CHECK > 0 for most events

### Network security
- HTTPS enforced
- Content Security Policy headers
- No third-party CDN scripts
- API routes validate origin

### Data protection
- Supabase backups enabled
- Periodic encrypted export to secure storage
- No PII in application logs
- Environment variables never committed

### Audit
- All import events logged
- All status transitions logged
- All correction events logged
- Login attempts logged
- Export operations logged
