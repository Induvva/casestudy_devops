from db import connect


def init_db():
    with connect() as conn:
        c = conn.cursor()
        statements = (
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS trips (
                id BIGSERIAL PRIMARY KEY,
                username TEXT NOT NULL,
                destination TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                from_location TEXT,
                budget TEXT,
                itinerary_data TEXT,
                is_present INTEGER DEFAULT 1
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id BIGSERIAL PRIMARY KEY,
                username TEXT NOT NULL,
                feedback_text TEXT NOT NULL,
                star_rating INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS user_interests (
                id BIGSERIAL PRIMARY KEY,
                username TEXT NOT NULL,
                interest TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS trip_feedback (
                id BIGSERIAL PRIMARY KEY,
                trip_id BIGINT NOT NULL,
                username TEXT NOT NULL,
                enjoyed_most TEXT,
                could_be_better TEXT,
                recommend_friend TEXT,
                issues TEXT,
                star_rating INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user'",
            "ALTER TABLE feedback ADD COLUMN IF NOT EXISTS star_rating INTEGER",
            "UPDATE users SET role = 'user' WHERE role IS NULL",
        )
        for statement in statements:
            c.execute(statement)

if __name__ == '__main__':
    init_db()
    print("PostgreSQL database initialization completed.")
