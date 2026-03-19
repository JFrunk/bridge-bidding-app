# Vendor & Software Inventory

**Project:** My Bridge Buddy (mybridgebuddy.com)
**Last Updated:** 2026-03-19

---

## AI & Development Tools

| Tool | Purpose | Cost |
|------|---------|------|
| Claude Code (in VS Code) | Coding assistant | Anthropic subscription |
| Gemini | Strategy / brainstorming | Google subscription |

## Hosting & Infrastructure

| Vendor | Purpose | Details | Cost |
|--------|---------|---------|------|
| Hetzner Cloud | App server (app.mybridgebuddy.com) | CPX11: 2 vCPU AMD, 2GB RAM, 40GB SSD, Ubuntu 24.04 | $5.59/mo |
| GitHub Pages | Landing page (mybridgebuddy.com) | Static site hosting | Free |
| Oracle Cloud | Legacy/backup (unused) | Two AMD micro instances, Phoenix | Free tier |

## Domain & DNS

| Vendor | Purpose | Details |
|--------|---------|---------|
| Squarespace (ex-Google Domains) | Domain registrar & DNS | mybridgebuddy.com, app.mybridgebuddy.com |
| Let's Encrypt | SSL certificates | Auto-renewed via certbot on Hetzner |

## Code & CI/CD

| Vendor | Purpose | Details | Cost |
|--------|---------|---------|------|
| GitHub | Source control & CI/CD | GitHub Actions for testing, QA, deploy | Free tier |
| Codecov | Code coverage reporting | Via GitHub Actions | Free tier |

## Email & Communication

| Vendor | Purpose | Details |
|--------|---------|---------|
| Google (Gmail) | Project email | mybridgebuddy@gmail.com — SMTP for transactional auth emails & notifications |

## Authentication

| Vendor | Purpose | Details |
|--------|---------|---------|
| Google Cloud (OAuth 2.0) | Google Sign-In | Client ID: `735702527242-...apps.googleusercontent.com` — ID token verification via `google-auth` library |
| argon2-cffi | Password hashing | Argon2id with RFC 9106 defaults |
| PyJWT | JWT access tokens | HS256, 15-min expiry |

## Analytics & Monitoring

| Vendor | Purpose | Details |
|--------|---------|---------|
| Google Analytics 4 | User & gameplay analytics | Measurement ID: G-NPEBZNPK88, via react-ga4 |
| Sentry | Error tracking (frontend + backend) | Free tier: 5K errors/mo, 10K perf spans/mo |

## Database & Caching

| Software | Purpose | Details |
|----------|---------|---------|
| PostgreSQL | Primary database | Local: `bridge_app`, Production: `bridge_bidding` |
| Redis | Session/cache management | Optional, with fakeredis fallback for dev |

## Backend Stack

| Software | Purpose |
|----------|---------|
| Python 3.12 | Runtime |
| Flask 3.0+ | Web framework / REST API |
| Gunicorn | Production WSGI server |
| endplay (DDS) | Double dummy solver — Linux x86_64 only |
| psycopg2 | PostgreSQL adapter |
| argon2-cffi | Argon2id password hashing |
| PyJWT | JWT token creation/verification |
| google-auth | Google OAuth ID token verification |
| python-dotenv | Environment config |
| pytest | Testing framework |

## Frontend Stack

| Software | Purpose |
|----------|---------|
| React 18.3 | UI framework |
| Tailwind CSS 3.4 | Styling |
| Radix UI | Accessible dialog/collapsible components |
| Lucide React | Icon library |
| Playwright | End-to-end testing |
| @testing-library/react | Unit testing |
| html2canvas | Screenshot/export |
| @letele/playing-cards | SVG card graphics |

## QA & Reference

| Tool | Purpose |
|------|---------|
| WBridge5 (via Docker/Wine) | Baseline bid comparison & validation |

## Notable Absences

- No payment processing (free pedagogical tool)
- ~~No external auth provider~~ — Google OAuth added, plus password + magic link auth
- ~~No error tracking service~~ — Sentry added (free tier)
- No APM/monitoring (DataDog, New Relic, etc.)
- No CDN
- No dedicated mail service (direct Gmail SMTP)
