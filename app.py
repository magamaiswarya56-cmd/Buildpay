from flask import Flask, jsonify, request, render_template
import sqlite3
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "buildpay.db"
app = Flask(__name__)

SITES = [
    "Orchid Residency · Site A",
    "Metro Tower · Site B",
    "Riverfront Villas · Site C",
]

INITIAL_WORKERS = [
    ("23491A1213", "M.VYSHNAVI", "Mason", 850, SITES[0], "Skilled", "Pending", "1234"),
    ("23491A1214", "M.AISWARYA", "Electrician", 950, SITES[1], "Skilled", "Pending", "1234"),
    ("23491A1216", "N.GREESHMA", "Helper", 600, SITES[0], "Unskilled", "Pending", "1234"),
    ("23491A1218", "P.VARSHITHA", "Carpenter", 900, SITES[2], "Skilled", "Pending", "1234"),
    ("23491A1222", "A.KOWSHIK REDDY", "Plumber", 1000, SITES[1], "Skilled", "Pending", "1234"),
    ("23491A1254", "M.SANTHOSH", "Mason", 850, SITES[2], "Skilled", "Pending", "1234"),
    ("BP1001", "Ravi Kumar", "Mason", 850, SITES[0], "Skilled", "Completed", "1234"),
    ("BP1002", "Suresh Naidu", "Electrician", 950, SITES[1], "Skilled", "Completed", "1234"),
    ("BP1003", "Lakshmi Devi", "Painter", 750, SITES[0], "Semi-skilled", "Pending", "1234"),
    ("BP1004", "Arjun Reddy", "Carpenter", 900, SITES[1], "Skilled", "Completed", "1234"),
    ("BP1005", "Manoj Das", "Helper / General labour", 600, SITES[0], "Unskilled", "Pending", "1234"),
    ("BP1006", "Imran Khan", "Steel fixer", 875, SITES[2], "Skilled", "Completed", "1234"),
]

def connect_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

def init_db():
    with connect_db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS workers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            phone TEXT DEFAULT '',
            site TEXT NOT NULL,
            wage REAL NOT NULL CHECK(wage >= 0),
            type TEXT NOT NULL DEFAULT 'Skilled',
            emergency TEXT DEFAULT '',
            safety TEXT NOT NULL DEFAULT 'Pending',
            status TEXT NOT NULL DEFAULT 'Present',
            pin TEXT NOT NULL DEFAULT '1234',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id TEXT NOT NULL,
            work_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present','Late','Absent')),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(worker_id, work_date),
            FOREIGN KEY(worker_id) REFERENCES workers(id) ON DELETE CASCADE
        );
        """)
        count = con.execute("SELECT COUNT(*) FROM workers").fetchone()[0]
        if count == 0:
            for row in INITIAL_WORKERS:
                wid, name, role, wage, site, category, safety, pin = row
                con.execute(
                    """INSERT INTO workers
                    (id,name,role,site,wage,type,safety,status,pin)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (wid, name, role, site, wage, category, safety, "Present", pin)
                )
            roles = ["Helper / General labour", "Mason", "Electrician", "Plumber",
                     "Carpenter", "Machine operator", "Painter", "Steel fixer",
                     "Site supervisor", "Helper / General labour", "Mason", "Plumber"]
            names = ["Kiran Kumar", "Ramesh Babu", "Anil Prasad", "Vijay Rao",
                     "Sita Ram", "Naveen Kumar", "Raju", "Mohan", "Prakash",
                     "Kavitha", "Ravi Teja", "Srinivas"]
            wages = [600, 750, 850, 900, 950, 700, 800, 875, 1200, 600, 850, 900]
            for i in range(12):
                wid = f"BP{1007+i}"
                con.execute(
                    """INSERT INTO workers
                    (id,name,role,site,wage,type,safety,status,pin)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (wid, names[i], roles[i], SITES[i % 3], wages[i],
                     "Unskilled" if wages[i] <= 650 else "Skilled",
                     "Pending" if i % 4 == 0 else "Completed",
                     "Absent" if i % 10 == 0 else ("Late" if i % 7 == 0 else "Present"),
                     "1234")
                )

def worker_dict(row, include_pin=False):
    data = {k: row[k] for k in row.keys() if k != "pin"}
    if include_pin:
        data["pin"] = row["pin"]
    return data

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/health")
def health():
    return jsonify(status="ok", application="BuildPay", database="SQLite")

@app.get("/api/workers")
def list_workers():
    with connect_db() as con:
        rows = con.execute("SELECT * FROM workers ORDER BY created_at, id").fetchall()
        today = date.today().isoformat()
        for row in rows:
            att = con.execute(
                "SELECT status FROM attendance WHERE worker_id=? AND work_date=?",
                (row["id"], today)
            ).fetchone()
            if att:
                d = worker_dict(row)
                d["status"] = att["status"]
                # Return current attendance status without modifying the worker master record.
                row_data = d
                yield_data = None
            else:
                row_data = worker_dict(row)
            # build list below
            if "items" not in locals():
                items = []
            items.append(row_data)
    return jsonify(workers=items)

@app.post("/api/login")
def login():
    payload = request.get_json(silent=True) or {}
    role = str(payload.get("role", "worker")).lower()
    user_id = str(payload.get("id", "")).strip()
    pin = str(payload.get("pin", ""))
    if role == "admin":
        # Demo credentials only. Replace with hashed passwords and proper sessions before deployment.
        if user_id == "admin" and pin == "admin123":
            return jsonify(role="admin", message="Demo admin login successful")
        return jsonify(error="Admin credentials did not match."), 401
    with connect_db() as con:
        row = con.execute("SELECT * FROM workers WHERE lower(id)=lower(?)", (user_id,)).fetchone()
        if not row or row["pin"] != pin:
            return jsonify(error="Worker ID or PIN is incorrect."), 401
        return jsonify(role="worker", worker=worker_dict(row))

@app.post("/api/workers")
def create_worker():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    role = str(payload.get("role", "Helper")).strip()
    site = str(payload.get("site", SITES[0])).strip()
    try:
        wage = float(payload.get("wage", 0))
    except (TypeError, ValueError):
        return jsonify(error="Daily wage must be a number."), 400
    if not name or wage <= 0:
        return jsonify(error="Worker name and a positive daily wage are required."), 400
    with connect_db() as con:
        next_num = con.execute(
            "SELECT COALESCE(MAX(CAST(substr(id,3) AS INTEGER)),1000)+1 FROM workers WHERE id LIKE 'BP%'"
        ).fetchone()[0]
        wid = f"BP{next_num}"
        con.execute(
            """INSERT INTO workers
            (id,name,role,phone,site,wage,type,emergency,safety,status,pin)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (wid, name, role, str(payload.get("phone", "")).strip(), site, wage,
             str(payload.get("type", "Skilled")), str(payload.get("emergency", "")).strip(),
             str(payload.get("safety", "Pending")), "Present", "1234")
        )
        row = con.execute("SELECT * FROM workers WHERE id=?", (wid,)).fetchone()
        return jsonify(worker=worker_dict(row)), 201

