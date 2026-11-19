# Library Management System

A beginner-friendly **Library Management System** built with:

- MySQL — database
- Flask — Python backend/API
- HTML/CSS/JavaScript — frontend

## Project Modules

1. Dashboard
2. Books
3. Members
4. Issue / Return
5. Fines
6. Master Data (Authors, Categories, Publishers)

## Files

- `library_schema.sql` — complete MySQL database, tables, relationships, views and sample data.
- `app.py` — Flask backend with commented APIs.
- `library_management.html` — frontend dashboard.
- `ER_DIAGRAM.md` — ER diagram and explanation.
- `requirements.txt` — Python packages.

## How to Run

### Step 1 — Create database
Open MySQL Workbench / phpMyAdmin and run:

```sql
SOURCE path/to/library_schema.sql;
```

Or open `library_schema.sql`, copy all SQL and execute it in MySQL.

### Step 2 — Install Python packages

```bash
pip install -r requirements.txt
```

### Step 3 — Configure MySQL password

Open `app.py` and change:

```python
"password": ""
```

to your MySQL root password.

### Step 4 — Start Flask

```bash
python app.py
```

### Step 5 — Open browser

`http://127.0.0.1:5000`

## Important learning flow

**Member registers → Librarian selects available book copy → Issue transaction is created → Copy status becomes Issued → Book is returned → Copy becomes Available → If returned late, fine is calculated.**

## Suggested project viva topics

- What is an ER diagram?
- What is a primary key?
- What is a foreign key?
- Why is `book_copies` a separate table?
- What is normalization?
- What is a JOIN?
- What is CRUD?
- What is a database view?
- Why do we use Flask?
- Why do we use MySQL?
- What is a transaction?
- What is ACID?
