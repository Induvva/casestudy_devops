import sqlite3
from werkzeug.security import generate_password_hash

def add_admin_user(username, email, password):
    hashed_password = generate_password_hash(password)
    try:
        with sqlite3.connect('users.db') as con:
            cur = con.cursor()
            # Check if user already exists
            cur.execute("SELECT * FROM users WHERE username = ?", (username,))
            if cur.fetchone():
                print(f"User {username} already exists.")
                return
            # Insert new admin user
            cur.execute("INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                        (username, email, hashed_password, 'admin'))
            con.commit()
            print(f"Admin user {username} added successfully.")
    except Exception as e:
        print(f"Error adding admin user: {e}")

if __name__ == "__main__":
    # Change these values as needed
    admin_username = "admin"
    admin_email = "admin@example.com"
    admin_password = "adminpassword"

    add_admin_user(admin_username, admin_email, admin_password)
