# %% [1] Imports and file paths
"""
Library Management Portal
-------------------------
A console-based portal to manage books, members, issuing and returning.
Data is stored in:
    data/books.json         -> all books in the library
    data/users.json         -> login accounts (admin / member)
    data/transactions.csv   -> log of every issue / return (appended)
"""

import json
import csv
import os
from datetime import datetime

DATA_FOLDER = "data"
BOOKS_FILE = os.path.join(DATA_FOLDER, "books.json")
USERS_FILE = os.path.join(DATA_FOLDER, "users.json")
LOG_FILE = os.path.join(DATA_FOLDER, "transactions.csv")


# %% [2] File handling functions
def load_json(file_path, default_data):
    """
    Read a JSON file and return its data.
    If the file is missing or broken, return default_data instead of crashing.
    """
    file = None
    try:
        file = open(file_path, "r")
        data = json.load(file)
        print(f"[OK] Loaded {len(data)} records from {file_path}")
        return data
    except FileNotFoundError:
        print(f"[WARNING] {file_path} not found. Starting with empty data.")
        return default_data
    except PermissionError:
        print(f"[ERROR] No permission to read {file_path}.")
        return default_data
    except json.JSONDecodeError:
        print(f"[ERROR] {file_path} is corrupted. Starting with empty data.")
        return default_data
    finally:
        if file is not None:
            file.close()


def save_json(file_path, data):
    """Write data to a JSON file. Returns True if saved, False if it failed."""
    file = None
    try:
        os.makedirs(DATA_FOLDER, exist_ok=True)
        file = open(file_path, "w")
        json.dump(data, file, indent=4)
        return True
    except PermissionError:
        print(f"[ERROR] No permission to write {file_path}.")
        return False
    except OSError as error:
        print(f"[ERROR] Could not save {file_path}: {error}")
        return False
    finally:
        if file is not None:
            file.close()


