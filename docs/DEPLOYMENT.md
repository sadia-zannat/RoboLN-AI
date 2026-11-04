# Deployment preparation — not deployed

`render.yaml`, backend/frontend Dockerfiles, env templates, health/readiness endpoints, database migrations and lockfiles are included. No service or repository was created.

## API

Root directory `backend`; build `pip install -r requirements.lock`; start `python -m alembic upgrade head && python -m uvicorn app.api:app --host 0.0.0.0 --port $PORT`. Use Python 3.12. Set `ROBOLN_DATABASE_URL` to durable PostgreSQL using `postgresql+psycopg://...`, `ROBOLN_COOKIE_SECURE=true`, and `ROBOLN_ALLOWED_ORIGINS` to the exact HTTPS frontend origin. Set the provider key on the API service only.

`/api/health` reports configured capabilities, not external inference. `/api/ready` verifies database availability/schema. Use one migration runner during rollout. Back up the database before schema upgrades. Sources and normalized evidence images are stored in the same database, so database storage and backup capacity must account for binary content.

A live PostgreSQL instance and cloud environment have not been exercised here. Local SQLite migration and HTTP tests are separate from cloud commissioning. Default ephemeral service disks must not hold your production SQLite database.

## Frontend

Root directory `frontend`; build `npm ci && npm run build`; start with a server bound to `0.0.0.0` and the supplied port. `ROBOLN_BACKEND_URL` is the trusted API origin read by the explicit server proxy at runtime. Restart the frontend server after changing it; a rebuild is not needed for this URL. This is a Node server application, not static export. Browser requests remain same-origin `/api/...` and are proxied server-side. No model key belongs in a frontend variable.

Keep the proxy and cookies on the same public origin; allow that origin in the API settings. Set HTTPS at the ingress. Do not publish backend API docs or expose unrestricted registration without considering rate limits, abuse controls and operational monitoring appropriate to your deployment.

## Security and operations

Review `SECURITY.md`. Configure ingress request limits and timeouts, TLS, database backups, logging retention and storage quotas. Verify cookies are Secure and HttpOnly for the session, CSRF mutations fail without their token, forbidden origins fail, and one project cannot access another. Check both anonymous and signed-in error pages.

The package's automated tests do not prove cloud isolation, TLS configuration, availability, load capacity, disaster recovery or hardware safety. Dockerfiles and Render configuration are preparation artifacts, not executed deployment evidence.
