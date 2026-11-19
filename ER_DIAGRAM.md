# Library Management System — ER Diagram

## Main Entities

- **AUTHORS** — stores author information.
- **CATEGORIES** — stores book categories.
- **PUBLISHERS** — stores publisher information.
- **BOOKS** — stores book-level information.
- **BOOK_COPIES** — stores physical copies of each book.
- **MEMBERS** — stores students/teachers/staff who borrow books.
- **STAFF** — stores librarians/admins.
- **BORROW_TRANSACTIONS** — records issue and return activity.
- **FINES** — records late-return fines.

## ER Diagram (Mermaid)

```mermaid
erDiagram
    AUTHORS ||--o{ BOOKS : writes
    CATEGORIES ||--o{ BOOKS : classifies
    PUBLISHERS ||--o{ BOOKS : publishes
    BOOKS ||--o{ BOOK_COPIES : has
    MEMBERS ||--o{ BORROW_TRANSACTIONS : borrows
    BOOK_COPIES ||--o{ BORROW_TRANSACTIONS : issued_in
    STAFF ||--o{ BORROW_TRANSACTIONS : issues
    BORROW_TRANSACTIONS ||--o| FINES : may_have

    AUTHORS {
      int author_id PK
      varchar author_name
      varchar email
      varchar country
    }
    CATEGORIES {
      int category_id PK
      varchar category_name
    }
    PUBLISHERS {
      int publisher_id PK
      varchar publisher_name
    }
    BOOKS {
      int book_id PK
      varchar isbn UK
      varchar title
      int author_id FK
      int category_id FK
      int publisher_id FK
      decimal price
    }
    BOOK_COPIES {
      int copy_id PK
      int book_id FK
      varchar accession_no UK
      varchar shelf_no
      enum status
    }
    MEMBERS {
      int member_id PK
      varchar member_code UK
      varchar first_name
      varchar last_name
      enum member_type
      varchar phone
      enum status
    }
    STAFF {
      int staff_id PK
      varchar name
      varchar email UK
      enum role
    }
    BORROW_TRANSACTIONS {
      int transaction_id PK
      int copy_id FK
      int member_id FK
      int issued_by FK
      date issue_date
      date due_date
      date return_date
      enum status
    }
    FINES {
      int fine_id PK
      int transaction_id FK UK
      decimal amount
      decimal paid_amount
      enum status
    }
```

## Relationship explanation

1. **Author → Books:** One author can write many books.
2. **Category → Books:** One category can contain many books.
3. **Publisher → Books:** One publisher can publish many books.
4. **Book → Book Copies:** One book title can have many physical copies.
5. **Member → Borrow Transactions:** One member can borrow many books over time.
6. **Book Copy → Borrow Transactions:** One physical copy can appear in many transactions over time, but it should have only one active issue at a time.
7. **Staff → Borrow Transactions:** One librarian/staff member can issue many books.
8. **Borrow Transaction → Fine:** A transaction may have zero or one fine.

## Primary Key and Foreign Key

- **PK:** uniquely identifies a row, e.g. `book_id`.
- **FK:** connects one table to another, e.g. `books.author_id → authors.author_id`.

## Normalization used

The design keeps authors, categories, publishers, books, physical copies and members in separate tables. This reduces repeated data and makes updates easier. The `book_copies` table is especially important because one book title can have multiple physical copies.
