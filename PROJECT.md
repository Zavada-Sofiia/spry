# PROJECT.md — Spry Monorepo

## Overview

`spry` is a monorepo structured for containerized local development.

### Developer Onboarding

1. Install Docker Desktop.
2. Run:
   ```bash
   docker compose up
   ```

## Repository Structure

```
spry/
├── docker-compose.yml
├── PROJECT.md
├── backend/
│   └── alembic/
└── frontend/
```

### Folder Purpose Definitions

* **`/` (Monorepo Root)**: Global orchestration (`docker-compose.yml`) and project specification (`PROJECT.md`).
* **`backend/`**: FastAPI backend service, database models (SQLAlchemy), and API routes.
* **`backend/alembic/`**: Alembic database migration scripts and migration environment config.
* **`frontend/`**: React single-page application built with Vite, Tailwind CSS, and shadcn/ui components.

---

## Tooling & Docker Image Pinning

### Docker Base Images
* `postgres`: `postgres:16.2-alpine`
* `backend`: `python:3.12.2-slim`
* `frontend`: `node:20.11.1-alpine`

### Software Tooling Versions
* **Database**: PostgreSQL `16.2`
* **Backend**: Python `3.12.2`, FastAPI `0.110.0`, SQLAlchemy `2.0.28`, Alembic `1.13.1`
* **Frontend**: Node `20.11.1`, React `18.2.0`, Vite `5.1.4`, Tailwind CSS `3.4.1`, shadcn/ui `0.8.0`

---

## Docker Services (`docker-compose.yml`)

### 1. `postgres`
* **Port**: `5432:5432`
* **Dependencies**: None
* **Healthcheck**: `pg_isready -U postgres -d spry`
* **Readiness Criteria**: Responds with exit code `0`.

### 2. `backend`
* **Port**: `8000:8000`
* **Dependencies**: `postgres` (condition: `service_healthy`)
* **Startup Mechanics**:
  1. Wait for `postgres` healthcheck to pass.
  2. Run `alembic upgrade head`.
  3. Start Uvicorn (`uvicorn main:app --host 0.0.0.0 --port 8000`).
* **Healthcheck**: `curl -f http://localhost:8000/api/meetings` returning `200 OK`.

### 3. `frontend`
* **Port**: `3000:3000`
* **Dependencies**: `backend` (condition: `service_healthy`)
* **Startup Mechanics**:
  1. Wait for `backend` healthcheck to pass.
  2. Run `npm run dev` (Vite dev server on port `3000`).

---

## Slice 1 Contracts & Specifications

### Data Schema: `Meeting`
* `id` (`integer`, primary key, auto-increment)
* `title` (`string`, required)
* `starts_at` (`datetime`, ISO 8601 UTC string: `YYYY-MM-DDTHH:MM:SSZ`)
* `ends_at` (`datetime`, ISO 8601 UTC string: `YYYY-MM-DDTHH:MM:SSZ`)
* `attendee_count` (`integer`, non-negative)

---

### API Contracts

#### `GET /api/meetings`
* **Response Status**: `200 OK`
* **Response Content-Type**: `application/json`
* **Response Body**:
  ```json
  [
    {
      "id": 1,
      "title": "Sprint Planning",
      "starts_at": "2026-10-01T10:00:00Z",
      "ends_at": "2026-10-01T11:00:00Z",
      "attendee_count": 5
    }
  ]
  ```

#### `POST /api/meetings`
* **Request Content-Type**: `application/json`
* **Request Body**:
  ```json
  {
    "title": "Design Review",
    "starts_at": "2026-10-02T14:00:00Z",
    "ends_at": "2026-10-02T15:00:00Z",
    "attendee_count": 3
  }
  ```
* **Response Status**: `201 Created`
* **Response Content-Type**: `application/json`
* **Response Body**:
  ```json
  {
    "id": 2,
    "title": "Design Review",
    "starts_at": "2026-10-02T14:00:00Z",
    "ends_at": "2026-10-02T15:00:00Z",
    "attendee_count": 3
  }
  ```

---

### Frontend UI Contract
* **Route**: `/` (Single Page)
* **Functionality**:
  1. **Meetings List**: Calls `GET /api/meetings` on load and displays meeting title, formatted start/end times, and attendee count.
  2. **Add Meeting Form**: Built with shadcn/ui controls (`Input`, `Button`, `Label`). Submits `POST /api/meetings` and updates the list upon `201 Created`.