import sqlite3

def add_channel_name_column(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE videos ADD COLUMN channel_name TEXT DEFAULT ''")
    conn.commit()
    conn.close()
    print("channel_name column added successfully.")

if __name__ == "__main__":
    add_channel_name_column("transcripts.db")
