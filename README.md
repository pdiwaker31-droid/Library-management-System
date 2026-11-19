# Library Management System (MySQL)

A relational MySQL database schema designed for managing library operations, book copies, member borrowing records, fines, and reporting views.

## Features & Modules
- **Catalog Management:** `categories`, `authors`, `publishers`, `books`, and physical `book_copies` tracking.
- **Membership & Staff:** `members` (Student, Teacher, Staff, Other) and `staff` (Admin, Librarian, Assistant).
- **Circulation & Fines:** `borrow_transactions` (issue, due, return, overdue tracking) and `fines` management.
- **Reporting Views:** `vw_book_inventory`, `vw_issued_books`, and `vw_overdue_books`.
- **Sample Data:** Pre-loaded seed records for quick testing.

## How to Run
1. Open MySQL Workbench, MySQL CLI, or your preferred SQL client.
2. Run the `library_schema.sql` script:
   ```sql
   SOURCE library_schema.sql;
