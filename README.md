# Health Assistant API  DecodeLabs Backend Development Internship (2026 Batch)

A backend system for a health assistant application, built progressively across the DecodeLabs internship's project series. This README covers every project completed so far and will be updated as each new stage is implemented.


## Overall Tech Stack

- **Python 3** / **FastAPI** — web framework
- **Pydantic** — request/response validation
- **PostgreSQL** — relational database (Project 2 onward)
- **SQLAlchemy** — ORM (Project 2 onward)
- **Argon2id** — password hashing (Project 2 onward)
- **python-dotenv** — environment variable management (Project 2 onward)
- **Uvicorn** — ASGI server

---
---

# Project 1 — REST API Fundamentals

**Location:** `project1/`

Introduces core REST concepts: stateless routing, GET/POST methods, JSON serialization, and proper HTTP status codes. Data is stored in an in-memory Python dictionary — no database yet.

## Features

- Register a new patient (`POST`)
- Retrieve all patients / a single patient by ID (`GET`)
- Auto-generated, sequential patient IDs
- Passwords excluded from all responses

## Data Model

**Request body (`Patient`):**

| Field | Type |
|---|---|
| `patient_Name` | string |
| `Age` | int |
| `Email` | string |
| `password` | string |

**Response body (`PatientResponse`):**

| Field | Type |
|---|---|
| `patient_id` | string |
| `patient_Name` | string |
| `Email` | string |

> `password` is never included in any response.

## Patient ID Format

```
2026 + a 4-digit sequential number
```
Example: `20260001`, `20260002`, etc. The counter only increases when a patient is successfully created.

## Endpoints

**`POST /patients/create_patient`** — creates a new patient.
```json
{
  "patient_Name": "John Doe",
  "Age": 30,
  "Email": "john@example.com",
  "password": "mypassword"
}
```
→ `201 Created`

**`GET /get_patient`** — returns all patients.

**`GET /patients/{patient_id}`** — returns one patient by ID.
→ `404 Not Found` if the ID doesn't exist

## Running Locally

```bash
cd project1
pip install fastapi uvicorn
python -m uvicorn HealthAssistant:app --reload
```
Open `http://127.0.0.1:8000/docs`.

## Known Limitations

- No persistent database — all data is lost on server restart
- Passwords stored in plain text — acceptable for a fundamentals exercise only
- No authentication

---
---

# Project 2 — Database Integration (CRUD)

**Location:** `project2/`

Connects the API to a real **PostgreSQL** database via SQLAlchemy, replacing Project 1's in-memory storage with permanent persistence. Adds full CRUD, a second user role (doctors), and password security.

## Features

- Full CRUD for patients and doctors — Create, Read, Update, Delete
- Real, persistent storage — data survives server restarts
- Staff ID approval system — a doctor can only register with a staff ID the hospital has pre-approved
- Admin login — fixed admin account, email + password
- Duplicate email prevention — enforced at the database level (`UNIQUE` constraint), returns `409 Conflict`
- Passwords hashed with **Argon2id** — never stored or returned in plain text
- Secrets loaded from `.env` — no credentials hardcoded in source

## Data Model

### Patient

**Request body (`Patient`):**

| Field | Type | Notes |
|---|---|---|
| `patient_Name` | string | |
| `Age` | int | |
| `Patient_gender` | enum | `"Male"` or `"Female"` |
| `Email` | string | must be unique |
| `password` | string | hashed before storage |

**Response body (`PatientResponse`):**

| Field | Type |
|---|---|
| `patient_id` | string |
| `patient_Name` | string |
| `Email` | string |

### Doctor

**Request body (`Doctor`):**

| Field | Type | Notes |
|---|---|---|
| `staff_id` | string | must already be on the approved list |
| `doctor_Name` | string | |
| `specialization` | string | |
| `Email` | string | must be unique |
| `password` | string | hashed before storage |

**Response body (`DoctorResponse`):**

| Field | Type |
|---|---|
| `staff_id` | string |
| `doctor_Name` | string |
| `specialization` | string |
| `Email` | string |

### Approved Staff

**Request body (`ApprovedStaffCreate`):**

| Field | Type |
|---|---|
| `staff_id` | string |
| `staff_Name` | string |
| `Email` | string |

## Patient ID Format

```
2026 + a 4-digit sequential number
```
Example: `20260001`, `20260002`. Unlike Project 1, the next number is determined by querying the highest existing ID already in the database — so numbering stays correct even across server restarts.

