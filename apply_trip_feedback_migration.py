from init_db import init_db

def apply_trip_feedback_migration():
    try:
        init_db()
        print("Database schema migration applied.")
    except Exception as e:
        print(f"Error applying migration: {e}")

if __name__ == '__main__':
    apply_trip_feedback_migration()
