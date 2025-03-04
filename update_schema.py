import sqlite3

def update_schema(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add new columns if they don't exist
    cursor.execute("ALTER TABLE videos ADD COLUMN likes INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE videos ADD COLUMN views INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE videos ADD COLUMN duration INTEGER DEFAULT 0")

    conn.commit()
    conn.close()
    print("Schema updated successfully.")

if __name__ == "__main__":
    update_schema("transcripts.db")