## Endpoints

### Patients

**`POST /patients/create_patient`**
```json
{
  "patient_Name": "Adeyanju Feranmi",
  "Age": 15,
  "Patient_gender": "Male",
  "Email": "adeyanju@example.com",
  "password": "mypassword"
}
```
→ `201 Created` · `409 Conflict` if the email already exists

**`GET /get_patient`** — returns all patients.

**`GET /patients/{patient_id}`** → `404` if not found

**`PUT /patients/{patient_id}`** — same body as create. → `409` on duplicate email, `404` if not found

**`DELETE /patients/{patient_id}`** → `204 No Content` · `404` if not found

### Doctors

**`POST /doctors/register`**
```json
{
  "staff_id": "DOC-1001",
  "doctor_Name": "Dr. Grace Okafor",
  "specialization": "Cardiology",
  "Email": "youremail@gmail.com",
  "password": "yourpassword"
}
```
→ `201 Created` · `403 Forbidden` if the staff ID isn't approved · `409 Conflict` if already registered or email taken

**`GET /doctors`** — returns all registered doctors.

**`GET /doctors/{staff_id}`** → `404` if not found

**`PUT /doctors/{staff_id}`** — updates a doctor's details.

**`DELETE /doctors/{staff_id}`** → `204 No Content`

### Admin

**`POST /admin/login`**
```json
{
  "email": "youremail@gmail.com",
  "password": "changeme123"
}
```
→ `200 OK` on success · `401 Unauthorized` on wrong credentials

**`POST /admin/approve_staff`** — must happen before a doctor with that staff ID can register.
```json
{
  "staff_id": "DOC-1001",
  "staff_Name": "Dr. Grace Okafor",
  "Email": "youremail@gmail.com"
}
```
→ `201 Created` · `409 Conflict` if already approved

**`GET /admin/approved_staff`** — lists every approved staff ID.

## Running Locally

```bash
cd project2
pip install fastapi uvicorn sqlalchemy psycopg2-binary argon2-cffi python-dotenv

# Create the database:
#   CREATE DATABASE health_assistant;

# Create a .env file (see .env.example):
#   DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/health_assistant
#   ADMIN_EMAIL= youremail.com
#   ADMIN_PASSWORD=yourpassword

python -m uvicorn HealthAssistant_2:app --reload
```
Open `http://127.0.0.1:8000/docs`.

**Verifying persistence:** create a patient, stop the server, restart it, then fetch that patient again — the data should still be there.

## Known Limitations

- Admin login checks credentials but doesn't yet issue/require a token , other admin routes aren't gated behind authentication yet (JWT scaffolding exists in `auth.py`, ready to wire in later)
- Only one fixed admin account, not a full admin table
- No automated tests yet

---
---

# Roadmap — Planned for Future Projects

- JWT-based authentication and route protection
- Appointments linking patients to doctors
- Prescriptions tied to specific appointments
- Test results / lab reports
- Role-based access control (a patient can only view their own records; a doctor only their assigned patients)

*This section, and the project sections above, will be updated as each new project stage is completed.*

## Security Notes

- Real credentials (database password, admin password) live in a `.env` file, excluded from version control via `.gitignore`. A `.env.example` file is provided as a safe template.
- Passwords are hashed with Argon2id before storage — they cannot be reversed, only verified.



 
# Project 3 — Secure Authentication System
 
**Location:** `project3/`
 
Adds modern authentication on top of Project 2's data layer: JWT-based login, role-protected routes, and — extending beyond the base brief — a full appointment booking and negotiation system connecting patients and doctors.
 
## Features
 
- **JWT authentication** for three roles: admin, doctor, patient — each login issues a signed token carrying the user's role
- **Role-protected routes** — `require_admin`, `require_doctor`, `require_patient` dependencies gate access; missing/invalid tokens return `401`, valid-but-wrong-role returns `403`
- **Admin-controlled staff approval** — a doctor can only register if their `staff_id` is already on an admin-managed approved list (`POST /admin/approve_staff`)
- **Doctor search** — patients can find a doctor by name and/or specialization instead of needing to know a raw staff ID
- **Full appointment negotiation flow** — a patient books a time; the doctor can confirm, decline, or propose an alternative time; the patient then accepts or declines that alternative
- **Ownership checks throughout** — a doctor can only respond to/update *their own* appointments; a patient can only view/respond to *their own* — enforced by looking up the record from the JWT, never trusting an ID supplied in the request
- Secrets (`DATABASE_URL`, `JWT_SECRET_KEY`, admin credentials) loaded from `.env`, excluded from version control
## Authentication
 
