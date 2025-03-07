from flask import Flask, render_template, request, jsonify
import extract_transcripts

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    url_input = request.form['url_input']
    if 'youtube.com/channel/' in url_input or 'youtu.be' in url_input or '@' in url_input:
        # Handle channel URL
        if '@' in url_input:
            # Extract the channel name from the URL
            channel_name = url_input.split('@')[1]
            # Construct the channel URL (this may need to be adjusted based on actual channel IDs)
            url_input = f'https://www.youtube.com/{channel_name}'
        num_transcripts = int(request.form['num_transcripts'])
        transcripts = extract_transcripts.extract_transcripts(url_input, num_transcripts)
        return render_template('results.html', transcripts=transcripts)
    elif 'youtube.com/watch?v=' in url_input:
        # Handle video URL
        video_id = url_input.split('v=')[1]
        transcript = extract_transcripts.extract_transcript(video_id)
        return render_template('results.html', transcripts=[transcript])
    else:
        return render_template('index.html', error='Invalid URL. Please enter a valid YouTube channel or video URL.')

@app.route('/sort', methods=['GET'])
def sort_transcripts():
    sort_by = request.args.get('by')
    # Implement sorting logic based on the sort_by parameter
    # This is a placeholder for actual database fetching and sorting
    sorted_transcripts = fetch_sorted_transcripts(sort_by)
    return jsonify(sorted_transcripts)

@app.route('/add', methods=['POST'])
def add_video():
    data = request.get_json()
    video_id = data['videoId']
    # Implement logic to add video to the database
    success = add_video_to_database(video_id)
    return jsonify({'success': success})

@app.route('/transcripts', methods=['GET'])
def get_transcripts():
    conn = create_database()  # Ensure you have a connection to the database
    transcripts = fetch_transcripts(conn)
    return jsonify(transcripts)

@app.route('/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('videoId')
    transcript = extract_transcripts.extract_transcript(video_id)  # Assuming this function fetches the transcript
    return jsonify({'transcript': transcript})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
