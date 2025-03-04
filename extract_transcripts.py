import sqlite3
import json

# Connect to the database
def extract_top_transcripts(db_path="transcripts.db", output_file="top_transcripts.json", limit=250):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query top videos by publish date (newest first) for the specified channel
    cursor.execute("""
        SELECT v.video_id, v.title, v.publish_date, GROUP_CONCAT(t.text, ' ') AS transcript_text
        FROM videos v
        LEFT JOIN transcripts t ON v.video_id = t.video_id
        WHERE v.channel_id = 'UCXXXXXX'  # Replace with the actual channel ID for @DragonsDenGlobal
        GROUP BY v.video_id
        ORDER BY v.publish_date DESC
        LIMIT ?
    """, (limit,))

    # Fetch results
    results = cursor.fetchall()

    # Format as a list of dictionaries
    formatted_transcripts = []
    for row in results:
        formatted_transcripts.append({
            "video_id": row[0],
            "title": row[1],
            "publish_date": row[2],
            "transcript_text": row[3]
        })

    # Save to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(formatted_transcripts, f, indent=2)

    print(f"Successfully extracted {len(formatted_transcripts)} transcripts to {output_file}")


if __name__ == "__main__":
    extract_top_transcripts()
