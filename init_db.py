import sqlite3

def init_db():
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()

        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        # Create trips table with necessary columns
        c.execute('''
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                destination TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                from_location TEXT,
                budget TEXT,
                itinerary_data TEXT,
                is_present INTEGER DEFAULT 1
            )
        ''')

        # No need to check for columns that are already defined in the CREATE TABLE statement

        # Commit changes
        conn.commit()

        # Create feedback table
        c.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                feedback_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

if __name__ == '__main__':
    init_db()
    print("✅ users.db initialization check completed.")
