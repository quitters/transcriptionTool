#!/usr/bin/env python3

import os
import re
import sys
import sqlite3
import datetime

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from google.auth.exceptions import GoogleAuthError


# ----------------------------------------------------------
# Database Setup
# ----------------------------------------------------------
def create_database(db_path="transcripts.db"):
    """
    Create (if not exists) a SQLite database with tables for videos and transcripts.
    Returns a connection object.
    """
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create "videos" table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            title TEXT,
            channel_id TEXT,
            channel_name TEXT,
            publish_date TEXT
        )
    """)

    # Create "transcripts" table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            start_time REAL,
            text TEXT,
            FOREIGN KEY(video_id) REFERENCES videos(video_id)
        )
    """)

    # Commit changes
    conn.commit()
    return conn


# ----------------------------------------------------------
# 1. Authenticate with Google (OAuth 2.0 flow)
# ----------------------------------------------------------
def authenticate_youtube_api(client_secrets_file="client_secret.json"):
    """
    Authenticates with the YouTube Data API via OAuth 2.0 and returns a service resource.
    Make sure you have created OAuth 2.0 credentials in the Google Cloud Console
    and have placed the JSON file in the same directory.
    """
    # Define scopes for authentication
    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

    try:
        # Create flow instance
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes
        )
        # Run local server for authentication
        credentials = flow.run_local_server(port=0)

        # Build YouTube API client
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", credentials=credentials
        )
        return youtube
    except FileNotFoundError:
        print("Error: client_secret.json file not found. Please provide your OAuth client secrets file.")
        sys.exit(1)
    except GoogleAuthError as e:
        print(f"Google Auth error: {e}")
        sys.exit(1)


# ----------------------------------------------------------
# 2. Retrieve Single Video Transcript
# ----------------------------------------------------------
def parse_video_id_from_url(url):
    """
    Attempts to extract a video ID from common YouTube URL formats.
    Example URL formats:
      - https://www.youtube.com/watch?v=VIDEO_ID
      - https://youtu.be/VIDEO_ID
    Returns the video ID string or None if not found.
    """
    # Regex to match typical query parameter v=VIDEO_ID
    match = re.search(r"(?:v=)([A-Za-z0-9_-]{11})", url)
    if match:
        return match.group(1)

    # Regex to match https://youtu.be/VIDEO_ID
    match = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", url)
    if match:
        return match.group(1)

    return None


