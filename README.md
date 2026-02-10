# Q-Logic: Dynamic Schema Orchestration System

A full-stack system for uploading CSV data, inferring schemas, dynamically provisioning PostgreSQL tables, and providing an agent workspace with screen pop integration and employee tracking.

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌────────────┐
│   Angular    │───▶│   FastAPI    │───▶│ PostgreSQL │
│  Frontend    │◀───│   Backend    │◀───│            │
│  (Port 4200) │    │  (Port 8000) │    │ (Port 5432)│
└─────────────┘    └──────────────┘    └────────────┘
```

## Components

### 1. Schema Inference Engine
- Upload a CSV file, analyze first 100 rows
- Detect types: String, Integer, Float, Boolean, Date
- Identify primary key candidates

### 2. Schema Designer UI
- Mapping grid to edit display names, data types, and unique ID flags
- Provision button creates a dedicated PostgreSQL table

### 3. Dynamic Table Provisioning
- Executes `CREATE TABLE` DDL from finalized schemas
- Registry system (`source_metadata` + `column_metadata`) tracks all projects

### 4. Agent Workspace
- Dynamic task loading from project-specific tables
- Screen pop URL injection using the unique ID column

### 5. Employee Tracking
- State engine: Available, In-Task, Break, Wrap-up
- Task assignment and completion tracking
- AHT (Average Handle Time) calculation

## Quick Start

```bash
docker compose up --build
```

- **Frontend**: http://localhost:4200
- **Backend API**: http://localhost:8000/api
- **API Docs**: http://localhost:8000/docs

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/schema/infer` | Upload CSV and get inferred schema |
| POST | `/api/schema/provision` | Create table from finalized schema |
| GET | `/api/workspace/projects` | List all provisioned projects |
| GET | `/api/workspace/projects/{id}/records` | Fetch records from a dynamic table |
| POST | `/api/employees` | Register a new employee |
| PUT | `/api/employees/{id}/state` | Change employee state |
| POST | `/api/employees/{id}/tasks` | Assign a task |
| POST | `/api/employees/tasks/{id}/complete` | Complete a task |
| GET | `/api/employees/{id}/metrics/aht` | Get Average Handle Time |

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, asyncpg
- **Frontend**: Angular 17, Reactive Forms, standalone components
- **Database**: PostgreSQL 16
- **Infrastructure**: Docker Compose
