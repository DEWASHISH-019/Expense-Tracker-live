from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
import psycopg2.extras
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from ai.analysis import analyze_spending

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-production-secret-key")
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            expense_date TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "danger")
            return render_template("register.html")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, email, password, created_at) VALUES (%s, %s, %s, %s)",
                (name, email, generate_password_hash(password), datetime.now().isoformat())
            )
            conn.commit()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("login"))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash("Email is already registered.", "danger")
            return render_template("register.html")
        finally:
            cursor.close()
            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT * FROM expenses WHERE user_id = %s ORDER BY expense_date DESC, id DESC",
        (session["user_id"],)
    )
    expenses = cursor.fetchall()
    cursor.close()
    conn.close()

    total = sum(row["amount"] for row in expenses)
    count = len(expenses)

    current_month = datetime.now().strftime("%Y-%m")
    monthly_total = sum(
        row["amount"] for row in expenses
        if row["expense_date"].startswith(current_month)
    )

    category_totals = {}
    for row in expenses:
        category_totals[row["category"]] = category_totals.get(row["category"], 0) + row["amount"]

    highest_category = max(category_totals, key=category_totals.get) if category_totals else "No data"

    return render_template(
        "dashboard.html",
        expenses=expenses[:5],
        total=total,
        count=count,
        monthly_total=monthly_total,
        highest_category=highest_category
    )

@app.route("/expenses")
@login_required
def expenses():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    query = "SELECT * FROM expenses WHERE user_id = %s"
    params = [session["user_id"]]

    if search:
        query += """ AND (
            LOWER(title) LIKE LOWER(%s) 
            OR LOWER(COALESCE(notes, '')) LIKE LOWER(%s) 
            OR LOWER(category) LIKE LOWER(%s) 
            OR CAST(amount AS TEXT) LIKE %s 
            OR expense_date LIKE %s
        )"""
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])

    if category:
        query += " AND category = %s"
        params.append(category)

    query += " ORDER BY expense_date DESC, id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("expenses.html", expenses=rows, search=search, category=category)

@app.route("/add-expense", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        title = request.form["title"].strip()
        amount = request.form["amount"]
        category = request.form["category"]
        expense_date = request.form["expense_date"]
        notes = request.form.get("notes", "").strip()

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Please enter a valid positive amount.", "danger")
            return render_template("add_expense.html")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expenses
            (user_id, title, amount, category, expense_date, notes, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            session["user_id"], title, amount, category,
            expense_date, notes, datetime.now().isoformat()
        ))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Expense added successfully.", "success")
        return redirect(url_for("expenses"))

    return render_template("add_expense.html")

@app.route("/edit-expense/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT * FROM expenses WHERE id = %s AND user_id = %s",
        (expense_id, session["user_id"])
    )
    expense = cursor.fetchone()

    if not expense:
        cursor.close()
        conn.close()
        flash("Expense not found.", "danger")
        return redirect(url_for("expenses"))

    if request.method == "POST":
        title = request.form["title"].strip()
        amount = request.form["amount"]
        category = request.form["category"]
        expense_date = request.form["expense_date"]
        notes = request.form.get("notes", "").strip()

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            cursor.close()
            conn.close()
            flash("Please enter a valid positive amount.", "danger")
            return render_template("edit_expense.html", expense=expense)

        cursor.execute("""
            UPDATE expenses
            SET title = %s, amount = %s, category = %s, expense_date = %s, notes = %s
            WHERE id = %s AND user_id = %s
        """, (
            title, amount, category, expense_date, notes,
            expense_id, session["user_id"]
        ))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Expense updated successfully.", "success")
        return redirect(url_for("expenses"))

    cursor.close()
    conn.close()
    return render_template("edit_expense.html", expense=expense)

@app.route("/delete-expense/<int:expense_id>", methods=["GET", "POST"])
@login_required
def delete_expense(expense_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM expenses WHERE id = %s AND user_id = %s",
        (expense_id, session["user_id"])
    )
    conn.commit()
    cursor.close()
    conn.close()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({"success": True, "message": "Expense deleted."})

    flash("Expense deleted.", "success")
    return redirect(url_for("expenses"))

@app.route("/reports")
@login_required
def reports():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT * FROM expenses WHERE user_id = %s ORDER BY expense_date",
        (session["user_id"],)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("reports.html", expenses=rows)

@app.route("/api/chart-data")
@login_required
def chart_data():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute(
        "SELECT category, SUM(amount) AS total FROM expenses WHERE user_id = %s GROUP BY category ORDER BY total DESC",
        (session["user_id"],)
    )
    rows = cursor.fetchall()

    cursor.execute("""
        SELECT SUBSTRING(expense_date, 1, 7) AS month, SUM(amount) AS total
        FROM expenses
        WHERE user_id = %s
        GROUP BY month
        ORDER BY month
    """, (session["user_id"],))
    monthly = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return jsonify({
        "categories": [r["category"] for r in rows],
        "category_totals": [round(r["total"], 2) for r in rows],
        "months": [r["month"] for r in monthly],
        "monthly_totals": [round(r["total"], 2) for r in monthly]
    })

@app.route("/ai-analysis")
@login_required
def ai_analysis():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT * FROM expenses WHERE user_id = %s ORDER BY expense_date",
        (session["user_id"],)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    result = analyze_spending(rows)
    return render_template("ai_analysis.html", result=result)

@app.context_processor
def inject_now():
    return {"now": datetime.now().strftime("%Y-%m-%d")}

if __name__ == '__main__':
    # Only runs during local testing, not on Render
    try:
        init_db()
    except Exception as e:
        print("Set your DATABASE_URL environment variable to run locally.")
    app.run(debug=False, use_reloader=False, threaded=True)
