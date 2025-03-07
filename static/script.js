document.getElementById('process-btn').addEventListener('click', function() {
    const urlInput = document.getElementById('url-input').value;
    const channelUI = document.getElementById('channel-ui');
    const videoUI = document.getElementById('video-ui');
    const statusMessage = document.getElementById('status-message');

    // Reset UI
    channelUI.classList.add('hidden');
    videoUI.classList.add('hidden');
    statusMessage.textContent = '';

    // URL validation and processing logic
    if (urlInput.includes('youtube.com/channel/') || urlInput.includes('youtu.be') || urlInput.includes('@')) {
        // Channel URL detected
        channelUI.classList.remove('hidden');
    } else if (urlInput.includes('youtube.com/watch?v=')) {
        // Video URL detected
        videoUI.classList.remove('hidden');
        // Fetch and display video thumbnail
        const videoId = urlInput.split('v=')[1];
        const thumbnailUrl = `https://img.youtube.com/vi/${videoId}/0.jpg`;
        document.getElementById('video-thumbnail').src = thumbnailUrl;
        document.getElementById('video-thumbnail').classList.remove('hidden');

        // Fetch and display transcript
        fetch(`/transcript?videoId=${videoId}`)
            .then(response => response.json())
            .then(data => {
                console.log('Transcript data:', data);  // Debugging statement
                const transcriptTextArea = document.getElementById('transcript-text');
                transcriptTextArea.value = data.transcript; // Assuming data.transcript contains the transcript text
                document.getElementById('transcript-preview').classList.remove('hidden');
            })
            .catch(error => {
                console.error('Error fetching transcript:', error);
                statusMessage.textContent = 'Error fetching transcript. Please try again.';
            });
    } else {
        // Invalid URL
        statusMessage.textContent = 'Invalid URL. Please enter a valid YouTube channel or video URL.';
    }
});

document.getElementById('sort-btn').addEventListener('click', function() {
    const sortOption = document.getElementById('db-sort-options').value;
    fetch(`/sort?by=${sortOption}`)
        .then(response => response.json())
        .then(data => {
            const transcriptList = document.getElementById('transcript-list');
            transcriptList.innerHTML = ''; // Clear existing list
            data.forEach(transcript => {
                const listItem = document.createElement('li');
                listItem.textContent = transcript.title;
                transcriptList.appendChild(listItem);
            });
        })
        .catch(error => console.error('Error:', error));
});

document.getElementById('add-to-db-btn').addEventListener('click', function() {
    const videoId = document.getElementById('url-input').value.split('v=')[1];
    fetch('/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ videoId: videoId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('video-confirmation').classList.remove('hidden');
        } else {
            alert('Error adding video to database.');
        }
    })
    .catch(error => console.error('Error:', error));
});

document.getElementById('theme-toggle').addEventListener('click', function() {
    console.log('Toggle button clicked'); // Debugging statement
    document.body.classList.toggle('dark-mode');
    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode);
});

// Check for saved user preference
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
}

window.onload = function() {
    fetch('/transcripts')
        .then(response => response.json())
        .then(data => {
            const transcriptList = document.getElementById('transcript-list');
            transcriptList.innerHTML = ''; // Clear existing list
            data.forEach(transcript => {
                const listItem = document.createElement('li');
                listItem.textContent = transcript.title;
                transcriptList.appendChild(listItem);
            });
        })
        .catch(error => console.error('Error fetching transcripts:', error));
};

// Additional functions for handling form submissions and displaying results will be added here.
