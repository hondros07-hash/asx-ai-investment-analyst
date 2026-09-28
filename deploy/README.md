# AXÍA V24.4 — Stage 5: controlled production deployment

**This PR provides release tooling, not a live cutover.** Keep the current Streamlit website and DNS untouched until a separate explicit approval. The new frontend still lacks authenticated saved portfolios/watchlists/alerts, official non-US disclosures, and full report analysis; do not describe it as feature-complete.

## Staging prerequisites
- A Linux host with Docker Compose and an HTTPS reverse proxy; a dedicated staging subdomain; DNS and valid TLS.
- Configure AXIA_SITE_URL to the exact staging HTTPS origin and AXIA_FRONTEND_PORT to a free loopback port. Do not put secrets in the repository.
- The API is accessible only on the internal Docker network. Expose the frontend only on 127.0.0.1 and proxy HTTPS to that port.
- Set AXIA_SEC_USER_AGENT with a genuine application name and contact only when official SEC retrieval is required. Confirm provider terms, rate limits and production usage.
- Do not reuse production credentials or copy user holdings into staging.

## Build and validate
From repository root: `AXIA_SITE_URL=https://YOUR-STAGING-HOST docker compose -f deploy/compose.yaml up -d --build`. Check `docker compose -f deploy/compose.yaml ps`, then `AXIA_SMOKE_ORIGIN=https://YOUR-STAGING-HOST python scripts/deployment_smoke.py`. CI builds both images and smoke-tests the local public routes. Liveness and readiness at /health/live and /health/ready indicate API process readiness, **not provider data health**.

## Manual release gates (record evidence)
1. CI backend/frontend/image/smoke jobs green on the release commit.
2. Home, Search, 11 Company Command Centre sections, seven workspace routes, footer and SEO pages reviewed on mobile/tablet/desktop.
3. Compare KO, ZIP.AX and QAN.AX prices, identities, currencies, dates and issuer disclosures. Test stale, empty and provider-failure states.
4. Confirm no unauthenticated private data access or alert delivery claims. Confirm all remaining feature gaps are acceptable to release owner.
5. Verify staging robots/canonical and sitemap target staging; decide production indexing and canonical behaviour before DNS changes.
6. Verify TLS, reverse proxy, logs, monitoring, resource limits, backups and access restrictions with the chosen host.
7. Record approval, image digest, rollback target, deploy timestamp and owner. No automatic DNS change or production deploy occurs in GitHub Actions.

## Cutover and rollback
Only after approval, deploy the reviewed image digests to production behind the proxy; use a reversible traffic/DNS change. Keep Streamlit running and its configuration backed up. If API errors, financial mismatches, privacy issues or material navigation regressions occur, revert the proxy/DNS to Streamlit, verify its home and company routes, and preserve logs for diagnosis. DNS propagation may delay rollback; proxy routing is preferable when available.

## Limitations
The compose file is a reference for a self-managed Linux Docker host, not a configured cloud account. Deployment credentials, DNS, TLS, persistent authenticated data, live provider verification and production monitoring require environment-specific setup. Do not merge solely because CI passes.
