# Library Management Portal

A console-based Library Management Portal built in Python for **Assignment 3: End-to-End Portal Design**.

Librarians can add, search and delete books and generate reports. Members can search, issue and return books. All data is saved in JSON and CSV files, so nothing is lost when the program closes.

## Features
- Login with two roles: **admin** (librarian) and **member** (student)
- Add, search (by title, author or ID), view and delete books
- Issue and return books, with available copies tracked automatically
- Transaction history appended to a CSV file
- Library report: totals, issued copies, out-of-stock books and the most popular book
- Full input validation, so wrong input never crashes the portal

## Python concepts used
| Concept | Where |
|---|---|
| Functions (`def`) | `user_login()`, `add_record()`, `search_record()`, `issue_book()`, `return_book()`, `generate_report()` and more |
| Loops | `while True` main and sub-menus; `for` loops to search, display and build the report |
| File handling | `books.json` and `users.json` (read on startup, written after changes), `transactions.csv` (append mode) |
| Exception handling | `FileNotFoundError`, `PermissionError`, `JSONDecodeError`, `ValueError`, `KeyboardInterrupt`, with `try / except / finally` |

## Project structure
```
library_portal.py                 # main program
Library_Management_Portal.ipynb   # notebook with explanations and test runs
data/
  books.json                      # book records
  users.json                      # login accounts
  transactions.csv                # issue/return log (created automatically)
```

## How to run
Requires Python 3.8 or later. No extra packages are needed.

```bash
python library_portal.py
```

Or open `Library_Management_Portal.ipynb` in Jupyter and choose **Run All**.

### Sample logins
| Username | Password | Role |
|---|---|---|
| admin | admin123 | Admin |
| ali | ali123 | Member |
| sara | sara123 | Member |

## Team
| Name | Roll No | Main contribution |
|---|---|---|
| Rija Maqsood | 25L-5302 | File handling, login system, report generation, Word/PDF report  |
| Sofia Noreen | 25L-5301 |  Book records, issue/return logic, Jupyter Notebook, GitHub repository and screenshots  |
