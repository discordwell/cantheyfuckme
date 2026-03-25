# Project: cantheyfuckme (Can They Fuck Me?)

**Domain**: cantheyfuckme.com (registrar: Cloudflare, transferring to Porkbun)

**Deployment**: Docker Compose on OVH2 VPS (15.204.59.61)
- App: FastAPI + React SPA (port 8081)
- Database: PostgreSQL 16
- TLS: Caddy (`/etc/caddy/sites/cantheyfuckme.com`)
- Deploy: `./deploy.sh`

**Stack**:
- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI + OpenAI
- Database: PostgreSQL 16
- Payments: Stripe (donation link)
