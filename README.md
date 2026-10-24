# BuildPay — Construction Payroll Management

Full-stack academic demo: HTML/CSS/JavaScript frontend + Python Flask REST API + SQLite database.

## Features
- Admin demo login and separate worker self-service portal
- Worker records stored in SQLite
- Add workers through the frontend and save them permanently
- Date-based attendance saved to SQLite
- Worker list, attendance, payroll preview, and report summary API endpoints
- Existing BuildPay dashboard, worker portal, payroll estimator, and CSV exports

## Run on Windows
1. Install Python 3.10 or newer from https://www.python.org/downloads/ (select “Add Python to PATH”).
2. Extract this ZIP folder.
3. Double-click `run_windows.bat`, or run these commands in this folder:
   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   python -m pip install -r requirements.txt
   python app.py
   ```
4. Open http://127.0.0.1:5000 in Chrome.

## Demo credentials
- Admin username: `admin`
- Admin password: `admin123`
- Six student worker IDs: `23491A1213`, `23491A1214`, `23491A1216`, `23491A1218`, `23491A1222`, `23491A1254`
- PIN for seeded workers: `1234`
- Additional demo worker IDs (BP1001 onward) also use PIN `1234`.

## Database
`buildpay.db` is created automatically the first time you run `python app.py`. It stores worker records and date-specific attendance. Keep the database file to preserve saved records.

## API endpoints
- `GET /api/health` — backend health check
- `GET /api/workers` — worker directory
- `POST /api/login` — demo login validation
- `POST /api/workers` — create a worker
- `GET /api/attendance?date=YYYY-MM-DD` — attendance records for a date
- `POST /api/attendance` — save attendance for a date
- `GET /api/payroll?days=26&overtime=6&deductions=300` — payroll estimates
- `GET /api/reports/summary` — totals and today's attendance summary

## Important limitations
This is a classroom prototype, not production payroll software. The login uses demo PINs and the admin credential is hard-coded. Before real use, implement hashed passwords, secure server-side sessions, CSRF protection, role-based authorization on write endpoints, input validation, audit logs, HTTPS, backups, and appropriate labour-law/payroll review. Do not use real worker personal data in this demo.