def download_single_video_transcript(youtube, conn, video_url):
    """
    Downloads the transcript for a single video and stores its metadata in the database.
    
    Parameters:
    youtube: The YouTube API client.
    conn: SQLite database connection.
    video_url: URL of the YouTube video.
    """
    # Function to download a single video transcript and store metadata in the database

    video_id = parse_video_id_from_url(video_url)
    if not video_id:
        print("Error: Could not parse video ID from the provided URL.")
        return None

    print(f"Fetching transcript for video ID: {video_id}")  # Debugging statement

    # Get video details from YouTube Data API
    try:
        request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response = request.execute()

        items = response.get("items", [])
        if not items:
            print("Error: No video found with that ID (it may be private, deleted, or invalid).")
            return None

        snippet = items[0]["snippet"]
        title = snippet.get("title", "Unknown Title")
        channel_id = snippet.get("channelId", "Unknown Channel")
        channel_name = snippet.get("channelTitle", "Unknown Channel Name")  # Fetch channel name
        publish_date = snippet.get("publishedAt", "")

        # Insert or update video record in the "videos" table
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO videos (video_id, title, channel_id, channel_name, publish_date)
            VALUES (?, ?, ?, ?, ?)
        """, (video_id, title, channel_id, channel_name, publish_date))
        conn.commit()

        print(f"Found video: {title} (ID: {video_id})")
        print("Attempting to download transcript...")

        # Fetch transcript
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
        except TranscriptsDisabled:
            print("Transcript is disabled for this video.")
            return None
        except NoTranscriptFound:
            print("No transcript found for this video (it may be auto-generated but not available).")
            return None
        except Exception as e:
            print(f"Error fetching transcript: {e}")
            return None

        # Store each line in the "transcripts" table
        transcript_text = ""  # Initialize transcript text
        for line in transcript:
            start_time = line["start"]
            text = line["text"]
            cursor.execute("""
                INSERT INTO transcripts (video_id, start_time, text)
                VALUES (?, ?, ?)
            """, (video_id, start_time, text))
            transcript_text += text + "\n"  # Append text to transcript

        conn.commit()
        print(f"Transcript for '{title}' has been saved into the database.")
        return transcript_text  # Return the full transcript text

    except googleapiclient.errors.HttpError as e:
        print(f"API Error: {e}")
        return None


# ----------------------------------------------------------
# 3. Advanced Option: Retrieve all transcripts from a channel
# ----------------------------------------------------------
def extract_channel_identifier(channel_url):
    """
    Basic attempt to parse various channel URL formats:
      - https://www.youtube.com/channel/UCXXXXXX
      - https://www.youtube.com/user/USERNAME
      - https://www.youtube.com/@HANDLE
    Return a dict: {"type": ..., "value": ...} or None if parsing fails.
    """
    # match for /channel/...
    match_channel = re.search(r"/channel/([^/\s]+)", channel_url)
    if match_channel:
        return {"type": "channel_id", "value": match_channel.group(1)}

    # match for /user/...
    match_user = re.search(r"/user/([^/\s]+)", channel_url)
    if match_user:
        return {"type": "username", "value": match_user.group(1)}

    # match for @HANDLE...
    match_handle = re.search(r"@([^/\s]+)", channel_url)
    if match_handle:
        return {"type": "handle", "value": match_handle.group(1)}

    return None


def get_channel_id(youtube, identifier_dict):
    """
    Convert user input (channelId, forUsername, or handle) into an actual channel ID
    using the YouTube Data API.
    """
    if identifier_dict is None:
        print("Error: Could not parse channel URL. Please check the URL.")
        return None

    id_type = identifier_dict["type"]
    value = identifier_dict["value"]

    if id_type == "channel_id":
        # Already have the channel ID
        return value
    elif id_type == "username":
        # channels.list using forUsername
        try:
            request = youtube.channels().list(
                part="id",
                forUsername=value
            )
            response = request.execute()
        except googleapiclient.errors.HttpError as e:
            print(f"API error: {e}")
            return None

        items = response.get("items", [])
        if not items:
            print(f"No channel found for username: {value}")
            return None
        return items[0]["id"]
    elif id_type == "handle":
        # Attempt a search for the handle
        # (As of writing, not all handle -> channel queries are 100% guaranteed in the Data API)
        handle_stripped = value.replace("@", "")
        try:
            request = youtube.search().list(
                part="snippet",
                q=handle_stripped,
                type="channel",
                maxResults=1
            )
            response = request.execute()
            items = response.get("items", [])
            if not items:
                print(f"No channel found by searching handle: {value}")
                return None
            return items[0]["snippet"]["channelId"]
        except googleapiclient.errors.HttpError as e:
            print(f"API error: {e}")
            return None

    print("Unrecognized channel identifier type.")
    return None


def get_uploads_playlist_id(youtube, channel_id):
    """
    Retrieve the 'uploads' playlist for a channel.
    """
    try:
        request = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        )
        response = request.execute()

        items = response.get("items", [])
        if not items:
            print(f"No channel found for ID: {channel_id}")
            return None

        uploads_playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
        return uploads_playlist_id
    except googleapiclient.errors.HttpError as e:
        print(f"API error: {e}")
        return None


def get_all_video_ids(youtube, uploads_playlist_id):
    """
    Paginate through the uploads playlist to get all video IDs and metadata.
    """
    video_data = []
    next_page_token = None

    while True:
        try:
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
        except googleapiclient.errors.HttpError as e:
            print(f"API error retrieving playlist items: {e}")
            break

        for item in response.get("items", []):
            vid_id = item["snippet"]["resourceId"]["videoId"]
            vid_title = item["snippet"]["title"]
            publish_date = item["snippet"]["publishedAt"]
            channel_id = item["snippet"]["channelId"]
            video_data.append((vid_id, vid_title, publish_date, channel_id))

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return video_data


def download_channel_videos_transcripts(youtube, conn, channel_url):
    """
    Advanced function to fetch transcripts for all (or selected) videos in a channel.
    1. Parse the channel ID.
    2. Get the uploads playlist ID.
    3. Retrieve all video IDs.
    4. Let user select which ones to process.
    5. Download transcripts for those videos.
    """
    identifier_dict = extract_channel_identifier(channel_url)
    channel_id = get_channel_id(youtube, identifier_dict)
    if not channel_id:
        return

    uploads_playlist_id = get_uploads_playlist_id(youtube, channel_id)
    if not uploads_playlist_id:
        return

    video_data = get_all_video_ids(youtube, uploads_playlist_id)
    total_videos = len(video_data)
    print(f"Found {total_videos} videos in this channel.")

    if total_videos == 0:
        return

    # Show up to 50, let user pick
    max_display = 50
    print("\n=== Video List (showing up to 50) ===")
    for i, (vid_id, vid_title, pub_date, ch_id) in enumerate(video_data[:max_display], start=1):
        print(f"{i}. {vid_title} (https://youtu.be/{vid_id})")

    if total_videos > max_display:
        print(f"... (only first {max_display} shown) ...")

    print()
    print("Enter the numbers of the videos you want transcripts for (comma-separated), or 'all' to select all.")
    selection = input("> ").strip().lower()

    if selection == "all":
        selected_indices = range(1, total_videos + 1)
    else:
        try:
            selected_indices = [int(x) for x in selection.split(",")]
        except ValueError:
            print("Invalid input.")
            return

    # Filter valid indices
    valid_videos = []
    for idx in selected_indices:
        if 1 <= idx <= total_videos:
            valid_videos.append(video_data[idx - 1])
        else:
            print(f"Warning: ignoring invalid selection index {idx}")

    if not valid_videos:
        print("No valid videos selected.")
        return

    # Download transcripts
    print("\n=== Downloading transcripts... ===")
    cursor = conn.cursor()

    for vid_id, vid_title, pub_date, ch_id in valid_videos:
        # Insert or update the video record
        cursor.execute("""
            INSERT OR IGNORE INTO videos (video_id, title, channel_id, publish_date)
            VALUES (?, ?, ?, ?)
        """, (vid_id, vid_title, ch_id, pub_date))
        conn.commit()

        print(f"Downloading transcript for: {vid_title} (ID: {vid_id})")
        try:
            transcript = YouTubeTranscriptApi.get_transcript(vid_id)
            # Insert transcript lines into DB
            for line in transcript:
                start_time = line["start"]
                text = line["text"]
                cursor.execute("""
                    INSERT INTO transcripts (video_id, start_time, text)
                    VALUES (?, ?, ?)
                """, (vid_id, start_time, text))
            conn.commit()
            print(f"Transcript stored for '{vid_title}'")

        except TranscriptsDisabled:
            print(f"Transcript disabled for {vid_title}.")
        except NoTranscriptFound:
            print(f"No transcript found for {vid_title}.")
        except Exception as e:
            print(f"Error retrieving transcript for {vid_title}: {e}")


# ----------------------------------------------------------
# Fetch transcripts from the database
# ----------------------------------------------------------
def fetch_transcripts(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM videos")  # Adjust the query as needed
    transcripts = cursor.fetchall()
    return [{"title": title} for (title,) in transcripts]


# ----------------------------------------------------------
# Main
# ----------------------------------------------------------
def main():
    """
    Main function to run the YouTube Transcript Tool.
    """
    print("=== YouTube Transcript Tool (Single Video or Channel) ===")

    # Initialize our local DB
    conn = create_database(db_path="transcripts.db")

    # Authentication
    print("\nStep 1: Authenticating with Google...")
    youtube = authenticate_youtube_api()

    while True:
        print("\nSelect an option:")
        print("1. Download transcript for a single YouTube video")
        print("2. Advanced: Download transcripts from an entire channel")
        print("3. Fetch transcripts from the database")
        print("4. Exit")
        choice = input("> ").strip()

        if choice == "1":
            video_url = input("Enter the full YouTube video URL: ").strip()
            transcript_text = download_single_video_transcript(youtube, conn, video_url)
            if transcript_text:
                print("\nTranscript:")
                print(transcript_text)
        elif choice == "2":
            channel_url = input("Enter the channel URL (e.g., https://www.youtube.com/channel/UC...): ").strip()
            download_channel_videos_transcripts(youtube, conn, channel_url)
        elif choice == "3":
            transcripts = fetch_transcripts(conn)
            for transcript in transcripts:
                print(transcript)
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

    conn.close()


if __name__ == "__main__":
    main()
