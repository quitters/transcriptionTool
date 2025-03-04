import sqlite3
import json
import csv
import tkinter as tk
from tkinter import ttk, messagebox

class TranscriptExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcript Extractor")

        # Channel Selection
        tk.Label(root, text="Channel:").grid(row=0, column=0, padx=10, pady=10)
        self.channel_var = tk.StringVar()
        self.channel_dropdown = ttk.Combobox(root, textvariable=self.channel_var)
        self.channel_dropdown.grid(row=0, column=1, padx=10, pady=10)
        self.channel_dropdown["values"] = self.get_channels()

        # Sorting Options
        tk.Label(root, text="Sort by:").grid(row=1, column=0, padx=10, pady=10)
        self.sort_var = tk.StringVar(value="publish_date DESC")
        ttk.Radiobutton(root, text="Newest First", variable=self.sort_var, value="publish_date DESC").grid(row=1, column=1, padx=10, pady=5)
        ttk.Radiobutton(root, text="Oldest First", variable=self.sort_var, value="publish_date ASC").grid(row=1, column=2, padx=10, pady=5)
        ttk.Radiobutton(root, text="Most Liked", variable=self.sort_var, value="likes DESC").grid(row=2, column=1, padx=10, pady=5)
        ttk.Radiobutton(root, text="Most Watched", variable=self.sort_var, value="views DESC").grid(row=2, column=2, padx=10, pady=5)
        ttk.Radiobutton(root, text="Longest", variable=self.sort_var, value="duration DESC").grid(row=3, column=1, padx=10, pady=5)
        ttk.Radiobutton(root, text="Shortest", variable=self.sort_var, value="duration ASC").grid(row=3, column=2, padx=10, pady=5)
        ttk.Radiobutton(root, text="Most Commented", variable=self.sort_var, value="comment_count DESC").grid(row=4, column=1, padx=10, pady=5)
        ttk.Radiobutton(root, text="Least Commented", variable=self.sort_var, value="comment_count ASC").grid(row=4, column=2, padx=10, pady=5)

        # Limit Selection
        tk.Label(root, text="Number of Transcripts:").grid(row=5, column=0, padx=10, pady=10)
        self.limit_var = tk.IntVar(value=250)
        ttk.Entry(root, textvariable=self.limit_var).grid(row=5, column=1, padx=10, pady=10)

        # Export Format
        tk.Label(root, text="Export Format:").grid(row=6, column=0, padx=10, pady=10)
        self.format_var = tk.StringVar(value="json")
        ttk.Radiobutton(root, text="JSON", variable=self.format_var, value="json").grid(row=6, column=1, padx=10, pady=5)
        ttk.Radiobutton(root, text="CSV", variable=self.format_var, value="csv").grid(row=6, column=2, padx=10, pady=5)

        # Extract Button
        ttk.Button(root, text="Extract Transcripts", command=self.extract_transcripts).grid(row=7, column=1, padx=10, pady=20)

    def get_channels(self):
        """Fetch all unique channels from the database and format with @ sign."""
        conn = sqlite3.connect("transcripts.db")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT channel_id FROM videos")
        channels = [f"@{row[0]}" for row in cursor.fetchall()]
        conn.close()
        return channels

    def extract_transcripts(self):
        """Extract transcripts based on user selections."""
        channel_id = self.channel_var.get().lstrip("@")
        sort_order = self.sort_var.get()
        limit = self.limit_var.get()
        export_format = self.format_var.get()

        if not channel_id:
            messagebox.showerror("Error", "Please select a channel.")
            return

        conn = sqlite3.connect("transcripts.db")
        cursor = conn.cursor()

        # Query transcripts
        cursor.execute(f"""
            SELECT v.video_id, v.title, v.publish_date, v.comment_count, GROUP_CONCAT(t.text, ' ') AS transcript_text
            FROM videos v
            LEFT JOIN transcripts t ON v.video_id = t.video_id
            WHERE v.channel_id = ?
            GROUP BY v.video_id
            ORDER BY {sort_order}
            LIMIT ?
        """, (channel_id, limit))

        results = cursor.fetchall()
        conn.close()

        if not results:
            messagebox.showinfo("Info", "No transcripts found for the selected channel.")
            return

        # Format results
        formatted_transcripts = []
        for row in results:
            formatted_transcripts.append({
                "video_id": row[0],
                "title": row[1],
                "publish_date": row[2],
                "comment_count": row[3],
                "transcript_text": row[4]
            })

        # Save to file
        output_file = f"transcripts_{channel_id}.{export_format}"
        if export_format == "json":
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(formatted_transcripts, f, indent=2)
        else:
            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["video_id", "title", "publish_date", "comment_count", "transcript_text"])
                writer.writeheader()
                writer.writerows(formatted_transcripts)

        messagebox.showinfo("Success", f"Successfully extracted {len(formatted_transcripts)} transcripts to {output_file}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TranscriptExtractorGUI(root)
    root.mainloop()
