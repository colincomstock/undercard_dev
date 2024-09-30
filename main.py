import random
import pandas as pd
import requests
import base64
import json
import pandas
import os
from dotenv import load_dotenv

# Load client id and secret
load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

def get_access_token(client_id, client_secret):
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials'
    }
    response = requests.post(auth_url, headers=headers, data=data)
    if response.status_code != 200:
        raise Exception(f"Failed to authenticate with Spotify API: {response.text}")
    access_token = response.json()['access_token']
    return access_token


def extract_artist_ids_from_uris(uris):
    artist_ids = []
    for uri in uris:
        parts = uri.split(':')
        if len(parts) == 3 and parts[0] == 'spotify' and parts[1] == 'artist':
            artist_ids.append(parts[2])
        else:
            print(f"Invalid URI format: {uri}")
    return artist_ids


def get_recommendations(access_token, seed_artists, limit=50, max_popularity=30):
    url = 'https://api.spotify.com/v1/recommendations'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'seed_artists': ','.join(seed_artists),
        'limit': limit,
        'max_popularity': max_popularity
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to get recommendations: {response.text}")
    data = response.json()
    return data['tracks']


def extract_small_artists(tracks, access_token, popularity_threshold=30, follower_threshold=10000):
    artist_ids = set()
    for track in tracks:
        for artist in track['artists']:
            artist_ids.add(artist['id'])
    artist_ids = list(artist_ids)
    small_artists = []
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    # Spotify allows up to 50 artists per request
    for i in range(0, len(artist_ids), 50):
        batch = artist_ids[i:i + 50]
        url = 'https://api.spotify.com/v1/artists'
        params = {
            'ids': ','.join(batch)
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to get artist details: {response.text}")
        artists_data = response.json()['artists']
        for artist in artists_data:
            if (artist['popularity'] <= popularity_threshold and
                    artist['followers']['total'] <= follower_threshold):
                small_artists.append({
                    'name': artist['name'],
                    'id': artist['id'],
                    'popularity': artist['popularity'],
                    'followers': artist['followers']['total'],
                    'genres': artist['genres'],
                    'external_url': artist['external_urls']['spotify']
                })
    return small_artists

def generate_unique_filename(extension='csv'):
    while True:
        # Generate a random 8-digit number
        random_number = random.randint(10000000, 99999999)
        filename = f"{random_number}.{extension}"
        # Check if the file already exists
        if not os.path.exists(filename):
            return filename

def save_to_csv(small_artists):
    # Generate a unique filename
    filename = generate_unique_filename()

    # Convert the list of dictionaries (small_artists) to a DataFrame
    new_data = pd.DataFrame(small_artists)

    # Save the data to the CSV file with the unique filename
    new_data.to_csv(filename, index=False)
    print(f"Data saved to {filename}")


def main():
    # Step 1: Authenticate and get access token
    access_token = get_access_token(CLIENT_ID, CLIENT_SECRET)

    # Step 2: Define your seed artists (Spotify artist URIs)
    # Replace these with actual Spotify URIs of small artists
    seed_artist_uris = [
        'spotify:artist:08sk1ebt8DoanTgWdpdsEs',  # Example small artist URI
        'spotify:artist:6Pqi8pJCwwtAlInEcJbcDX'  # Another example small artist URI
    ]

    # Extract artist IDs from URIs
    seed_artists = extract_artist_ids_from_uris(seed_artist_uris)

    # Step 3: Get recommendations based on seed artists
    tracks = get_recommendations(access_token, seed_artists, limit=100, max_popularity=30)
    for track in tracks:
        print(track)

    # Step 4: Extract and filter small artists from the recommended tracks
    small_artists = extract_small_artists(tracks, access_token, popularity_threshold=30, follower_threshold=10000)

    # Step 5: Output the results
    print("Discovered Small Artists:")
    for artist in small_artists:
        print(f"Name: {artist['name']}")
        print(f"ID: {artist['id']}")
        print(f"Popularity: {artist['popularity']}")
        print(f"Followers: {artist['followers']}")
        print(f"Genres: {', '.join(artist['genres']) if artist['genres'] else 'N/A'}")
        print(f"Spotify URL: {artist['external_url']}")
        print("-" * 40)

    # Save the results to a CSV file with a unique filename
    save_to_csv(small_artists)


if __name__ == "__main__":
    main()
