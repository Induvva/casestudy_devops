from getpass import getpass

from werkzeug.security import generate_password_hash

from db import connect


def add_admin_user(username, email, password):
    hashed_password = generate_password_hash(password)
    try:
        with connect() as con:
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
    admin_username = input("Admin username: ").strip()
    admin_email = input("Admin email: ").strip()
    admin_password = getpass("Admin password: ")
    if not admin_username or not admin_email or not admin_password:
        raise SystemExit("Username, email, and password are required.")

    add_admin_user(admin_username, admin_email, admin_password)
