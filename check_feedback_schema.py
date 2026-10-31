import sqlite3

def check_feedback_table():
    try:
        with sqlite3.connect('users.db') as con:
            cur = con.cursor()
            cur.execute("PRAGMA table_info(feedback);")
            schema = cur.fetchall()
            for column in schema:
                print(column)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_feedback_table()
