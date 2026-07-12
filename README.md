# Health Assistant API — Project 1: REST API Fundamentals

A simple REST API built with **FastAPI** as part of the DecodeLabs Backend Development internship (Project 1: REST API Fundamentals). This project demonstrates core REST concepts such as: stateless routing, GET/POST methods, JSON serialization, and proper HTTP status codes — by managing patient records for a health assistant system.

## Tech Stack

- **Python 3**
- **FastAPI** — web framework
- **Pydantic** — request/response data validation
- **Uvicorn** — ASGI server used to run the app locally

## Features

- Register a new patient via `POST`
- Retrieve all registered patients via `GET`
- Retrieve a single patient by ID via `GET`
- Auto-generated, sequential patient IDs (year-prefixed)
- Passwords are excluded from all API responses
- Proper HTTP status codes (`201` on creation, `404` when a patient isn't found)

## Data Model

**Patient (request body for registration):**

| Field           | Type   | Description                  |
|-----------------|--------|------------------------------|
| `patient_Name`  | string | Patient's full name          |
| `Age`           | int    | Patient's age                |
| `Email`         | string | Patient's email address      |
| `password`      | string | Account password             |

**PatientResponse (what the API returns):**

| Field           | Type   | Description                  |
|-----------------|--------|------------------------------|
| `patient_id`    | string | Auto-generated unique ID     |
| `patient_Name`  | string | Patient's full name          |
| `Email`         | string | Patient's email address      |

> Note: `password` is intentionally never included in any response.

## Patient ID Format

Each new patient is assigned an ID automatically — the client never provides one. IDs follow the format:

```
2026 + a 4-digit sequential number
```

Example: the first patient created gets `20260001`, the second gets `20260002`, and so on. The counter increases only when a patient is successfully created.

## Endpoints

### `POST /patients/create_patient`
Creates a new patient record.

**Request body:**
```json
{
  "patient_Name": "Adeyanju Feranmi",
  "Age": 15,
  "Email": "adeyanju@example.com",
  "password": "mypassword"
}
```

**Response — `201 Created`:**
```json
{
  "patient_id": "20260001",
  "patient_Name": "Adeyanju Feranmi",
  "Email": "adeyanju@example.com"
}
```

---

### `GET /get_patient`
Returns a list of all registered patients.

**Response — `200 OK`:**
```json
[
  {
    "patient_id": "20260001",
    "patient_Name": "Adeyanju Feranmi",
    "Email": "adeyanju@example.com"
  }
]
```

---

### `GET /patients/{patient_id}`
Returns a single patient by their ID.

**Example:** `GET /patients/20260001`

**Response — `200 OK`:**
```json
{
  "patient_id": "20260001",
  "patient_Name": "Adeyanju Feranmi",
  "Email": "adeyanju@example.com"
}
```

**Response — `404 Not Found`** (if the ID doesn't exist):
```json
{
  "detail": "Patient Not Found"
}
```

## Running the Project Locally

1. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn
   ```

2. **Run the server:**
   ```bash
   python -m uvicorn HealthAssistant:app --reload
   ```
   (replace `HealthAssistant` with your actual filename if different)

3. **Open the interactive API docs:**
   Visit `http://127.0.0.1:8000/docs` in your browser. FastAPI auto-generates a Swagger UI where every endpoint can be tested directly — no separate tool like Postman required.

## Known Limitations

This project intentionally keeps things simple, in line with "Project 1: Fundamentals":

- **No persistent database** — all data is stored in an in-memory Python dictionary (`patient_db`). Every time the server restarts, all data is lost. This will be addressed in a later project stage, likely to use SQL Database.
- **Passwords are stored in plaintext** — acceptable for a fundamentals exercise, but as production system continues passwords would be  hashed before storing them.
- **No authentication** — anyone can call any endpoint. Future iterations may add doctor accounts with role-based access.

## Author

Feranmi — Backend Developer Intern, DecodeLabs (2026 july Batch)