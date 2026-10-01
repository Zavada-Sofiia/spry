# PROJECT.md — Spry Monorepo

## Overview

`spry` is a monorepo structured for containerized local development. 

### Developer Onboarding
1. Install Docker Desktop.
2. Run:
   ```bash
   docker compose up
   ```

---

## Tooling & Version Pinning

- **Database Engine**: PostgreSQL `16.2`
- **Backend Stack**:
  - Python `3.12.2`
  - FastAPI `0.110.0`
  - SQLAlchemy `2.0.28`
  - Alembic `1.13.1`
- **Frontend Stack**:
  - Node.js `20.11.1`
  - React `18.2.0`
  - Vite `5.1.4`
  - Tailwind CSS `3.4.1`
  - shadcn/ui `0.8.0`

---

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

* **`/` (Root)**: Monorepo root containing orchestration definitions (`docker-compose.yml`) and project documentation (`PROJECT.md`).
* **`backend/`**: Contains the FastAPI web application, SQLAlchemy ORM data models, and API route definitions.
* **`backend/alembic/`**: Contains database migration scripts and configuration managed by Alembic.
* **`frontend/`**: Contains the React single-page application built with Vite, Tailwind CSS, and shadcn/ui components.

---

## Docker Services (`docker-compose.yml`)

### 1. `postgres`
* **Listening Port**: `5432`
* **Dependencies**: None
* **Readiness Check**: Uses `pg_isready -U postgres` to verify database readiness before dependent services launch.

### 2. `backend`
* **Listening Port**: `8000`
* **Dependencies**: `postgres`
* **Readiness Check**: Depends on `postgres` reaching `service_healthy` status via `pg_isready`. Signals its own readiness via an HTTP check returning status `200 OK` on `GET /api/meetings`.

### 3. `frontend`
* **Listening Port**: `3000`
* **Dependencies**: `backend`
* **Readiness Check**: Depends on `backend` reaching `service_healthy` status on port `8000`.

---

## Slice 1 Contracts & Specifications

### Data Model: Meeting
* `id`: Integer (Primary Key, Auto-increment)
* `title`: String
* `starts_at`: ISO 8601 Timestamp
* `ends_at`: ISO 8601 Timestamp
* `attendee_count`: Integer

### API Contract (`backend` <-> `frontend`)

#### `GET /api/meetings`
* **Description**: Returns a list of all meetings.
* **Request**: None
* **Response**: JSON array of Meeting objects.

#### `POST /api/meetings`
* **Description**: Creates a new meeting.
* **Request Payload**:
  * `title`: String
  * `starts_at`: ISO 8601 Timestamp
  * `ends_at`: ISO 8601 Timestamp
  * `attendee_count`: Integer
* **Response**: Created Meeting object with generated `id`.

### Frontend Interface Contract
* Single-page layout containing:
  1. **Meetings List**: Displays existing meetings fetched from `GET /api/meetings`.
  2. **Creation Form**: Form using shadcn/ui components that posts new meeting data to `POST /api/meetings` and updates the meetings list upon success.