@app.get("/api/attendance")
def get_attendance():
    work_date = request.args.get("date", date.today().isoformat())
    with connect_db() as con:
        rows = con.execute(
            """SELECT a.worker_id, w.name, a.work_date, a.status
               FROM attendance a JOIN workers w ON w.id=a.worker_id
               WHERE a.work_date=? ORDER BY w.name""", (work_date,)
        ).fetchall()
    return jsonify(date=work_date, records=[dict(r) for r in rows])

@app.post("/api/attendance")
def save_attendance():
    payload = request.get_json(silent=True) or {}
    work_date = str(payload.get("date", date.today().isoformat()))
    records = payload.get("records", [])
    if not isinstance(records, list):
        return jsonify(error="Attendance records must be a list."), 400
    with connect_db() as con:
        for record in records:
            wid = str(record.get("worker_id", ""))
            status = str(record.get("status", "Present"))
            if status not in ("Present", "Late", "Absent"):
                return jsonify(error=f"Invalid attendance status for {wid}."), 400
            exists = con.execute("SELECT 1 FROM workers WHERE id=?", (wid,)).fetchone()
            if not exists:
                continue
            con.execute(
                """INSERT INTO attendance(worker_id,work_date,status)
                   VALUES(?,?,?)
                   ON CONFLICT(worker_id,work_date) DO UPDATE SET
                   status=excluded.status, updated_at=CURRENT_TIMESTAMP""",
                (wid, work_date, status)
            )
        con.commit()
    return jsonify(message="Attendance saved", date=work_date, saved=len(records))

@app.get("/api/payroll")
def payroll_preview():
    try:
        days = max(0, min(31, int(request.args.get("days", 26))))
        overtime_hours = max(0, float(request.args.get("overtime", 6)))
        deductions = max(0, float(request.args.get("deductions", 300)))
    except ValueError:
        return jsonify(error="Invalid payroll parameters."), 400
    with connect_db() as con:
        rows = con.execute("SELECT * FROM workers ORDER BY name").fetchall()
    items = []
    for row in rows:
        base = row["wage"] * days
        hourly = row["wage"] / 8
        overtime = hourly * 1.5 * overtime_hours
        items.append({
            "worker_id": row["id"], "name": row["name"], "daily_wage": row["wage"],
            "paid_days": days, "base_wages": round(base, 2),
            "overtime_hours": overtime_hours, "overtime_pay": round(overtime, 2),
            "deductions": deductions, "estimated_net": round(max(0, base + overtime - deductions), 2)
        })
    return jsonify(payroll=items, note="Illustrative estimates only; not a payment or statutory payslip.")

@app.get("/api/reports/summary")
def report_summary():
    with connect_db() as con:
        total = con.execute("SELECT COUNT(*) FROM workers").fetchone()[0]
        pending = con.execute("SELECT COUNT(*) FROM workers WHERE safety='Pending'").fetchone()[0]
        today = date.today().isoformat()
        counts = {r["status"]: r["n"] for r in con.execute(
            "SELECT status,COUNT(*) n FROM attendance WHERE work_date=? GROUP BY status", (today,)
        ).fetchall()}
    return jsonify(total_workers=total, safety_pending=pending,
                   attendance_today=counts, date=today)

if __name__ == "__main__":
    init_db()
    print("BuildPay backend running at http://127.0.0.1:5000")
    print("Demo admin: admin / admin123 | Worker demo PIN: 1234")
    
