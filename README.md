# Transcriber Project

## Overview
This project is a YouTube transcript extraction tool that allows users to extract transcripts from videos on specified YouTube channels. It provides a GUI for easy interaction and supports various sorting options.

## Features
- Extract transcripts from specified YouTube channels.
- Sort transcripts by various criteria: publish date, likes, views, duration, and comment count.
- Export transcripts in JSON or CSV format.

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/quitters/transcriptionTool.git
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Obtain your own `client_secret.json` file from Google Cloud Console and place it in the project directory.

## Usage
1. Run the GUI:
   ```bash
   python transcript_gui.py
   ```
2. Select a channel, sorting options, and the number of transcripts to extract.
3. Click on the "Extract Transcripts" button to save the transcripts.

## Troubleshooting
- Ensure that `client_secret.json` is not included in the repository for security reasons; use the provided `client_secret_template.json` as a reference.
- The `transcripts.db` file is not included in the repository to maintain privacy.
- If you encounter issues with the YouTube API, check your API key and permissions.

## Contributions
Feel free to fork the repository and submit pull requests for improvements or bug fixes.