def log_transaction(action, book_id, username):
    """Append one line (date, action, book, user) to the CSV log file."""
    try:
        os.makedirs(DATA_FOLDER, exist_ok=True)
        new_file = not os.path.exists(LOG_FILE)
        with open(LOG_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            if new_file:
                writer.writerow(["date_time", "action", "book_id", "username"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M"),
                             action, book_id, username])
        return True
    except (PermissionError, OSError) as error:
        print(f"[ERROR] Could not write log: {error}")
        return False


def read_transactions():
    """Read the CSV log and return a list of rows (dictionaries)."""
    try:
        with open(LOG_FILE, "r") as file:
            return list(csv.DictReader(file))
    except FileNotFoundError:
        return []


# %% [3] Login function
def user_login(users, username, password):
    """
    Check username and password against the users list.
    Returns the matching user dictionary, or None if login fails.
    """
    for user in users:
        if user["username"] == username.strip() and user["password"] == password:
            return user
    return None


# %% [4] Add, search and delete book records
def add_record(books, book_id, title, author, year, copies):
    """
    Add a new book to the books list.
    year and copies may arrive as text, so they are converted to int here.
    Returns (True, message) on success or (False, message) on failure.
    """
    try:
        year = int(year)
        copies = int(copies)
    except ValueError:
        return False, "Year and copies must be whole numbers."

    book_id = book_id.strip().upper()
    if book_id == "" or title.strip() == "" or author.strip() == "":
        return False, "Book ID, title and author cannot be empty."
    if copies <= 0:
        return False, "Copies must be at least 1."
    if year < 1000 or year > datetime.now().year:
        return False, "Please enter a valid publication year."

    for book in books:
        if book["book_id"] == book_id:
            return False, f"A book with ID {book_id} already exists."

    new_book = {
        "book_id": book_id,
        "title": title.strip(),
        "author": author.strip(),
        "year": year,
        "total_copies": copies,
        "available": copies,
        "issued_to": []
    }
    books.append(new_book)
    return True, f"Book '{new_book['title']}' added successfully."


def search_record(books, keyword, field="title"):
    """
    Search books by 'title', 'author' or 'book_id'.
    Returns a list of matching books (case-insensitive partial match).
    """
    if field not in ("title", "author", "book_id"):
        return []
    keyword = keyword.strip().lower()
    results = []
    for book in books:
        if keyword in str(book[field]).lower():
            results.append(book)
    return results


def find_book(books, book_id):
    """Return the book with this exact ID, or None."""
    for book in books:
        if book["book_id"] == book_id.strip().upper():
            return book
    return None


def delete_record(books, book_id):
    """Remove a book if none of its copies are issued. Returns (bool, message)."""
    book = find_book(books, book_id)
    if book is None:
        return False, "Book not found."
    if len(book["issued_to"]) > 0:
        return False, "Cannot delete: some copies are still issued."
    books.remove(book)
    return True, f"Book '{book['title']}' deleted."


# %% [5] Issue and return books
def issue_book(books, book_id, username):
    """Issue one copy of a book to a member. Returns (bool, message)."""
    book = find_book(books, book_id)
    if book is None:
        return False, "Book not found."
    if book["available"] <= 0:
        return False, f"No copies of '{book['title']}' are available."
    if username in book["issued_to"]:
        return False, "You already have this book."
    book["available"] -= 1
    book["issued_to"].append(username)
    log_transaction("ISSUE", book["book_id"], username)
    return True, f"'{book['title']}' issued to {username}."


def return_book(books, book_id, username):
    """Return a book that the member has borrowed. Returns (bool, message)."""
    book = find_book(books, book_id)
    if book is None:
        return False, "Book not found."
    if username not in book["issued_to"]:
        return False, "This book was not issued to you."
    book["available"] += 1
    book["issued_to"].remove(username)
    log_transaction("RETURN", book["book_id"], username)
    return True, f"'{book['title']}' returned by {username}."


# %% [6] Display and report functions
def display_books(books):
    """Print books in a neat table using a for loop."""
    if len(books) == 0:
        print("No books to show.")
        return
    print(f"{'ID':<6} {'Title':<32} {'Author':<22} {'Year':<6} {'Avail':<6}")
    print("-" * 76)
    for book in books:
        print(f"{book['book_id']:<6} {book['title'][:31]:<32} "
              f"{book['author'][:21]:<22} {book['year']:<6} "
              f"{book['available']}/{book['total_copies']}")


def generate_report(books):
    """
    Build summary statistics about the library.
    Returns a dictionary so it can be printed or tested.
    """
    total_titles = len(books)
    total_copies = 0
    issued_copies = 0
    out_of_stock = []
    for book in books:
        total_copies += book["total_copies"]
        issued_copies += book["total_copies"] - book["available"]
        if book["available"] == 0:
            out_of_stock.append(book["title"])

    transactions = read_transactions()
    issue_count = {}
    for row in transactions:
        if row["action"] == "ISSUE":
            issue_count[row["book_id"]] = issue_count.get(row["book_id"], 0) + 1

    most_popular = None
    if issue_count:
        top_id = max(issue_count, key=issue_count.get)
        top_book = find_book(books, top_id)
        name = top_book["title"] if top_book else top_id
        most_popular = f"{name} ({issue_count[top_id]} issues)"

    return {
        "total_titles": total_titles,
        "total_copies": total_copies,
        "issued_copies": issued_copies,
        "available_copies": total_copies - issued_copies,
        "out_of_stock": out_of_stock,
        "total_transactions": len(transactions),
        "most_popular": most_popular
    }


def print_report(report):
    """Print the report dictionary in a readable way."""
    print("\n========== LIBRARY REPORT ==========")
    print(f"Total titles       : {report['total_titles']}")
    print(f"Total copies       : {report['total_copies']}")
    print(f"Copies issued      : {report['issued_copies']}")
    print(f"Copies available   : {report['available_copies']}")
    print(f"Out of stock       : {', '.join(report['out_of_stock']) or 'None'}")
    print(f"Total transactions : {report['total_transactions']}")
    print(f"Most popular book  : {report['most_popular'] or 'No issues yet'}")
    print("====================================")


# %% [7] Safe input helpers
def get_int_input(prompt, low, high):
    """Keep asking until the user types a whole number between low and high."""
    while True:
        try:
            value = int(input(prompt))
            if low <= value <= high:
                return value
            print(f"Please enter a number from {low} to {high}.")
        except ValueError:
            print("Invalid input. Please type a number.")


def get_text_input(prompt):
    """Keep asking until the user types something that is not empty."""
    while True:
        text = input(prompt).strip()
        if text != "":
            return text
        print("This field cannot be empty.")


# %% [8] Menus and main loop
def login_screen(users):
    """Give the user 3 attempts to log in. Returns the user or None."""
    attempts = 3
    while attempts > 0:
        username = get_text_input("Username: ")
        password = get_text_input("Password: ")
        user = user_login(users, username, password)
        if user is not None:
            print(f"\nWelcome, {user['name']}! (role: {user['role']})")
            return user
        attempts -= 1
        print(f"Wrong username or password. {attempts} attempt(s) left.")
    print("Too many failed attempts.")
    return None


def admin_menu(books, user):
    """Menu loop for librarians/admins."""
    while True:
        print("\n--- ADMIN MENU ---")
        print("1. View all books\n2. Add book\n3. Search books\n"
              "4. Delete book\n5. Generate report\n6. Logout")
        choice = get_int_input("Choose (1-6): ", 1, 6)

        if choice == 1:
            display_books(books)
        elif choice == 2:
            ok, msg = add_record(books,
                                 get_text_input("Book ID: "),
                                 get_text_input("Title: "),
                                 get_text_input("Author: "),
                                 get_text_input("Year: "),
                                 get_text_input("Number of copies: "))
            print(msg)
            if ok:
                save_json(BOOKS_FILE, books)
        elif choice == 3:
            search_menu(books)
        elif choice == 4:
            ok, msg = delete_record(books, get_text_input("Book ID to delete: "))
            print(msg)
            if ok:
                save_json(BOOKS_FILE, books)
        elif choice == 5:
            print_report(generate_report(books))
        elif choice == 6:
            print("Logged out.")
            return


def member_menu(books, user):
    """Menu loop for library members (students)."""
    while True:
        print("\n--- MEMBER MENU ---")
        print("1. View all books\n2. Search books\n3. Issue book\n"
              "4. Return book\n5. My books\n6. Logout")
        choice = get_int_input("Choose (1-6): ", 1, 6)

        if choice == 1:
            display_books(books)
        elif choice == 2:
            search_menu(books)
        elif choice == 3:
            ok, msg = issue_book(books, get_text_input("Book ID: "), user["username"])
            print(msg)
            if ok:
                save_json(BOOKS_FILE, books)
        elif choice == 4:
            ok, msg = return_book(books, get_text_input("Book ID: "), user["username"])
            print(msg)
            if ok:
                save_json(BOOKS_FILE, books)
        elif choice == 5:
            my_books = [b for b in books if user["username"] in b["issued_to"]]
            display_books(my_books)
        elif choice == 6:
            print("Logged out.")
            return


def search_menu(books):
    """Ask what to search by, then show results."""
    print("Search by: 1. Title  2. Author  3. Book ID")
    option = get_int_input("Choose (1-3): ", 1, 3)
    fields = {1: "title", 2: "author", 3: "book_id"}
    results = search_record(books, get_text_input("Keyword: "), fields[option])
    print(f"{len(results)} result(s) found.")
    display_books(results)


def main():
    """Start the portal: load data, then keep running until the user exits."""
    print("=" * 40)
    print("   WELCOME TO THE LIBRARY PORTAL")
    print("=" * 40)
    books = load_json(BOOKS_FILE, [])
    users = load_json(USERS_FILE, [])
    if len(users) == 0:
        users = [{"username": "admin", "password": "admin123",
                  "name": "Librarian", "role": "admin"}]
        save_json(USERS_FILE, users)
        print("Created default admin account (admin / admin123).")

    while True:
        print("\n--- MAIN MENU ---\n1. Login\n2. Exit")
        choice = get_int_input("Choose (1-2): ", 1, 2)
        if choice == 1:
            user = login_screen(users)
            if user is None:
                continue
            if user["role"] == "admin":
                admin_menu(books, user)
            else:
                member_menu(books, user)
        else:
            save_json(BOOKS_FILE, books)
            print("Data saved. Goodbye!")
            break


# %% [9] Run the program
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user. Goodbye!")
