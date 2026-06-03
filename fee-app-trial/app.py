from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("students.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            month INTEGER,
            year INTEGER
        )
    """)

    conn.commit()
    conn.close()

init_db()


# ---------------- HOME DASHBOARD ----------------
@app.route("/")
def home():
    conn = sqlite3.connect("students.db")
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]

    now = datetime.now()
    month = now.month
    year = now.year

    # paid count
    cur.execute("""
        SELECT COUNT(DISTINCT student_id)
        FROM payments
        WHERE month=? AND year=?
    """, (month, year))
    paid_students = cur.fetchone()[0]

    pending_students = total_students - paid_students

    # ---------------- PAID LIST ----------------
    cur.execute("""
        SELECT DISTINCT students.id, students.name
        FROM students
        JOIN payments ON students.id = payments.student_id
        WHERE payments.month=? AND payments.year=?
    """, (month, year))
    paid_list = cur.fetchall()

    # ---------------- UNPAID LIST ----------------
    cur.execute("""
        SELECT id, name FROM students
        WHERE id NOT IN (
            SELECT student_id FROM payments
            WHERE month=? AND year=?
        )
    """, (month, year))
    unpaid_list = cur.fetchall()

    conn.close()

    return render_template(
        "home.html",
        total=total_students,
        paid=paid_students,
        pending=pending_students,
        paid_list=paid_list,
        unpaid_list=unpaid_list
    )


# ---------------- ADD STUDENT ----------------
@app.route("/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]

        conn = sqlite3.connect("students.db")
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO students (name, phone) VALUES (?, ?)",
            (name, phone)
        )

        conn.commit()
        conn.close()

        return redirect("/students")

    return render_template("add_student.html")


# ---------------- VIEW STUDENTS ----------------
@app.route("/students")
def students():
    conn = sqlite3.connect("students.db")
    cur = conn.cursor()

    cur.execute("SELECT id, name, phone FROM students")
    students = cur.fetchall()

    now = datetime.now()
    month = now.month
    year = now.year

    cur.execute("""
        SELECT student_id FROM payments
        WHERE month=? AND year=?
    """, (month, year))

    paid_ids = [row[0] for row in cur.fetchall()]

    conn.close()

    return render_template(
        "students.html",
        students=students,
        paid_ids=paid_ids
    )


# ---------------- MARK PAID ----------------
@app.route("/pay/<int:student_id>")
def mark_paid(student_id):
    now = datetime.now()
    month = now.month
    year = now.year

    conn = sqlite3.connect("students.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM payments
        WHERE student_id=? AND month=? AND year=?
    """, (student_id, month, year))

    existing = cur.fetchone()

    if not existing:
        cur.execute("""
            INSERT INTO payments (student_id, month, year)
            VALUES (?, ?, ?)
        """, (student_id, month, year))

    conn.commit()
    conn.close()

    return redirect("/students")

@app.route("/delete/<int:student_id>")
def delete_student(student_id):

    conn = sqlite3.connect("students.db")
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM students WHERE id=?",
        (student_id,)
    )

    cur.execute(
        "DELETE FROM payments WHERE student_id=?",
        (student_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/students")
# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
