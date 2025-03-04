import google_auth_oauthlib.flow
import googleapiclient.discovery

# Define the scope for read-only access to YouTube
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

# Load client secrets and initiate authentication
flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
    "client_secret.json", scopes
)
credentials = flow.run_local_server(port=0)

# Build the YouTube service object
youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

# Test API call to get the authenticated user's channel info
request = youtube.channels().list(
    part="snippet,contentDetails,statistics",
    mine=True
)
response = request.execute()

print("Authenticated! Your channel info:")
print(response)
