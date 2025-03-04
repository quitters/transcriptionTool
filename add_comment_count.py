import sqlite3

def add_comment_count_column(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE videos ADD COLUMN comment_count INTEGER DEFAULT 0")
    conn.commit()
    conn.close()
    print("comment_count column added successfully.")

if __name__ == "__main__":
    add_comment_count_column("transcripts.db")
