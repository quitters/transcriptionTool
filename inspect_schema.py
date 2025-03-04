import sqlite3

def inspect_schema(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(videos)")
    columns = cursor.fetchall()
    conn.close()

    print("Columns in 'videos' table:")
    for column in columns:
        print(column)

if __name__ == "__main__":
    inspect_schema("transcripts.db")
