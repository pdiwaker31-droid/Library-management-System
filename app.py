"""
Library Management System
Flask Backend + MySQL
Run: python app.py

This file is intentionally written with comments so a student can
understand what each API is doing.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pymysql
import pymysql.cursors

app = Flask(__name__)
CORS(app)

# ------------------------------------------------------------
# DATABASE CONFIGURATION
# Change these values according to your local MySQL setup.
# ------------------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Arpit1996#@",       # Put your MySQL password here.
    "database": "library_db",
    "cursorclass": pymysql.cursors.DictCursor,
    "charset": "utf8mb4",
}


def get_db():
    """Create a fresh MySQL connection for an API request."""
    return pymysql.connect(**DB_CONFIG)


@app.route("/")
def index():
    # Serve the frontend when the user opens http://127.0.0.1:5000
    return send_from_directory(".", "library_management.html")


# ============================================================
# DASHBOARD
# ============================================================
@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    db = get_db()
    try:
        with db.cursor() as cur:
            # Count total books (book titles).
            cur.execute("SELECT COUNT(*) AS total FROM books")
            total_books = cur.fetchone()["total"]

            # Count physical copies.
            cur.execute("SELECT COUNT(*) AS total FROM book_copies")
            total_copies = cur.fetchone()["total"]

            # Count registered members.
            cur.execute("SELECT COUNT(*) AS total FROM members WHERE status='Active'")
            active_members = cur.fetchone()["total"]

            # Count currently issued books.
            cur.execute("SELECT COUNT(*) AS total FROM borrow_transactions WHERE status IN ('Issued','Overdue')")
            issued_books = cur.fetchone()["total"]

            # Count overdue books directly from due date.
            cur.execute("SELECT COUNT(*) AS total FROM borrow_transactions WHERE status='Issued' AND due_date < CURDATE()")
            overdue_books = cur.fetchone()["total"]

            # Total unpaid fine amount.
            cur.execute("SELECT COALESCE(SUM(amount-paid_amount),0) AS total FROM fines WHERE status IN ('Unpaid','Partial')")
            pending_fines = cur.fetchone()["total"]

        return jsonify({
            "total_books": total_books,
            "total_copies": total_copies,
            "active_members": active_members,
            "issued_books": issued_books,
            "overdue_books": overdue_books,
            "pending_fines": float(pending_fines),
        })
    finally:
        db.close()


# ============================================================
# BOOKS
# ============================================================
@app.route("/api/books", methods=["GET"])
def get_books():
    search = request.args.get("search", "")
    db = get_db()
    try:
        with db.cursor() as cur:
            sql = """
                SELECT v.*
                FROM vw_book_inventory v
                WHERE v.title LIKE %s OR v.isbn LIKE %s OR v.author_name LIKE %s
                ORDER BY v.title
            """
            like = f"%{search}%"
            cur.execute(sql, (like, like, like))
            return jsonify(cur.fetchall())
    finally:
        db.close()


@app.route("/api/books", methods=["POST"])
def add_book():
    data = request.json
    db = get_db()
    try:
        with db.cursor() as cur:
            # Insert the book first.
            cur.execute("""
                INSERT INTO books
                (isbn,title,author_id,category_id,publisher_id,edition,publish_year,price,language,description)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                data.get("isbn"), data["title"], data["author_id"], data.get("category_id"),
                data.get("publisher_id"), data.get("edition"), data.get("publish_year"),
                data.get("price", 0), data.get("language", "English"), data.get("description")
            ))
            db.commit()
            return jsonify({"success": True, "book_id": cur.lastrowid}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


# ============================================================
# AUTHORS / CATEGORIES / PUBLISHERS
# ============================================================
@app.route("/api/authors", methods=["GET"])
def get_authors():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM authors ORDER BY author_name")
            return jsonify(cur.fetchall())
    finally:
        db.close()


@app.route("/api/categories", methods=["GET"])
def get_categories():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM categories ORDER BY category_name")
            return jsonify(cur.fetchall())
    finally:
        db.close()


@app.route("/api/publishers", methods=["GET"])
def get_publishers():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM publishers ORDER BY publisher_name")
            return jsonify(cur.fetchall())
    finally:
        db.close()


# ============================================================
# MEMBERS
# ============================================================
@app.route("/api/members", methods=["GET"])
def get_members():
    search = request.args.get("search", "")
    db = get_db()
    try:
        with db.cursor() as cur:
            like = f"%{search}%"
            cur.execute("""
                SELECT * FROM members
                WHERE member_code LIKE %s OR first_name LIKE %s
                   OR last_name LIKE %s OR phone LIKE %s
                ORDER BY created_at DESC
            """, (like, like, like, like))
            return jsonify(cur.fetchall())
    finally:
        db.close()


@app.route("/api/members", methods=["POST"])
def add_member():
    data = request.json
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                INSERT INTO members
                (member_code,first_name,last_name,member_type,phone,email,address)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                data["member_code"], data["first_name"], data.get("last_name"),
                data.get("member_type", "Student"), data["phone"],
                data.get("email"), data.get("address")
            ))
            db.commit()
            return jsonify({"success": True, "member_id": cur.lastrowid}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


# ============================================================
# ISSUE / RETURN
# ============================================================
@app.route("/api/issue", methods=["POST"])
def issue_book():
    data = request.json
    db = get_db()
    try:
        with db.cursor() as cur:
            # First check that the selected copy is available.
            cur.execute("SELECT status FROM book_copies WHERE copy_id=%s", (data["copy_id"],))
            copy = cur.fetchone()
            if not copy:
                return jsonify({"error": "Book copy not found"}), 404
            if copy["status"] != "Available":
                return jsonify({"error": "This copy is not available"}), 400

            # Create issue transaction.
            cur.execute("""
                INSERT INTO borrow_transactions
                (copy_id,member_id,issued_by,issue_date,due_date,remarks)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                data["copy_id"], data["member_id"], data.get("issued_by"),
                data.get("issue_date"), data["due_date"], data.get("remarks")
            ))

            # Change physical copy status to Issued.
            cur.execute("UPDATE book_copies SET status='Issued' WHERE copy_id=%s", (data["copy_id"],))
            db.commit()
            return jsonify({"success": True, "transaction_id": cur.lastrowid}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT bt.transaction_id,
                       m.member_code,
                       CONCAT(m.first_name,' ',COALESCE(m.last_name,'')) AS member_name,
                       b.title, bc.accession_no,
                       bt.issue_date, bt.due_date, bt.return_date, bt.status,
                       COALESCE(f.amount,0) AS fine_amount,
                       COALESCE(f.status,'-') AS fine_status
                FROM borrow_transactions bt
                JOIN members m ON m.member_id=bt.member_id
                JOIN book_copies bc ON bc.copy_id=bt.copy_id
                JOIN books b ON b.book_id=bc.book_id
                LEFT JOIN fines f ON f.transaction_id=bt.transaction_id
                ORDER BY bt.transaction_id DESC
            """)
            return jsonify(cur.fetchall())
    finally:
        db.close()


@app.route("/api/return/<int:transaction_id>", methods=["PUT"])
def return_book(transaction_id):
    db = get_db()
    try:
        with db.cursor() as cur:
            # Find the copy connected to the transaction.
            cur.execute("SELECT copy_id, due_date, status FROM borrow_transactions WHERE transaction_id=%s", (transaction_id,))
            tx = cur.fetchone()
            if not tx:
                return jsonify({"error": "Transaction not found"}), 404
            if tx["status"] == "Returned":
                return jsonify({"error": "Book already returned"}), 400

            # Mark transaction returned.
            cur.execute("""
                UPDATE borrow_transactions
                SET return_date=CURDATE(), status='Returned'
                WHERE transaction_id=%s
            """, (transaction_id,))

            # Make the physical copy available again.
            cur.execute("UPDATE book_copies SET status='Available' WHERE copy_id=%s", (tx["copy_id"],))

            # Automatically create a simple late fine: Rs. 20 per overdue day.
            cur.execute("""
                SELECT DATEDIFF(CURDATE(), %s) AS days_late
            """, (tx["due_date"],))
            days_late = max(0, cur.fetchone()["days_late"])
            if days_late > 0:
                amount = days_late * 20
                cur.execute("""
                    INSERT INTO fines (transaction_id,amount,reason,status)
                    VALUES (%s,%s,%s,'Unpaid')
                    ON DUPLICATE KEY UPDATE amount=%s, reason=%s
                """, (
                    transaction_id, amount, f"Late return - {days_late} day(s)",
                    amount, f"Late return - {days_late} day(s)"
                ))

            db.commit()
            return jsonify({"success": True, "days_late": days_late}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


# ============================================================
# BOOK COPIES - used by issue form
# ============================================================
@app.route("/api/copies", methods=["GET"])
def get_copies():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT bc.copy_id, bc.accession_no, bc.shelf_no, bc.status,
                       b.book_id, b.title
                FROM book_copies bc
                JOIN books b ON b.book_id=bc.book_id
                ORDER BY b.title, bc.accession_no
            """)
            return jsonify(cur.fetchall())
    finally:
        db.close()


# ============================================================
# FINES
# ============================================================
@app.route("/api/fines", methods=["GET"])
def get_fines():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT f.*, bt.member_id,
                       CONCAT(m.first_name,' ',COALESCE(m.last_name,'')) AS member_name,
                       b.title
                FROM fines f
                JOIN borrow_transactions bt ON bt.transaction_id=f.transaction_id
                JOIN members m ON m.member_id=bt.member_id
                JOIN book_copies bc ON bc.copy_id=bt.copy_id
                JOIN books b ON b.book_id=bc.book_id
                ORDER BY f.fine_id DESC
            """)
            return jsonify(cur.fetchall())
    finally:
        db.close()


@app.route("/api/fines/<int:fine_id>/pay", methods=["PUT"])
def pay_fine(fine_id):
    data = request.json
    amount = float(data.get("amount", 0))
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT amount,paid_amount FROM fines WHERE fine_id=%s", (fine_id,))
            fine = cur.fetchone()
            if not fine:
                return jsonify({"error": "Fine not found"}), 404

            new_paid = float(fine["paid_amount"]) + amount
            if new_paid > float(fine["amount"]):
                return jsonify({"error": "Payment cannot exceed fine amount"}), 400

            status = "Paid" if new_paid == float(fine["amount"]) else "Partial"
            cur.execute("""
                UPDATE fines SET paid_amount=%s, status=%s,
                    paid_date=CASE WHEN %s='Paid' THEN CURDATE() ELSE paid_date END
                WHERE fine_id=%s
            """, (new_paid, status, status, fine_id))
            db.commit()
            return jsonify({"success": True}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


# ============================================================
# START SERVER
# ============================================================
if __name__ == "__main__":
    # debug=True helps beginners see errors while developing.
    app.run(debug=True, host="127.0.0.1", port=5000)
