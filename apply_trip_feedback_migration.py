import sqlite3

def apply_trip_feedback_migration():
    try:
        with sqlite3.connect('users.db') as con:
            cur = con.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS trip_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trip_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    enjoyed_most TEXT,
                    could_be_better TEXT,
                    recommend_friend TEXT,
                    issues TEXT,
                    star_rating INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trip_id) REFERENCES trips(id)
                )
            ''')
            con.commit()
            print("Migration applied: trip_feedback table created.")
    except Exception as e:
        print(f"Error applying migration: {e}")

if __name__ == '__main__':
    apply_trip_feedback_migration()
