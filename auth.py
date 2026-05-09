import sqlite3

# -----------------------------
# DB CONNECTION
# -----------------------------
def connect_db():
    return sqlite3.connect("expense_tracker.db")


# -----------------------------
# CREATE USER TABLE
# -----------------------------
def create_user_table():

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# CREATE USER
# -----------------------------
def create_user(username, password):

    conn = connect_db()
    cursor = conn.cursor()

    try:

        cursor.execute("""
        INSERT INTO users (username, password)
        VALUES (?, ?)
        """, (username, password))

        conn.commit()
        conn.close()

        return True

    except:

        return False


# -----------------------------
# LOGIN USER
# -----------------------------
def login_user(username, password):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM users
    WHERE username=? AND password=?
    """, (username, password))

    data = cursor.fetchone()

    conn.close()

    return data