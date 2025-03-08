import spotipy
import random
import streamlit as st
from spotipy.oauth2 import SpotifyOAuth

# Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="52c56ae18ac346a3868bdb537c313f53",
    client_secret="a5df4992dcd34222b17cff6151d47510",
    redirect_uri="http://127.0.0.1:8888",
    scope="playlist-modify-public ugc-image-upload"
))

# **Step 1: Emotion-to-Genre Mapping**
EMOTION_GENRE_MAP = {
    "happy": "pop",
    "sad": "acoustic",
    "angry": "rock",
    "relaxed": "jazz",
    "energetic": "electronic",
    "romantic": "r&b",
    "nostalgic": "indie",
    "focused": "instrumental"
}

# **Step 2: Function to Get Tracks by Genre**
def get_top_tracks_by_genre(genre, track_limit=10, exclude_tracks=set()):
    """Fetch diverse songs for a given genre, ensuring max 1 song per artist and avoiding repeats."""
    try:
        search_results = sp.search(q=f"genre:{genre}", type="track", limit=50)
        tracks = []
        artist_seen = set()

        for track in search_results["tracks"]["items"]:
            artist_name = track["artists"][0]["name"]
            track_id = track["id"]

            # Ensure max 1 song per artist & avoid previously recommended tracks
            if artist_name not in artist_seen and track_id not in exclude_tracks:
                tracks.append({
                    "id": track_id,
                    "name": track["name"],
                    "artist": artist_name,
                    "album_cover": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                    "spotify_url": track["external_urls"]["spotify"]
                })
                artist_seen.add(artist_name)
                exclude_tracks.add(track_id)  # Add to exclusion list

            if len(tracks) >= track_limit:
                break

        random.shuffle(tracks)
        return tracks if tracks else None
    except Exception as e:
        st.error(f"Error fetching tracks: {e}")
        return None

# **Step 3: Function to Update Playlist**
def update_playlist(user_id, playlist_id, emotion):
    """Updates a Spotify playlist with new songs based on the detected emotion."""
    genre = EMOTION_GENRE_MAP.get(emotion, "pop")
    if "prev_tracks" not in st.session_state:
        st.session_state.prev_tracks = set()

    tracks = get_top_tracks_by_genre(genre, track_limit=10, exclude_tracks=st.session_state.prev_tracks)
    
    if not tracks:
        return "No tracks found for this emotion."

    track_uris = [sp.track(track["id"])["uri"] for track in tracks]
    
    try:
        sp.playlist_replace_items(playlist_id=playlist_id, items=track_uris)
        return tracks  # Return track details instead of a message
    except Exception as e:
        st.error(f"Error updating playlist: {e}")
        return None

# **Step 4: Streamlit Interface**
st.title("🎵 Dynamic Emotion-Based Playlist")
st.write("As your emotion changes, your playlist updates in real time!")

try:
    user_id = sp.current_user()["id"]
    playlist_name = "Emotion-Based Playlist"

    # **Check if playlist exists, otherwise create it**
    existing_playlists = sp.current_user_playlists().get("items", [])
    playlist_id = next((pl["id"] for pl in existing_playlists if pl["name"] == playlist_name), None)

    if not playlist_id:
        playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True)
        playlist_id = playlist["id"]

    # **Simulated Emotion (Replace with Real-Time Detection)**
    emotion = st.selectbox("Select Your Emotion:", list(EMOTION_GENRE_MAP.keys()))

    if st.button("Update Playlist"):
        tracks = update_playlist(user_id, playlist_id, emotion)
        if tracks:
            st.success(f"Playlist updated with {emotion.capitalize()} tracks!")

            # **Display Songs in Grid Layout (2 Rows x 5 Columns)**
            cols = st.columns(5)
            for i, track in enumerate(tracks):
                with cols[i % 5]:
                    st.image(track["album_cover"], width=150)
                    st.markdown(f"**[{track['name']}]({track['spotify_url']})**")
                    st.caption(track["artist"])

    # **Display Playlist Link**
    playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
    st.markdown(f"### 🎶 [Listen to Full Playlist on Spotify]({playlist_url})")

except Exception as e:
    st.error(f"An error occurred: {e}")
