# Clevia Beauty Clinic — Backend

Backend MVP untuk website public, CRM, appointments, knowledge base, dan AI chatbot Clevia.

## Stack
- Python 3.12
- FastAPI
- PostgreSQL 16 + pgvector
- Redis
- SQLAlchemy async + Alembic
- OpenAI Responses API
- Docker Compose

## Install
```bash
cp .env.example .env
```

Isi minimal:
```env
JWT_SECRET=buat-secret-yang-panjang
OPENAI_API_KEY=sk-...
```

Lalu:
```bash
docker compose up -d --build
docker compose exec api python -m scripts.seed
```

Swagger:
`http://localhost:8000/docs`

Seed login:
- email: `owner@clevia.local`
- password: `ChangeMe123!`

Ganti password sebelum deployment nyata.

## Endpoint utama
Public:
- GET `/api/v1/public/clinic`
- GET `/api/v1/public/services`
- GET `/api/v1/public/staff`
- GET `/api/v1/public/availability`
- POST `/api/v1/public/appointment-requests`
- POST `/api/v1/public/conversations`
- POST `/api/v1/public/conversations/{id}/messages`

CRM:
- POST `/api/v1/auth/login`
- GET `/api/v1/auth/me`
- GET/POST/PATCH `/api/v1/crm/leads`
- GET/POST `/api/v1/crm/clients`
- GET/POST `/api/v1/appointments`
- GET `/api/v1/conversations`
- POST `/api/v1/conversations/{id}/takeover`
- POST `/api/v1/conversations/{id}/release`
- GET/POST `/api/v1/knowledge`
- POST `/api/v1/knowledge/{id}/publish`

## Important
CRM ini bukan EMR/EHR. Jangan menyimpan diagnosis, resep, atau detail rekam medis di `administrative_notes`.

Knowledge retrieval di v0.1 masih SQL text search. PostgreSQL pgvector sudah disiapkan untuk fase RAG embeddings berikutnya.


## Windows PowerShell Installer

Extract ZIP, buka PowerShell di folder project, lalu:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

Installer akan:

1. mengecek Docker + Docker Compose;
2. membuat `.env` bila belum ada;
3. membuat `JWT_SECRET` random;
4. build image Docker;
5. start FastAPI + PostgreSQL/pgvector + Redis;
6. menjalankan seed demo Clevia.

Jika `OPENAI_API_KEY` belum diisi, backend tetap hidup tetapi chatbot AI belum aktif.

Setelah mengisi API key:

```powershell
docker compose restart api
```


## Redis Caching Strategy

Clevia menggunakan cache-aside:

```text
Request
  -> Redis lookup
     -> HIT: return cached JSON
     -> MISS: query PostgreSQL -> cache result -> return
```

Cached sekarang:

- public clinic profile: 15 menit;
- public services: 5 menit;
- public staff: 5 menit;
- appointment availability: 30 detik.

Availability otomatis diinvalidate setelah appointment berhasil dibuat.

Tidak dicache secara default:

- login response;
- raw CRM leads/clients;
- private conversation messages;
- audit log;
- write operations.

Namespace key:

```text
clevia:v1:public:clinic
clevia:v1:public:services:{clinic_id}:{category}
clevia:v1:public:staff:{clinic_id}
clevia:v1:availability:{clinic_id}:{service_id}:{date}:{staff_id}
```

Gunakan `SCAN`, bukan `KEYS`, untuk invalidation berbasis pattern.