| Endpoint | Who | Returns |
|---|---|---|
| `POST /admin/login` | Fixed admin account | JWT (`role: admin`) |
| `POST /doctors/login` | Registered doctor | JWT (`role: doctor`) |
| `POST /patients/login` | Registered patient | JWT (`role: patient`) |
 
Tokens are passed via `Authorization: Bearer <token>` on protected routes — in Swagger, click **Authorize** and paste the token directly (no "Bearer" prefix needed).
 
## Data Model — Appointments
 
| Field | Type | Notes |
|---|---|---|
| `appointment_id` | string | Auto-generated, format `APP-00001` |
| `patient_id` | string | Foreign key -> `patients.patient_id` |
| `staff_id` | string | Foreign key -> `doctors.staff_id` |
| `appointment_date` | datetime | |
| `appointment_time` | datetime | |
| `proposed_time` | datetime, nullable | Set only while status is `alternative_proposed` |
| `status` | enum | `pending`, `confirmed`, `alternative_proposed`, `declined`, `completed`, `cancelled` |
 
## Appointment Lifecycle
 
```
pending
  -> doctor confirms              -> confirmed -> completed
  -> doctor declines              -> declined  (closed)
  -> doctor proposes alternative  -> alternative_proposed
                                       -> patient accepts  -> confirmed -> completed
                                       -> patient declines -> declined   (closed)
```
 
Every path ends in either `completed` or `declined`/`cancelled` — a closed, finite state machine. If a proposed time doesn't suit the patient, they decline and book a fresh new appointment rather than an open-ended counter-negotiation.
 
## Endpoints
 
### Doctor Search
**`GET /doctors/search?name=...&specialization=...`** — partial, case-insensitive match on either field. Requires any valid login.
 
### Appointments
- **`POST /appointments`** *(patient only)* — book a new appointment (always starts `pending`)
- **`GET /appointments`** *(admin/doctor only)* — view all appointments
- **`GET /patients/me/appointments`** *(patient only)* — view own bookings
- **`GET /doctors/me/appointments`** *(doctor only)* — view bookings made with them
- **`PUT /appointments/{id}/doctor-response`** *(doctor only, own appointments)* — `{"action": "confirm" | "decline" | "propose_alternative", "proposed_time": ...}`
- **`PUT /appointments/{id}/patient-response`** *(patient only, own appointments)* — `{"action": "accept" | "decline"}`, only valid when status is `alternative_proposed`
- **`PUT /appointments/{id}/complete`** *(doctor only, own appointments)* — marks a `confirmed` appointment as `completed`
### Admin
- **`POST /admin/approve_staff`** *(admin only)* — `{"staff_id", "staff_Name", "Email"}`
- **`GET /admin/approved_staff`** *(admin only)*
## Running Locally
 
```bash
cd project3
pip install fastapi uvicorn sqlalchemy psycopg2-binary argon2-cffi python-dotenv "python-jose[cryptography]"
```
 
`.env` must include:
```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/health_assistant
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=yourpassword
JWT_SECRET_KEY=generate_with_python_secrets_token_hex_32
```
 
```bash
python -m uvicorn HealthAssistant:app --reload
```
Open `http://127.0.0.1:8000/docs`.
 
## Known Limitations
 
- No counter-negotiation loop — a declined proposed time closes the appointment; the patient must submit a new booking rather than continuing to haggle over the same slot (a deliberate scope decision, not an oversight)
- No email/SMS notifications yet on status changes — planned as the next external-API integration
- No automated tests yet
---
---
 
# Roadmap — Planned for Future Projects
 
- Email/SMS notifications on appointment status changes (planned external API integration)
- Prescriptions tied to completed appointments
- Doctor availability windows
- Medical history / visit notes
- Vitals tracking
- Pagination on list endpoints
- Automated tests (pytest)
*This section, and the project sections above, will be updated as each new project stage is completed.*
 
## Security Notes
 
- Real credentials live in `.env`, excluded from version control via `.gitignore`; `.env.example` provides a safe template
- Passwords hashed with Argon2id — irreversible, never stored or returned in plain text
- JWT signature key (`JWT_SECRET_KEY`) is a randomly generated 32-byte value, loaded from `.env`, never hardcoded


## Author

Feranmi — Backend Developer Intern, DecodeLabs (2026 Batch)