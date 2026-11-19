-- ============================================================
-- LIBRARY MANAGEMENT SYSTEM - MySQL DATABASE
-- Beginner-friendly schema with comments
-- Modules: Members, Authors, Categories, Books, Book Copies,
--          Issue/Return, Fines, Staff & Dashboard Views
-- ============================================================

CREATE DATABASE IF NOT EXISTS library_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE library_db;

-- ------------------------------------------------------------
-- 1. CATEGORIES
-- One category can contain many books.
-- ------------------------------------------------------------
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 2. AUTHORS
-- One author can write many books.
-- ------------------------------------------------------------
CREATE TABLE authors (
    author_id INT AUTO_INCREMENT PRIMARY KEY,
    author_name VARCHAR(150) NOT NULL,
    email VARCHAR(120),
    country VARCHAR(80),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 3. PUBLISHERS
-- One publisher can publish many books.
-- ------------------------------------------------------------
CREATE TABLE publishers (
    publisher_id INT AUTO_INCREMENT PRIMARY KEY,
    publisher_name VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(20),
    email VARCHAR(120),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 4. BOOKS
-- Stores book-level information.
-- category_id and publisher_id are FOREIGN KEYS.
-- ------------------------------------------------------------
CREATE TABLE books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    isbn VARCHAR(20) UNIQUE,
    title VARCHAR(200) NOT NULL,
    author_id INT NOT NULL,
    category_id INT,
    publisher_id INT,
    edition VARCHAR(50),
    publish_year YEAR,
    price DECIMAL(10,2) DEFAULT 0.00,
    language VARCHAR(50) DEFAULT 'English',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL,
    FOREIGN KEY (publisher_id) REFERENCES publishers(publisher_id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- 5. BOOK COPIES
-- A book can have multiple physical copies.
-- Example: Python book has Copy 1, Copy 2, Copy 3.
-- ------------------------------------------------------------
CREATE TABLE book_copies (
    copy_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    accession_no VARCHAR(50) NOT NULL UNIQUE,
    shelf_no VARCHAR(30),
    status ENUM('Available','Issued','Lost','Damaged') DEFAULT 'Available',
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 6. MEMBERS
-- Students/teachers/other people who can borrow books.
-- ------------------------------------------------------------
CREATE TABLE members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    member_code VARCHAR(30) NOT NULL UNIQUE,
    first_name VARCHAR(60) NOT NULL,
    last_name VARCHAR(60),
    member_type ENUM('Student','Teacher','Staff','Other') DEFAULT 'Student',
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(120),
    address TEXT,
    join_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    status ENUM('Active','Inactive','Blocked') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 7. STAFF / LIBRARIANS
-- Used for login/operations and tracking who issued books.
-- ------------------------------------------------------------
CREATE TABLE staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(20),
    role ENUM('Admin','Librarian','Assistant') DEFAULT 'Librarian',
    username VARCHAR(60) UNIQUE,
    password_hash VARCHAR(255),
    status ENUM('Active','Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 8. BORROW / ISSUE TRANSACTIONS
-- Main transaction table: member borrows a physical copy.
-- ------------------------------------------------------------
CREATE TABLE borrow_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    copy_id INT NOT NULL,
    member_id INT NOT NULL,
    issued_by INT,
    issue_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    due_date DATE NOT NULL,
    return_date DATE,
    status ENUM('Issued','Returned','Overdue','Lost') DEFAULT 'Issued',
    remarks VARCHAR(255),
    FOREIGN KEY (copy_id) REFERENCES book_copies(copy_id) ON DELETE RESTRICT,
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE,
    FOREIGN KEY (issued_by) REFERENCES staff(staff_id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- 9. FINES
-- A transaction may have zero or one fine record.
-- ------------------------------------------------------------
CREATE TABLE fines (
    fine_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT NOT NULL UNIQUE,
    amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    reason VARCHAR(255),
    paid_amount DECIMAL(10,2) DEFAULT 0.00,
    status ENUM('Unpaid','Partial','Paid','Waived') DEFAULT 'Unpaid',
    paid_date DATE,
    FOREIGN KEY (transaction_id) REFERENCES borrow_transactions(transaction_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- USEFUL VIEWS
-- ------------------------------------------------------------

-- Current book availability with author/category information.
CREATE OR REPLACE VIEW vw_book_inventory AS
SELECT
    b.book_id,
    b.title,
    b.isbn,
    a.author_name,
    c.category_name,
    COUNT(bc.copy_id) AS total_copies,
    SUM(bc.status = 'Available') AS available_copies,
    SUM(bc.status = 'Issued') AS issued_copies
FROM books b
JOIN authors a ON a.author_id = b.author_id
LEFT JOIN categories c ON c.category_id = b.category_id
LEFT JOIN book_copies bc ON bc.book_id = b.book_id
GROUP BY b.book_id, b.title, b.isbn, a.author_name, c.category_name;

-- All currently issued books.
CREATE OR REPLACE VIEW vw_issued_books AS
SELECT
    bt.transaction_id,
    m.member_code,
    CONCAT(m.first_name, ' ', COALESCE(m.last_name,'')) AS member_name,
    b.title,
    bc.accession_no,
    bt.issue_date,
    bt.due_date,
    bt.status
FROM borrow_transactions bt
JOIN members m ON m.member_id = bt.member_id
JOIN book_copies bc ON bc.copy_id = bt.copy_id
JOIN books b ON b.book_id = bc.book_id
WHERE bt.status IN ('Issued','Overdue');

-- Overdue transactions.
CREATE OR REPLACE VIEW vw_overdue_books AS
SELECT
    bt.transaction_id,
    m.member_code,
    CONCAT(m.first_name, ' ', COALESCE(m.last_name,'')) AS member_name,
    m.phone,
    b.title,
    bc.accession_no,
    bt.due_date,
    DATEDIFF(CURDATE(), bt.due_date) AS overdue_days
FROM borrow_transactions bt
JOIN members m ON m.member_id = bt.member_id
JOIN book_copies bc ON bc.copy_id = bt.copy_id
JOIN books b ON b.book_id = bc.book_id
WHERE bt.status = 'Issued' AND bt.due_date < CURDATE();

-- ------------------------------------------------------------
-- SAMPLE DATA
-- ------------------------------------------------------------
INSERT INTO categories (category_name, description) VALUES
('Programming','Programming and software development books'),
('Database','SQL, DBMS and database design books'),
('Data Science','Statistics, Python, ML and Data Science'),
('Computer Fundamentals','Basic computer and IT books'),
('Business','Business and management books');

INSERT INTO authors (author_name, email, country) VALUES
('Ramesh Kumar','ramesh@example.com','India'),
('Amit Sharma','amit@example.com','India'),
('James Smith','james@example.com','USA'),
('Anita Verma','anita@example.com','India');

INSERT INTO publishers (publisher_name, phone, email, address) VALUES
('Tech Books India','9876500001','info@techbooks.in','New Delhi'),
('Knowledge Press','9876500002','contact@knowledgepress.in','Lucknow'),
('Global Learning','9876500003','info@globallearning.com','Mumbai');

INSERT INTO books (isbn,title,author_id,category_id,publisher_id,edition,publish_year,price,language) VALUES
('978100000001','Python Programming Basics',1,1,1,'3rd',2025,650,'English'),
('978100000002','SQL & Database Management',2,2,1,'2nd',2024,550,'English'),
('978100000003','Data Science with Python',3,3,3,'1st',2025,850,'English'),
('978100000004','Computer Fundamentals',4,4,2,'5th',2023,400,'English'),
('978100000005','Business Management',2,5,2,'2nd',2024,500,'English');

INSERT INTO book_copies (book_id,accession_no,shelf_no,status) VALUES
(1,'ACC-0001','S-A1','Available'),
(1,'ACC-0002','S-A1','Issued'),
(2,'ACC-0003','S-B1','Available'),
(2,'ACC-0004','S-B1','Available'),
(3,'ACC-0005','S-C1','Available'),
(4,'ACC-0006','S-D1','Issued'),
(5,'ACC-0007','S-E1','Available');

INSERT INTO members (member_code,first_name,last_name,member_type,phone,email,address) VALUES
('MEM001','Rahul','Verma','Student','9811111111','rahul@example.com','Lucknow'),
('MEM002','Priya','Singh','Student','9822222222','priya@example.com','Lucknow'),
('MEM003','Aman','Gupta','Teacher','9833333333','aman@example.com','Lucknow'),
('MEM004','Neha','Sharma','Staff','9844444444','neha@example.com','Lucknow');

INSERT INTO staff (name,email,phone,role,username,password_hash) VALUES
('Library Admin','admin@library.local','9876543210','Admin','admin','change-me'),
('Main Librarian','librarian@library.local','9876543211','Librarian','librarian','change-me');

-- Sample issue transactions.
INSERT INTO borrow_transactions (copy_id,member_id,issued_by,issue_date,due_date,status) VALUES
(2,1,2,DATE_SUB(CURDATE(), INTERVAL 3 DAY),DATE_SUB(CURDATE(), INTERVAL 1 DAY),'Issued'),
(6,2,2,CURDATE(),DATE_ADD(CURDATE(), INTERVAL 14 DAY),'Issued');

-- Fine for the overdue sample transaction.
INSERT INTO fines (transaction_id,amount,reason,status) VALUES
(1,20,'Late return - 1 day','Unpaid');
