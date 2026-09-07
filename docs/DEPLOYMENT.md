# Deployment

## Environments

- Local: Docker Compose.
- CI: build/test frontend và backend.
- Demo/Production: cấu hình qua environment variables, không bake secret vào image.

## Required services

- PostgreSQL 16
- Python/FastAPI API
- Static frontend served by Nginx
- Private persistent volume cho CV

MailHog chỉ dùng local; AI provider có thể tắt bằng `AI_PROVIDER=none`.
