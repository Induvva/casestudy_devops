from db import connect

def check_feedback_table():
    try:
        with connect() as con:
            cur = con.cursor()
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = current_schema() AND table_name = 'feedback'
                ORDER BY ordinal_position
            """)
            schema = cur.fetchall()
            for column in schema:
                print(column)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_feedback_table()
