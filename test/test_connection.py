"""Pytest suite for libopensonic covering the entire public API."""

# pylint: disable=W0212

from unittest.mock import AsyncMock, patch
import pytest

from libopensonic import AsyncConnection
from libopensonic._async.connection import API_VERSION
from libopensonic.media.media_types import (
    Album, AlbumID3, AlbumInfo, ArtistInfo, ArtistInfo2, ArtistWithAlbumsID3, Artists, Bookmark, ChatMessage, Child, Directory,
    Genre, Indexes, InternetRadioStation, JukeboxPlaylist, JukeboxStatus,
    Lyrics, MusicFolder, NowPlayingEntry, OpenSubsonicExtension, Playlist,
    PlayQueue, PlayQueueByIndex, PodcastChannel, PodcastEpisode, PodcastStatus,
    ScanStatus, SearchResult2, SearchResult3, Share, SonicMatch, Starred,
    Starred2, StructuredLyrics, TokenInfo, TranscodeDecision, User,
)
from libopensonic import errors


def make_response(data, status="ok"):
    """Build a minimal subsonic response envelope."""
    return {
        "subsonic-response": {
            "status": status,
            "version": API_VERSION,
            **data
        }
    }


def set_json_response(response, data):
    """Configure a mock ClientResponse to return data from .json()."""
    async def json_coro():
        return data
    response.json = json_coro
    return response


# ============================================================================
# CONSTRUCTOR TESTS
# ============================================================================

class TestConstructor:
    """Tests for AsyncConnection.__init__ and properties."""

    def test_basic_construction(self, mock_session):
        """Test basic connection creation."""
        with patch('aiohttp.ClientSession', return_value=mock_session):
            c = AsyncConnection(
                base_url="https://subsonic.example.com",
                username="user",
                password="pass"
            )
            assert c.base_url == "https://subsonic.example.com"
            assert c._hostname == "subsonic.example.com"
            assert c.username == "user"
            assert c.password == "pass"
            assert c.port == 4040
            assert c.api_version == API_VERSION

    def test_url_with_path(self, mock_session):
        """Test server_path handling."""
        with patch('aiohttp.ClientSession', return_value=mock_session):
            c = AsyncConnection(
                base_url="https://example.com",
                username="u",
                password="p",
                server_path="/path/to/subsonic"
            )
            assert c.server_path == "path/to/subsonic/rest"

    def test_api_key_auth(self, mock_session):
        """Test API key authentication."""
        with patch('aiohttp.ClientSession', return_value=mock_session):
            c = AsyncConnection(
                base_url="http://localhost",
                username=None,
                password=None,
                api_key="secret-key-123"
            )
            assert c.api_key == "secret-key-123"

    def test_credential_error_no_auth(self):
        """Test error when no credentials provided."""
        with pytest.raises(errors.CredentialError):
            AsyncConnection(
                base_url="http://localhost",
                username=None,
                password=None
            )

    def test_credential_error_both_auth_methods(self):
        """Test error when both password and API key provided."""
        with pytest.raises(errors.CredentialError):
            AsyncConnection(
                base_url="http://localhost",
                username="user",
                password="pass",
                api_key="key"
            )

    def test_property_setters(self, conn):
        """Test property getters/setters."""
        # base_url
        conn.base_url = "https://new.example.com"
        assert conn.base_url == "https://new.example.com"
        assert conn._hostname == "new.example.com"

        # port
        conn.port = 8080
        assert conn.port == 8080

        # username
        conn.username = "newuser"
        assert conn.username == "newuser"

        # password
        conn.password = "newpass"
        assert conn.password == "newpass"

        # api_key
        conn.api_key = "newkey"
        assert conn.api_key == "newkey"

        # app_name
        conn.app_name = "new-app"
        assert conn.app_name == "new-app"

        # server_path
        conn.server_path = "/api"
        assert conn.server_path == "api/rest"

        # legacy_auth
        conn.legacy_auth = True
        assert conn.legacy_auth is True

        # use_get
        conn.use_get = True
        assert conn.use_get is True


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

class TestAuthentication:
    """Tests for authentication parameter generation."""

    @pytest.mark.asyncio
    async def test_token_auth_post(self, conn, mock_session, mock_response):
        """Test token-based auth in POST request."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        await conn.ping()

        call_args = mock_session.post.call_args
        data = call_args.kwargs.get('data', {})
        assert 'u' in str(data) or 't' in str(call_args)
        assert 's' in str(call_args) or 's' in str(data)

    def test_hex_encoding(self, conn):
        """Test hex encoding for legacy auth."""
        encoded = conn._hex_enc("test")
        assert encoded == "74657374"  # hex for 'test'

    def test_ts2milli(self, conn):
        """Test timestamp conversion to milliseconds."""
        assert conn._ts2milli(1) == 1000
        assert conn._ts2milli(None) is None


# ============================================================================
# SYSTEM/PING TESTS
# ============================================================================

class TestSystemMethods:
    """Tests for ping, getLicense, etc."""

    @pytest.mark.asyncio
    async def test_ping_success(self, conn, mock_session, mock_response):
        """Test successful ping."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.ping()
        assert result is True

    @pytest.mark.asyncio
    async def test_ping_failure(self, conn, mock_session, mock_response):
        """Test failed ping raises exception."""
        set_json_response(mock_response, {
            "subsonic-response": {
                "status": "failed",
                "version": API_VERSION,
                "error": {"code": 40, "message": "Unauthorized"}
            }
        })
        mock_session.post = AsyncMock(return_value=mock_response)

        with pytest.raises(errors.SonicError):
            await conn.ping()

# ============================================================================
# CHAT METHODS
# ============================================================================

class TestChatMethods:
    """Tests for chat-related methods."""

    @pytest.mark.asyncio
    async def test_add_chat_message(self, conn, mock_session, mock_response):
        """Test add_chat_message."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.add_chat_message("Hello world")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_chat_messages_empty(self, conn, mock_session, mock_response):
        """Test get_chat_messages with no messages."""
        set_json_response(mock_response, make_response({"chatMessages": {}}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_chat_messages()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_chat_messages_with_data(self, conn, mock_session, mock_response):
        """Test get_chat_messages with messages."""
        messages = {
            "chatMessages": {
                "chatMessage": [
                    {"username": "user1", "time": 1234567890000, "message": "Hello"}
                ]
            }
        }
        set_json_response(mock_response, make_response(messages))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_chat_messages()
        assert len(result) == 1
        assert isinstance(result[0], ChatMessage)
        assert result[0].username == "user1"


# ============================================================================
# BOOKMARK METHODS
# ============================================================================

class TestBookmarkMethods:
    """Tests for bookmark methods."""

    @pytest.mark.asyncio
    async def test_create_bookmark(self, conn, mock_session, mock_response):
        """Test create_bookmark."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.create_bookmark("song-id-123", 5000, "My bookmark")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_bookmarks_empty(self, conn, mock_session, mock_response):
        """Test get_bookmarks with no bookmarks."""
        set_json_response(mock_response, make_response({"bookmarks": {}}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_bookmarks()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_bookmarks_with_data(self, conn, mock_session, mock_response):
        """Test get_bookmarks with bookmarks."""
        bookmarks = {
            "bookmarks": {
                "bookmark": [{
                    "position": 5000,
                    "username": "user",
                    "created": "2024-01-01T00:00:00",
                    "changed": "2024-01-01T00:00:00",
                    "entry": {
                        "id": "song-1",
                        "isDir": False,
                        "title": "Song Title"
                    }
                }]
            }
        }
        set_json_response(mock_response, make_response(bookmarks))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_bookmarks()
        assert len(result) == 1
        assert isinstance(result[0], Bookmark)
        assert result[0].position == 5000

    @pytest.mark.asyncio
    async def test_delete_bookmark(self, conn, mock_session, mock_response):
        """Test delete_bookmark."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.delete_bookmark("song-id-123")
        assert result is True


# ============================================================================
# INTERNET RADIO METHODS
# ============================================================================

class TestInternetRadioMethods:
    """Tests for internet radio station methods."""

    @pytest.mark.asyncio
    async def test_create_internet_radio_station(self, conn, mock_session, mock_response):
        """Test create_internet_radio_station."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.create_internet_radio_station(
            "http://stream.example.com",
            "Test Station",
            "http://homepage.example.com"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_internet_radio_station(self, conn, mock_session, mock_response):
        """Test delete_internet_radio_station."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.delete_internet_radio_station("station-123")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_internet_radio_stations_none(self, conn, mock_session, mock_response):
        """Test get_internet_radio_stations with no stations."""
        set_json_response(mock_response, make_response({
            "internetRadioStations": {}
        }))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_internet_radio_stations()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_internet_radio_stations_empty(self, conn, mock_session, mock_response):
        """Test get_internet_radio_stations with no stations."""
        set_json_response(mock_response, make_response({
            "internetRadioStations": {"internetRadioStation": []}
        }))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_internet_radio_stations()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_internet_radio_stations_with_data(self, conn, mock_session, mock_response):
        """Test get_internet_radio_stations with stations."""
        stations = {
            "internetRadioStations": {
                "internetRadioStation": [{
                    "id": "station-1",
                    "name": "Station One",
                    "streamUrl": "http://stream1.example.com"
                }]
            }
        }
        set_json_response(mock_response, make_response(stations))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_internet_radio_stations()
        assert len(result) == 1
        assert isinstance(result[0], InternetRadioStation)
        assert result[0].name == "Station One"

    @pytest.mark.asyncio
    async def test_update_internet_radio_station(self, conn, mock_session, mock_response):
        """Test update_internet_radio_station."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.update_internet_radio_station(
            "station-123",
            "http://newstream.example.com",
            "Updated Station"
        )
        assert result is True


# ============================================================================
# PLAYLIST METHODS
# ============================================================================

class TestPlaylistMethods:
    """Tests for playlist CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_playlist_name_only(self, conn, mock_session, mock_response):
        """Test create_playlist with name only."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.create_playlist(name="My Playlist")
        assert result is True

    @pytest.mark.asyncio
    async def test_create_playlist_update_mode(self, conn, mock_session, mock_response):
        """Test create_playlist in update mode with song IDs."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.create_playlist(
            playlist_id="pl-123",
            song_ids=["song-1", "song-2"]
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_playlist(self, conn, mock_session, mock_response):
        """Test delete_playlist."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.delete_playlist("pl-123")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_playlists_empty(self, conn, mock_session, mock_response):
        """Test get_playlists with no playlists."""
        set_json_response(mock_response, make_response({"playlists": {}}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_playlists()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_playlists_with_data(self, conn, mock_session, mock_response):
        """Test get_playlists with playlists."""
        playlists = {
            "playlists": {
                "playlist": [{
                    "id": "pl-1",
                    "name": "My Playlist",
                    "songCount": 10,
                    "duration": 3600,
                    "created": "2024-01-01T00:00:00",
                    "changed": "2024-01-01T00:00:00",
                    "owner": "user1"
                }]
            }
        }
        set_json_response(mock_response, make_response(playlists))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_playlists()
        assert len(result) == 1
        assert isinstance(result[0], Playlist)
        assert result[0].name == "My Playlist"

    @pytest.mark.asyncio
    async def test_get_playlist(self, conn, mock_session, mock_response):
        """Test get_playlist with full details."""
        playlist = {
            "playlist": {
                "id": "pl-1",
                "name": "Full Playlist",
                "songCount": 2,
                "duration": 300,
                "created": "2024-01-01T00:00:00",
                "changed": "2024-01-01T00:00:00",
                "entry": [
                    {"id": "song-1", "isDir": False, "title": "Track 1"},
                    {"id": "song-2", "isDir": False, "title": "Track 2"}
                ]
            }
        }
        set_json_response(mock_response, make_response(playlist))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_playlist("pl-1")
        assert isinstance(result, Playlist)
        assert result.id == "pl-1"
        assert result.entry and len(result.entry) == 2

    @pytest.mark.asyncio
    async def test_update_playlist(self, conn, mock_session, mock_response):
        """Test update_playlist."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.update_playlist(
            lid="pl-123",
            name="Updated Name",
            song_ids_to_add=["song-3"],
            song_indices_to_remove=[0]
        )
        assert result is True


# ============================================================================
# PODCAST METHODS
# ============================================================================

class TestPodcastMethods:
    """Tests for podcast methods."""

    @pytest.mark.asyncio
    async def test_create_podcast_channel(self, conn, mock_session, mock_response):
        """Test create_podcast_channel."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.create_podcast_channel("http://feed.example.com/podcast")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_podcast_channel(self, conn, mock_session, mock_response):
        """Test delete_podcast_channel."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.delete_podcast_channel("pod-123")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_podcast_episode(self, conn, mock_session, mock_response):
        """Test delete_podcast_episode."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.delete_podcast_episode("ep-123")
        assert result is True

    @pytest.mark.asyncio
    async def test_download_podcast_episode(self, conn, mock_session, mock_response):
        """Test download_podcast_episode."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.download_podcast_episode("ep-123")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_podcasts_empty(self, conn, mock_session, mock_response):
        """Test get_podcasts with no podcasts."""
        set_json_response(mock_response, make_response({"podcasts": {}}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_podcasts()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_podcasts_with_channels(self, conn, mock_session, mock_response):
        """Test get_podcasts with channels."""
        podcasts = {
            "podcasts": {
                "channel": [{
                    "id": "pod-1",
                    "url": "http://feed.example.com",
                    "status": "completed",
                    "title": "My Podcast"
                }]
            }
        }
        set_json_response(mock_response, make_response(podcasts))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_podcasts(inc_episodes=True)
        assert len(result) == 1
        assert isinstance(result[0], PodcastChannel)
        assert result[0].status == PodcastStatus.completed

    @pytest.mark.asyncio
    async def test_get_newest_podcasts_empty(self, conn, mock_session, mock_response):
        """Test get_newest_podcasts with no episodes."""
        set_json_response(mock_response, make_response({"newestPodcasts": {}}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_newest_podcasts()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_newest_podcasts_with_episodes(self, conn, mock_session, mock_response):
        """Test get_newest_podcasts with episodes."""
        episodes = {
            "newestPodcasts": {
                "episode": [{
                    "id": "ep-1",
                    "channelId": "pod-1",
                    "isDir": False,
                    "title": "Episode 1",
                    "status": "completed",
                    "streamId": "stream-1"
                }]
            }
        }
        set_json_response(mock_response, make_response(episodes))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_newest_podcasts(count=20)
        assert len(result) == 1
        assert isinstance(result[0], PodcastEpisode)

    @pytest.mark.asyncio
    async def test_refresh_podcasts(self, conn, mock_session, mock_response):
        """Test refresh_podcasts."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.refresh_podcasts()
        assert result is True


# ============================================================================
# SHARE METHODS
# ============================================================================

class TestShareMethods:
    """Tests for share methods."""

    @pytest.mark.asyncio
    async def test_create_share(self, conn, mock_session, mock_response):
        """Test create_share."""
        shares = {
            "shares": {
                "share": [{
                    "id": "sh-1",
                    "url": "http://share.example.com/s/abc123",
                    "username": "user1",
                    "created": "2024-01-01T00:00:00",
                    "visitCount": 0
                }]
            }
        }
        set_json_response(mock_response, make_response(shares))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.create_share(
            shids=["song-1", "song-2"],
            description="My share"
        )
        assert isinstance(result, Share)
        assert result.id == "sh-1"

    @pytest.mark.asyncio
    async def test_delete_share(self, conn, mock_session, mock_response):
        """Test delete_share."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.delete_share("sh-123")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_shares_empty(self, conn, mock_session, mock_response):
        """Test get_shares with no shares."""
        set_json_response(mock_response, make_response({"shares": {}}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_shares()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_shares_with_data(self, conn, mock_session, mock_response):
        """Test get_shares with shares."""
        shares = {
            "shares": {
                "share": [{
                    "id": "sh-1",
                    "url": "http://share.example.com/s/abc",
                    "username": "user1",
                    "created": "2024-01-01T00:00:00",
                    "visitCount": 5
                }]
            }
        }
        set_json_response(mock_response, make_response(shares))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_shares()
        assert len(result) == 1
        assert isinstance(result[0], Share)

    @pytest.mark.asyncio
    async def test_update_share(self, conn, mock_session, mock_response):
        """Test update_share."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.update_share(
            shid="sh-123",
            description="Updated description"
        )
        assert result is True


# ============================================================================
# USER METHODS
# ============================================================================

class TestUserMethods:
    """Tests for user management."""

    @pytest.mark.asyncio
    async def test_change_password(self, conn, mock_session, mock_response):
        """Test change_password."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.change_password("user1", "newpassword")
        assert result is True

    @pytest.mark.asyncio
    async def test_create_user(self, conn, mock_session, mock_response):
        """Test create_user with minimal params."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.create_user(
            username="newuser",
            password="pass123",
            email="new@example.com"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_create_user_with_roles(self, conn, mock_session, mock_response):
        """Test create_user with all role parameters."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.create_user(
            username="adminuser",
            password="adminpass",
            email="admin@example.com",
            admin_role=True,
            settings_role=True,
            download_role=True,
            upload_role=True,
            playlist_role=True,
            cover_art_role=True,
            comment_role=True,
            podcast_role=True,
            stream_role=True,
            jukebox_role=True,
            share_role=True,
            video_conversion_role=True,
            music_folder_id=1
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_user(self, conn, mock_session, mock_response):
        """Test delete_user."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.delete_user("user1")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_user(self, conn, mock_session, mock_response):
        """Test get_user."""
        user = {
            "user": {
                "username": "user1",
                "scrobblingEnabled": True,
                "adminRole": False,
                "settingsRole": True,
                "downloadRole": False,
                "uploadRole": False,
                "playlistRole": True,
                "coverArtRole": False,
                "commentRole": False,
                "podcastRole": False,
                "streamRole": True,
                "jukeboxRole": False,
                "shareRole": False,
                "videoConversionRole": False
            }
        }
        set_json_response(mock_response, make_response(user))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_user("user1")
        assert isinstance(result, User)
        assert result.username == "user1"
        assert result.admin_role is False

    @pytest.mark.asyncio
    async def test_get_users(self, conn, mock_session, mock_response):
        """Test get_users."""
        users = {
            "users": {
                "user": [
                    {"username": "user1", "scrobblingEnabled": True, "adminRole": True,
                     "settingsRole": True, "downloadRole": True, "uploadRole": False,
                     "playlistRole": True, "coverArtRole": False, "commentRole": False,
                     "podcastRole": False, "streamRole": True, "jukeboxRole": False,
                     "shareRole": False, "videoConversionRole": False}
                ]
            }
        }
        set_json_response(mock_response, make_response(users))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_users()
        assert len(result) == 1
        assert isinstance(result[0], User)

    @pytest.mark.asyncio
    async def test_update_user(self, conn, mock_session, mock_response):
        """Test update_user."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.update_user(
            username="user1",
            email="newemail@example.com",
            max_bit_rate=320
        )
        assert result is True


# ============================================================================
# MEDIA RETRIEVAL METHODS
# ============================================================================

class TestMediaRetrieval:
    """Tests for getAlbum, getArtist, getSong, etc."""

    @pytest.mark.asyncio
    async def test_get_album(self, conn, mock_session, mock_response):
        """Test get_album."""
        album = {
            "album": {
                "id": "album-1",
                "name": "Album Name",
                "songCount": 10,
                "duration": 3600,
                "created": "2024-01-01T00:00:00",
                "song": [{"id": "s1", "isDir": False, "title": "Track 1"}]
            }
        }
        set_json_response(mock_response, make_response(album))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_album("album-1")
        assert isinstance(result, AlbumID3)
        assert result.name == "Album Name"

    @pytest.mark.asyncio
    async def test_get_album_info(self, conn, mock_session, mock_response):
        """Test get_album_info."""
        info = {
            "albumInfo": {
                "notes": "Great album",
                "musicBrainzId": "mbid-123"
            }
        }
        set_json_response(mock_response, make_response(info))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_album_info("album-1")
        assert isinstance(result, AlbumInfo)
        assert result.notes == "Great album"

    @pytest.mark.asyncio
    async def test_get_album_info2(self, conn, mock_session, mock_response):
        """Test get_album_info2."""
        info = {
            "albumInfo": {
                "notes": "Great album v2"
            }
        }
        set_json_response(mock_response, make_response(info))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_album_info2("album-1")
        assert isinstance(result, AlbumInfo)

    @pytest.mark.asyncio
    async def test_get_artist(self, conn, mock_session, mock_response):
        """Test get_artist."""
        artist = {
            "artist": {
                "id": "artist-1",
                "name": "Artist Name",
                "album": [{"id": "alb-1", "name": "Album 1", "songCount": 5,
                          "duration": 1800, "created": "2024-01-01T00:00:00"}]
            }
        }
        set_json_response(mock_response, make_response(artist))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_artist("artist-1")
        assert isinstance(result, ArtistWithAlbumsID3)
        assert result.name == "Artist Name"
        assert len(result.album) == 1

    @pytest.mark.asyncio
    async def test_get_artists(self, conn, mock_session, mock_response):
        """Test get_artists."""
        artists = {
            "artists": {
                "ignoredArticles": "The El La",
                "index": [{"name": "A", "artist": [{"id": "a1", "name": "Artist A"}]}]
            }
        }
        set_json_response(mock_response, make_response(artists))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_artists()
        assert isinstance(result, Artists)

    @pytest.mark.asyncio
    async def test_get_song(self, conn, mock_session, mock_response):
        """Test get_song."""
        song = {
            "song": {
                "id": "song-1",
                "isDir": False,
                "title": "Song Title"
            }
        }
        set_json_response(mock_response, make_response(song))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_song("song-1")
        assert isinstance(result, Child)
        assert result.title == "Song Title"


# ============================================================================
# ALBUM/SONG LIST METHODS
# ============================================================================

class TestAlbumSongLists:
    """Tests for getAlbumList, getRandomSongs, etc."""

    @pytest.mark.asyncio
    async def test_get_album_list_empty(self, conn, mock_session, mock_response):
        """Test get_album_list with empty result."""
        set_json_response(mock_response, make_response({"albumList": {}}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_album_list("newest")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_album_list_with_results(self, conn, mock_session, mock_response):
        """Test get_album_list with albums."""
        albums = {
            "albumList": {
                "album": [
                    {"id": "alb-1", "name": "Album 1", "songCount": 5,
                     "duration": 1800, "created": "2024-01-01T00:00:00"}
                ]
            }
        }
        set_json_response(mock_response, make_response(albums))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_album_list("newest", size=10)
        assert len(result) == 1
        assert isinstance(result[0], Album)

    @pytest.mark.asyncio
    async def test_get_album_list2_empty(self, conn, mock_session, mock_response):
        """Test get_album_list2."""
        albums = {
            "albumList2": {
                "album": None
            }
        }
        set_json_response(mock_response, make_response(albums))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_album_list2("frequent")
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_album_list2(self, conn, mock_session, mock_response):
        """Test get_album_list2."""
        albums = {
            "albumList2": {
                "album": [
                    {"id": "alb-1", "name": "Album 1", "songCount": 5,
                     "duration": 1800, "created": "2024-01-01T00:00:00"}
                ]
            }
        }
        set_json_response(mock_response, make_response(albums))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_album_list2("frequent")
        assert len(result) == 1
        assert isinstance(result[0], AlbumID3)

    @pytest.mark.asyncio
    async def test_get_album_list2_with_music_folder(
        self, conn, mock_session, mock_response
    ):
        """Test get_album_list2 with a music folder filter."""
        albums = {
            "albumList2": {
                "album": [
                    {"id": "alb-1", "name": "Album 1", "songCount": 5,
                     "duration": 1800, "created": "2024-01-01T00:00:00"}
                ]
            }
        }
        set_json_response(mock_response, make_response(albums))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_album_list2("frequent", music_folder_id=1)
        assert len(result) == 1
        assert isinstance(result[0], AlbumID3)
        data = mock_session.post.call_args.kwargs["data"]
        assert data["musicFolderId"] == "1"

    @pytest.mark.asyncio
    async def test_get_random_songs_empty(self, conn, mock_session, mock_response):
        """Test get_random_songs with empty result."""
        set_json_response(mock_response, make_response({"randomSongs": {}}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_random_songs()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_random_songs_with_results(self, conn, mock_session, mock_response):
        """Test get_random_songs with songs."""
        songs = {
            "randomSongs": {
                "song": [
                    {"id": "s1", "isDir": False, "title": "Random Song 1"}
                ]
            }
        }
        set_json_response(mock_response, make_response(songs))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_random_songs(size=10, genre="Rock")
        assert len(result) == 1
        assert isinstance(result[0], Child)

    @pytest.mark.asyncio
    async def test_get_songs_by_genre_empty(self, conn, mock_session, mock_response):
        """Test get_songs_by_genre."""
        songs = {
            "songsByGenre": {
            }
        }
        set_json_response(mock_response, make_response(songs))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_songs_by_genre("Rock", count=20)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_songs_by_genre(self, conn, mock_session, mock_response):
        """Test get_songs_by_genre."""
        songs = {
            "songsByGenre": {
                "song": [{"id": "sg1", "isDir": False, "title": "Genre Song"}]
            }
        }
        set_json_response(mock_response, make_response(songs))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_songs_by_genre("Rock", count=20)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_similar_songs_empty(self, conn, mock_session, mock_response):
        """Test get_similar_songs."""
        songs = {
            "similarSongs": {
            }
        }
        set_json_response(mock_response, make_response(songs))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_similar_songs("song-1", count=10)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_similar_songs(self, conn, mock_session, mock_response):
        """Test get_similar_songs."""
        songs = {
            "similarSongs": {
                "song": [{"id": "sim1", "isDir": False, "title": "Similar"}]
            }
        }
        set_json_response(mock_response, make_response(songs))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_similar_songs("song-1", count=10)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_similar_songs2_empty(self, conn, mock_session, mock_response):
        """Test get_similar_songs2."""
        songs = {
            "similarSongs2": {
            }
        }
        set_json_response(mock_response, make_response(songs))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_similar_songs2("song-1", count=10)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_similar_songs2(self, conn, mock_session, mock_response):
        """Test get_similar_songs2."""
        songs = {
            "similarSongs2": {
                "song": [{"id": "sim2", "isDir": False, "title": "Similar2"}]
            }
        }
        set_json_response(mock_response, make_response(songs))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_similar_songs2("song-1", count=10)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_top_songs_empty(self, conn, mock_session, mock_response):
        """Test get_top_songs with empty result."""
        set_json_response(mock_response, make_response({"topSongs": {}}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_top_songs("Artist Name")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_top_songs_with_results(self, conn, mock_session, mock_response):
        """Test get_top_songs with songs."""
        songs = {
            "topSongs": {
                "song": [{"id": "top1", "isDir": False, "title": "Top Song"}]
            }
        }
        set_json_response(mock_response, make_response(songs))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_top_songs("Artist Name", count=5)
        assert len(result) == 1


# ============================================================================
# STARRED/SEARCH METHODS
# ============================================================================

class TestStarredSearch:
    """Tests for starred and search methods."""

    @pytest.mark.asyncio
    async def test_get_starred_data(self, conn, mock_session, mock_response):
        """Test get_starred."""
        starred = {
            "starred": {
                "artist": [{"id": "art-1", "name": "Artist"}],
                "album": [{"id": "alb-1", "isDir": False, "title": "Album"}],
                "song": [{"id": "s1", "isDir": False, "title": "Song"}]
            }
        }
        set_json_response(mock_response, make_response(starred))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_starred('id')
        assert isinstance(result, Starred)

    @pytest.mark.asyncio
    async def test_get_starred(self, conn, mock_session, mock_response):
        """Test get_starred."""
        starred = {
            "starred": {
                "artist": [{"id": "art-1", "name": "Artist"}],
                "album": [{"id": "alb-1", "isDir": False, "title": "Album"}],
                "song": [{"id": "s1", "isDir": False, "title": "Song"}]
            }
        }
        set_json_response(mock_response, make_response(starred))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_starred()
        assert isinstance(result, Starred)

    @pytest.mark.asyncio
    async def test_get_starred2_data(self, conn, mock_session, mock_response):
        """Test get_starred2."""
        starred = {
            "starred2": {
                "artist": [{"id": "art2-1", "name": "Artist2"}],
                "album": [{"id": "alb2-1", "name": "Album2", "songCount": 5,
                          "duration": 1800, "created": "2024-01-01T00:00:00"}],
                "song": [{"id": "s2-1", "isDir": False, "title": "Song2"}]
            }
        }
        set_json_response(mock_response, make_response(starred))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_starred2('id')
        assert isinstance(result, Starred2)

    @pytest.mark.asyncio
    async def test_get_starred2(self, conn, mock_session, mock_response):
        """Test get_starred2."""
        starred = {
            "starred2": {
                "artist": [{"id": "art2-1", "name": "Artist2"}],
                "album": [{"id": "alb2-1", "name": "Album2", "songCount": 5,
                          "duration": 1800, "created": "2024-01-01T00:00:00"}],
                "song": [{"id": "s2-1", "isDir": False, "title": "Song2"}]
            }
        }
        set_json_response(mock_response, make_response(starred))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_starred2()
        assert isinstance(result, Starred2)

    @pytest.mark.asyncio
    async def test_star(self, conn, mock_session, mock_response):
        """Test star method."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.star(
            sids=["song-1", "song-2"],
            album_ids=["alb-1"],
            artist_ids=["art-1"]
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_unstar(self, conn, mock_session, mock_response):
        """Test unstar method."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.unstar(sids=["song-1"])
        assert result is True

    @pytest.mark.asyncio
    async def test_set_rating(self, conn, mock_session, mock_response):
        """Test set_rating."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.set_rating("song-1", 5)
        assert result is True

    @pytest.mark.asyncio
    async def test_set_rating_range(self, conn, mock_session, mock_response):
        """Test set_rating."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        with pytest.raises(errors.ArgumentError):
            await conn.set_rating("song-1", 9)

    @pytest.mark.asyncio
    async def test_search2(self, conn, mock_session, mock_response):
        """Test search2."""
        results = {
            "searchResult2": {
                "artist": [{"id": "sa1", "name": "Search Artist"}],
                "album": [{"id": "sal1", "isDir": False, "title": "Search Album"}],
                "song": [{"id": "ss1", "isDir": False, "title": "Search Song"}]
            }
        }
        set_json_response(mock_response, make_response(results))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.search2("query")
        assert isinstance(result, SearchResult2)

    @pytest.mark.asyncio
    async def test_search3(self, conn, mock_session, mock_response):
        """Test search3."""
        results = {
            "searchResult3": {
                "artist": [{"id": "sa3-1", "name": "Artist3"}],
                "album": [{"id": "sal3-1", "name": "Album3", "songCount": 5,
                          "duration": 1800, "created": "2024-01-01T00:00:00"}],
                "song": [{"id": "ss3-1", "isDir": False, "title": "Song3"}]
            }
        }
        set_json_response(mock_response, make_response(results))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.search3("query")
        assert isinstance(result, SearchResult3)


# ============================================================================
# DOWNLOAD/STREAM METHODS
# ============================================================================

class TestDownloadStream:
    """Tests for download, stream methods."""

    @pytest.mark.asyncio
    async def test_download(self, conn, mock_session, mock_binary_response):
        """Test download returns binary response."""
        mock_session.get = AsyncMock(return_value=mock_binary_response)

        # Force use_get for download methods typically use GET
        conn.use_get = True

        result = await conn.download("song-123")
        # Should return the ClientResponse directly for binary data
        assert result is mock_binary_response

    @pytest.mark.asyncio
    async def test_stream(self, conn, mock_session, mock_binary_response):
        """Test stream returns binary response."""
        mock_session.get = AsyncMock(return_value=mock_binary_response)
        conn.use_get = True

        result = await conn.stream("song-123", max_bit_rate=320)
        assert result is mock_binary_response

    @pytest.mark.asyncio
    async def test_stream_with_range(self, conn, mock_session, mock_binary_response):
        """Test stream sends Range header when range parameter is provided."""
        mock_session.get = AsyncMock(return_value=mock_binary_response)
        conn.use_get = True

        await conn.stream("song-123", byte_range="bytes=0-1023")

        call_args = mock_session.get.call_args
        assert call_args.kwargs.get("headers") == {"Range": "bytes=0-1023"}

    @pytest.mark.asyncio
    async def test_stream_without_range(self, conn, mock_session, mock_binary_response):
        """Test stream sends no Range header when range parameter is omitted."""
        mock_session.get = AsyncMock(return_value=mock_binary_response)
        conn.use_get = True

        await conn.stream("song-123")

        call_args = mock_session.get.call_args
        assert call_args.kwargs.get("headers") is None

    def test_get_stream_url_returns_url_and_params(self, conn):
        """Test get_stream_url returns a url and a params dict without network I/O."""
        url, params = conn.get_stream_url("song-123", max_bit_rate=320)

        assert url == "http://localhost:4040/rest/stream.view"
        assert params["id"] == "song-123"
        assert params["maxBitRate"] == "320"

    def test_get_stream_url_no_network_call(self, conn, mock_session):
        """Test get_stream_url makes no request."""
        conn.get_stream_url("song-123")

        mock_session.get.assert_not_called()
        mock_session.post.assert_not_called()

    def test_get_stream_url_booleans_are_lowercase_strings(self, conn):
        """Test bool params serialize as lowercase 'true'/'false', not Python's True/False."""
        _, params = conn.get_stream_url("song-123", estimate_length=True, converted=False)

        assert params["estimateContentLength"] == "true"
        assert params["converted"] == "false"

    def test_get_stream_url_omits_none_params(self, conn):
        """Test optional params that are None are excluded from the dict."""
        _, params = conn.get_stream_url("song-123")

        assert "format" not in params
        assert "timeOffset" not in params
        assert "size" not in params

    def test_get_stream_url_includes_auth_params(self, conn):
        """Test the params dict carries auth credentials rather than embedding them in the url."""
        url, params = conn.get_stream_url("song-123")

        assert "?" not in url
        assert params["u"] == "testuser"
        assert "t" in params
        assert "s" in params

    def test_get_stream_url_api_key_auth(self, mock_session):
        """Test get_stream_url with api_key authentication."""
        with patch('aiohttp.ClientSession', return_value=mock_session):
            c = AsyncConnection(
                base_url="http://localhost",
                username=None,
                password=None,
                api_key="secret-key-123"
            )

        _, params = c.get_stream_url("song-123")
        assert params["apiKey"] == "secret-key-123"
        assert "u" not in params

    def test_get_stream_url_use_views_false(self, conn):
        """Test get_stream_url omits the .view suffix when use_views is False."""
        conn._use_views = False

        url, _ = conn.get_stream_url("song-123")
        assert url.split("?")[0] == "http://localhost:4040/rest/stream"

    def test_get_stream_url_use_get_encodes_params_in_url(self, conn):
        """Test that use_get=True encodes all params into the URL query string."""
        conn._use_get = True

        url, params = conn.get_stream_url("song-123")

        assert params == {}
        assert "?" in url
        assert "id=song-123" in url
        assert "u=testuser" in url

    def test_get_stream_url_use_get_returns_empty_params(self, conn):
        """Test that use_get=True returns an empty params dict."""
        conn._use_get = True

        _, params = conn.get_stream_url("song-123")

        assert params == {}

# ============================================================================
# JUKEBOX METHODS
# ============================================================================

class TestJukebox:
    """Tests for jukeboxControl."""

    @pytest.mark.asyncio
    async def test_jukebox_control_status(self, conn, mock_session, mock_response):
        """Test jukebox_control with status action."""
        status = {
            "jukeboxStatus": {
                "currentIndex": 0,
                "playing": True,
                "gain": 0.8
            }
        }
        set_json_response(mock_response, make_response(status))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.jukebox_control("status")
        assert isinstance(result, JukeboxStatus)
        assert result.playing is True

    @pytest.mark.asyncio
    async def test_jukebox_control_get(self, conn, mock_session, mock_response):
        """Test jukebox_control with get action returns playlist."""
        playlist = {
            "jukeboxPlaylist": {
                "currentIndex": 0,
                "playing": True,
                "gain": 0.8,
                "entry": [{"id": "j1", "isDir": False, "title": "Jukebox Song"}]
            }
        }
        set_json_response(mock_response, make_response(playlist))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.jukebox_control("get")
        assert isinstance(result, JukeboxPlaylist)
        assert result.current_index == 0

    @pytest.mark.asyncio
    async def test_jukebox_control_add_with_sids(self, conn, mock_session, mock_response):
        """Test jukebox_control add requires list parameter."""
        status = {
            "jukeboxStatus": {
                "currentIndex": 1,
                "playing": True,
                "gain": 0.5
            }
        }
        set_json_response(mock_response, make_response(status))
        # Note: _do_request_with_list is used for 'add' action
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.jukebox_control(
            "add",
            sids=["song-1", "song-2"]
        )
        assert isinstance(result, JukeboxStatus)


# ============================================================================
# SCAN/EXTENSION METHODS
# ============================================================================

class TestScanExtensions:
    """Tests for scan status and extensions."""

    @pytest.mark.asyncio
    async def test_get_scan_status(self, conn, mock_session, mock_response):
        """Test get_scan_status."""
        status = {
            "scanStatus": {
                "scanning": False,
                "count": 1000
            }
        }
        set_json_response(mock_response, make_response(status))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_scan_status()
        assert isinstance(result, ScanStatus)
        assert result.scanning is False
        assert result.count == 1000

    @pytest.mark.asyncio
    async def test_start_scan(self, conn, mock_session, mock_response):
        """Test start_scan."""
        status = {
            "scanStatus": {
                "scanning": True,
                "count": 0
            }
        }
        set_json_response(mock_response, make_response(status))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.start_scan()
        assert isinstance(result, ScanStatus)
        assert result.scanning is True
        assert result.count == 0

    @pytest.mark.asyncio
    async def test_get_open_subsonic_extensions(self, conn, mock_session, mock_response):
        """Test get_open_subsonic_extensions."""
        extensions = {
            "openSubsonicExtensions": [
                {"name": "formPost", "versions": [1]}
            ]
        }
        set_json_response(mock_response, make_response(extensions))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_open_subsonic_extensions()
        assert len(result) == 1
        assert isinstance(result[0], OpenSubsonicExtension)
        assert result[0].name == "formPost"

# ============================================================================
# GENRE/MUSIC FOLDER/INDEXES METHODS
# ============================================================================

class TestGenreFoldersIndexes:
    """Tests for genre, music folders, indexes."""

    @pytest.mark.asyncio
    async def test_get_genres_empty(self, conn, mock_session, mock_response):
        """Test get_genres with no genres."""
        set_json_response(mock_response, make_response({"genres": {}}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_genres()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_genres_with_data(self, conn, mock_session, mock_response):
        """Test get_genres with genres."""
        genres = {
            "genres": {
                "genre": [
                    {"value": "Rock", "songCount": 100, "albumCount": 10}
                ]
            }
        }
        set_json_response(mock_response, make_response(genres))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_genres()
        assert len(result) == 1
        assert isinstance(result[0], Genre)
        assert result[0].value == "Rock"

    @pytest.mark.asyncio
    async def test_get_music_folders_empty(self, conn, mock_session, mock_response):
        """Test get_music_folders with empty result."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_music_folders()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_music_folders_with_data(self, conn, mock_session, mock_response):
        """Test get_music_folders with folders."""
        folders = {
            "musicFolders": [
                {"id": 1, "name": "Music"},
                {"id": 2, "name": "Podcasts"}
            ]
        }
        set_json_response(mock_response, make_response(folders))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_music_folders()
        assert len(result) == 2
        assert isinstance(result[0], MusicFolder)

    @pytest.mark.asyncio
    async def test_get_indexes(self, conn, mock_session, mock_response):
        """Test get_indexes."""
        indexes = {
            "indexes": {
                "ignoredArticles": "The El La",
                "lastModified": 1234567890000,
                "index": [{"name": "A"}]
            }
        }
        set_json_response(mock_response, make_response(indexes))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_indexes()
        assert isinstance(result, Indexes)

    @pytest.mark.asyncio
    async def test_get_music_directory(self, conn, mock_session, mock_response):
        """Test get_music_directory."""
        directory = {
            "directory": {
                "id": "dir-1",
                "name": "My Directory"
            }
        }
        set_json_response(mock_response, make_response(directory))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_music_directory("dir-1")
        assert isinstance(result, Directory)


# ============================================================================
# LYRICS METHODS
# ============================================================================

class TestLyrics:
    """Tests for lyrics methods."""

    @pytest.mark.asyncio
    async def test_get_lyrics(self, conn, mock_session, mock_response):
        """Test get_lyrics."""
        lyrics = {
            "lyrics": {
                "value": "These are the lyrics",
                "artist": "Artist Name",
                "title": "Song Title"
            }
        }
        set_json_response(mock_response, make_response(lyrics))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_lyrics("Artist", "Title")
        assert isinstance(result, Lyrics)
        assert result.value == "These are the lyrics"

    @pytest.mark.asyncio
    async def test_get_lyrics_by_song_id_empty(self, conn, mock_session, mock_response):
        """Test get_lyrics_by_song_id with no lyrics."""
        set_json_response(mock_response, make_response({"lyricsList": {}}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_lyrics_by_song_id("song-1")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_lyrics_by_song_id_with_data(self, conn, mock_session, mock_response):
        """Test get_lyrics_by_song_id with lyrics."""
        lyrics = {
            "lyricsList": {
                "structuredLyrics": [{
                    "lang": "en",
                    "synced": True,
                    "line": [{"value": "Line 1", "start": 0.0}]
                }]
            }
        }
        set_json_response(mock_response, make_response(lyrics))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_lyrics_by_song_id("song-1")
        assert len(result) == 1
        assert isinstance(result[0], StructuredLyrics)


# ============================================================================
# NOW PLAYING / SCROBBLE / PLAY QUEUE
# ============================================================================

class TestNowPlayingScrobble:
    """Tests for now playing, scrobble, play queue."""

    @pytest.mark.asyncio
    async def test_get_now_playing_empty(self, conn, mock_session, mock_response):
        """Test get_now_playing with no entries."""
        set_json_response(mock_response, make_response({"nowPlaying": {}}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_now_playing()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_now_playing_with_entries(self, conn, mock_session, mock_response):
        """Test get_now_playing with entries."""
        playing = {
            "nowPlaying": {
                "entry": [{
                    "id": "np1",
                    "isDir": False,
                    "title": "Now Playing",
                    "username": "user1",
                    "minutesAgo": 0,
                    "playerId": 1
                }]
            }
        }
        set_json_response(mock_response, make_response(playing))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_now_playing()
        assert len(result) == 1
        assert isinstance(result[0], NowPlayingEntry)

    @pytest.mark.asyncio
    async def test_scrobble(self, conn, mock_session, mock_response):
        """Test scrobble."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.scrobble("song-1", submission=True, listen_time=1234567890)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_play_queue(self, conn, mock_session, mock_response):
        """Test get_play_queue."""
        queue = {
            "playQueue": {
                "username": "user1",
                "changed": "2024-01-01T00:00:00",
                "changedBy": "client1",
                "entry": [{"id": "pq1", "isDir": False, "title": "Queued"}]
            }
        }
        set_json_response(mock_response, make_response(queue))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_play_queue()
        assert isinstance(result, PlayQueue)

    @pytest.mark.asyncio
    async def test_save_play_queue(self, conn, mock_session, mock_response):
        """Test save_play_queue."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.save_play_queue(["song-1", "song-2"], current="song-1", position=5000)
        assert result is True


# ============================================================================
# VIDEO METHODS
# ============================================================================

class TestVideo:
    """Tests for video methods."""

    @pytest.mark.asyncio
    async def test_get_videos(self, conn, mock_session, mock_response):
        """Test get_videos returns dict."""
        videos = {"videos": {"video": []}}
        set_json_response(mock_response, make_response(videos))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_videos()
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_video_info(self, conn, mock_session, mock_response):
        """Test get_video_info."""
        info = {"videoInfo": {"id": 1, "captions": []}}
        set_json_response(mock_response, make_response(info))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_video_info(123)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_captions(self, conn, mock_session, mock_response):
        """Test get_captions."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_captions(123, fmt="srt")
        assert isinstance(result, dict)


# ============================================================================
# ARTIST INFO METHODS
# ============================================================================

class TestArtistInfo:
    """Tests for artist info methods."""

    @pytest.mark.asyncio
    async def test_get_artist_info(self, conn, mock_session, mock_response):
        """Test get_artist_info."""
        info = {
            "artistInfo": {
                "biography": "Artist biography text",
                "musicBrainzId": "mbid-abc"
            }
        }
        set_json_response(mock_response, make_response(info))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_artist_info("artist-1")
        assert isinstance(result, ArtistInfo)
        assert result.biography == "Artist biography text"

    @pytest.mark.asyncio
    async def test_get_artist_info2(self, conn, mock_session, mock_response):
        """Test get_artist_info2."""
        info = {
            "artistInfo2": {
                "biography": "Artist bio v2",
                "similarArtist": [{"id": "sim1", "name": "Similar"}]
            }
        }
        set_json_response(mock_response, make_response(info))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_artist_info2("artist-1")
        assert isinstance(result, ArtistInfo2)


# ============================================================================
# DEPRECATED METHODS
# ============================================================================

class TestDeprecated:
    """Tests for deprecated methods."""

    def test_search_deprecated(self, conn):
        """Test search raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            conn.search()


# ============================================================================
# INTERNAL HELPER TESTS
# ============================================================================

class TestInternalHelpers:
    """Edge case tests for internal methods."""

    def test_get_query_dict_filters_none(self, conn):
        """Test _get_query_dict removes None values."""
        d = {"a": 1, "b": None, "c": "value"}
        result = conn._get_query_dict(d)
        assert result == {"a": 1, "c": "value"}

    def test_ts2milli_edge_cases(self, conn):
        """Test timestamp conversion edge cases."""
        assert conn._ts2milli(0) == 0
        assert conn._ts2milli(1.5) == 1500
        assert conn._ts2milli(None) is None

    def test_hex_enc_empty(self, conn):
        """Test hex encoding with empty string."""
        assert conn._hex_enc("") == ""

    def test_hex_enc_special_chars(self, conn):
        """Test hex encoding with special characters."""
        # "A" = 0x41
        assert conn._hex_enc("A") == "41"
        # " test" = space(0x20) + t(0x74) + e(0x65) + s(0x73) + t(0x74)
        assert conn._hex_enc(" test") == "2074657374"


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Tests for error code mapping and raising."""

    @pytest.mark.asyncio
    async def test_error_40_generates_sonic_error(self, conn, mock_session, mock_response):
        """Test error code 40 raises CredentialError."""
        error_response = {
            "subsonic-response": {
                "status": "failed",
                "version": API_VERSION,
                "error": {"code": 40, "message": "Wrong username or password"}
            }
        }
        set_json_response(mock_response, error_response)
        mock_session.post = AsyncMock(return_value=mock_response)

        with pytest.raises(errors.CredentialError):
            await conn.ping()

    @pytest.mark.asyncio
    async def test_error_70_generates_not_found(self, conn, mock_session, mock_response):
        """Test error code 70 for data not found."""
        error_response = {
            "subsonic-response": {
                "status": "failed",
                "version": API_VERSION,
                "error": {"code": 70, "message": "Data not found"}
            }
        }
        set_json_response(mock_response, error_response)
        mock_session.post = AsyncMock(return_value=mock_response)

        with pytest.raises(errors.SonicError):
            await conn.ping()


# ============================================================================
# GET/POST METHOD SELECTION
# ============================================================================

class TestRequestMethodSelection:
    """Tests for GET vs POST selection."""

    @pytest.mark.asyncio
    async def test_uses_post_by_default(self, conn, mock_session, mock_response):
        """Test that POST is used by default."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.get = AsyncMock(return_value=mock_response)

        await conn.ping()

        mock_session.post.assert_called_once()
        mock_session.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_uses_get_when_configured(self, conn, mock_session, mock_response):
        """Test that GET is used when use_get=True."""
        conn.use_get = True
        set_json_response(mock_response, make_response({}))
        mock_session.get = AsyncMock(return_value=mock_response)

        await conn.ping()

        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_view_extension(self, conn, mock_session, mock_response):
        """Test that .view extension is added."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        await conn.ping()

        # Check URL contains .view
        assert "ping.view" in str(mock_session.post.call_args)


# ============================================================================
# CONSTRUCTOR EDGE CASES
# ============================================================================

class TestConstructorEdgeCases:
    """Additional edge case tests for constructor."""

    def test_server_path_edge_cases(self, mock_session):
        """Test various server_path inputs."""
        with patch('aiohttp.ClientSession', return_value=mock_session):
            # Empty path
            c1 = AsyncConnection("http://localhost", "u", "p", server_path="")
            assert c1.server_path == "rest"

            # Path with trailing slash
            c2 = AsyncConnection("http://localhost", "u", "p", server_path="/api/")
            assert c2.server_path == "api/rest"

            # Path without leading slash
            c3 = AsyncConnection("http://localhost", "u", "p", server_path="api")
            assert c3.server_path == "api/rest"

    def test_url_without_protocol(self, mock_session):
        """Test URL without protocol specification."""
        with patch('aiohttp.ClientSession', return_value=mock_session):
            c = AsyncConnection("localhost", "u", "p")
            assert c._hostname == "localhost"
            # base_url preserves the input
            assert c.base_url == "localhost"


# ============================================================================
# EDGE CASE: EMPTY RESPONSES AND MISSING FIELDS
# ============================================================================

class TestEmptyAndMissingResponses:
    """Tests for handling empty or minimal API responses."""

    @pytest.mark.asyncio
    async def test_get_album_list_no_album_key(self, conn, mock_session, mock_response):
        """Test get_album_list when 'album' key is missing."""
        set_json_response(mock_response, make_response({"albumList": {"something": "else"}}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_album_list("random")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_genres_no_genre_key(self, conn, mock_session, mock_response):
        """Test get_genres when 'genre' key is missing."""
        set_json_response(mock_response, make_response({"genres": {}}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_genres()
        assert result == []


# ============================================================================
# PLAY QUEUE BY INDEX
# ============================================================================

class TestPlayQueueByIndex:
    """Tests for index-based play queue methods."""

    @pytest.mark.asyncio
    async def test_get_play_queue_by_index(self, conn, mock_session, mock_response):
        """Test get_play_queue_by_index returns a PlayQueueByIndex."""
        data = {
            "playQueueByIndex": {
                "username": "testuser",
                "changed": "2024-01-01T00:00:00Z",
                "changedBy": "test-app",
                "currentIndex": 1,
                "position": 30000,
                "entry": [
                    {"id": "s1", "parent": "a1", "title": "Song 1", "isDir": False},
                    {"id": "s2", "parent": "a1", "title": "Song 2", "isDir": False},
                ],
            }
        }
        set_json_response(mock_response, make_response(data))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_play_queue_by_index()
        assert isinstance(result, PlayQueueByIndex)
        assert result.username == "testuser"
        assert result.current_index == 1
        assert result.position == 30000
        assert len(result.entry) == 2

    @pytest.mark.asyncio
    async def test_save_play_queue_by_index(self, conn, mock_session, mock_response):
        """Test save_play_queue_by_index with songs."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.save_play_queue_by_index(
            ids=["s1", "s2", "s3"], current_index=0, position=0
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_save_play_queue_by_index_clears_when_empty(
        self, conn, mock_session, mock_response
    ):
        """Test save_play_queue_by_index with no args clears the queue."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.save_play_queue_by_index()
        assert result is True
        mock_session.post.assert_called_once()
        call_kwargs = mock_session.post.call_args[1]
        # No 'id' param should be in the data when clearing
        assert "id" not in call_kwargs.get("data", {})


# ============================================================================
# SONIC SIMILARITY
# ============================================================================

class TestSonicSimilarity:
    """Tests for audio-similarity methods."""

    @pytest.mark.asyncio
    async def test_get_sonic_similar_tracks(self, conn, mock_session, mock_response):
        """Test get_sonic_similar_tracks returns SonicMatch list."""
        data = {
            "sonicMatch": [
                {
                    "entry": {"id": "s1", "parent": "a1", "title": "Close Song", "isDir": False},
                    "similarity": 0.92,
                },
                {
                    "entry": {"id": "s2", "parent": "a1", "title": "Similar Song", "isDir": False},
                    "similarity": 0.75,
                },
            ]
        }
        set_json_response(mock_response, make_response(data))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_sonic_similar_tracks("song-123", count=2)
        assert len(result) == 2
        assert isinstance(result[0], SonicMatch)
        assert result[0].similarity == 0.92
        assert result[0].entry.title == "Close Song"

    @pytest.mark.asyncio
    async def test_get_sonic_similar_tracks_empty(self, conn, mock_session, mock_response):
        """Test get_sonic_similar_tracks returns empty list when no matches."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_sonic_similar_tracks("song-123")
        assert result == []

    @pytest.mark.asyncio
    async def test_find_sonic_path(self, conn, mock_session, mock_response):
        """Test find_sonic_path returns ordered SonicMatch list."""
        data = {
            "sonicMatch": [
                {
                    "entry": {"id": "s1", "parent": "a1", "title": "Start Song", "isDir": False},
                    "similarity": 1.0,
                },
                {
                    "entry": {"id": "s2", "parent": "a1", "title": "Bridge Song", "isDir": False},
                    "similarity": 0.6,
                },
                {
                    "entry": {"id": "s3", "parent": "a1", "title": "End Song", "isDir": False},
                    "similarity": 0.3,
                },
            ]
        }
        set_json_response(mock_response, make_response(data))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.find_sonic_path("s1", "s3", count=25)
        assert len(result) == 3
        assert isinstance(result[0], SonicMatch)
        assert result[0].similarity == 1.0
        assert result[2].entry.id == "s3"

    @pytest.mark.asyncio
    async def test_find_sonic_path_empty(self, conn, mock_session, mock_response):
        """Test find_sonic_path returns empty list when no path found."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.find_sonic_path("s1", "s2")
        assert result == []


# ============================================================================
# TRANSCODING
# ============================================================================

class TestTranscoding:
    """Tests for getTranscodeDecision and getTranscodeStream."""

    @pytest.mark.asyncio
    async def test_get_transcode_decision_direct_play(
        self, conn, mock_session, mock_response
    ):
        """Test get_transcode_decision returns TranscodeDecision."""
        data = {
            "transcodeDecision": {
                "canDirectPlay": True,
                "canTranscode": False,
            }
        }
        set_json_response(mock_response, make_response(data))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_transcode_decision(
            "song-123", "song", {"supportedCodecs": ["flac", "mp3"]}
        )
        assert isinstance(result, TranscodeDecision)
        assert result.can_direct_play is True
        assert result.can_transcode is False

    @pytest.mark.asyncio
    async def test_get_transcode_decision_sends_json_body(
        self, conn, mock_session, mock_response
    ):
        """Test get_transcode_decision sends client_info as JSON body."""
        data = {"transcodeDecision": {"canDirectPlay": False, "canTranscode": True}}
        set_json_response(mock_response, make_response(data))
        mock_session.post = AsyncMock(return_value=mock_response)

        client_info = {"supportedCodecs": ["mp3"]}
        await conn.get_transcode_decision("song-123", "song", client_info)

        call_kwargs = mock_session.post.call_args[1]
        assert call_kwargs.get("json") == client_info
        assert "data" not in call_kwargs

    @pytest.mark.asyncio
    async def test_get_transcode_decision_with_stream_details(
        self, conn, mock_session, mock_response
    ):
        """Test get_transcode_decision parses nested StreamDetails."""
        data = {
            "transcodeDecision": {
                "canDirectPlay": False,
                "canTranscode": True,
                "transcodeParams": "abc123",
                "sourceStream": {
                    "protocol": "http",
                    "container": "flac",
                    "codec": "flac",
                    "audioBitrate": 1000,
                },
                "transcodeStream": {
                    "protocol": "http",
                    "container": "mp3",
                    "codec": "mp3",
                    "audioBitrate": 320,
                },
            }
        }
        set_json_response(mock_response, make_response(data))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_transcode_decision("song-123", "song", {})
        assert result.transcode_params == "abc123"
        assert result.source_stream.codec == "flac"
        assert result.transcode_stream.audio_bitrate == 320

    @pytest.mark.asyncio
    async def test_get_transcode_stream(
        self, conn, mock_session, mock_binary_response
    ):
        """Test get_transcode_stream returns binary response."""
        mock_session.post = AsyncMock(return_value=mock_binary_response)

        result = await conn.get_transcode_stream("song-123", "song", "abc123")
        assert result is mock_binary_response


# ============================================================================
# REPORT PLAYBACK
# ============================================================================

class TestReportPlayback:
    """Tests for reportPlayback."""

    @pytest.mark.asyncio
    async def test_report_playback(self, conn, mock_session, mock_response):
        """Test report_playback returns True on success."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.report_playback(
            "song-123", "song", 45000, "playing"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_report_playback_sends_required_params(
        self, conn, mock_session, mock_response
    ):
        """Test report_playback sends all required parameters."""
        set_json_response(mock_response, make_response({}))
        mock_session.post = AsyncMock(return_value=mock_response)

        await conn.report_playback("song-123", "song", 45000, "paused",
                                   playback_rate=1.5, ignore_scrobble=True)

        call_kwargs = mock_session.post.call_args[1]
        data = call_kwargs.get("data", {})
        assert data["mediaId"] == "song-123"
        assert data["mediaType"] == "song"
        assert data["positionMs"] == "45000"
        assert data["state"] == "paused"
        assert data["playbackRate"] == "1.5"
        assert data["ignoreScrobble"] == "true"


# ============================================================================
# PODCAST EPISODE
# ============================================================================

class TestGetPodcastEpisode:
    """Tests for getPodcastEpisode."""

    @pytest.mark.asyncio
    async def test_get_podcast_episode(self, conn, mock_session, mock_response):
        """Test get_podcast_episode returns a PodcastEpisode."""
        data = {
            "podcastEpisode": {
                "id": "ep-1",
                "channelId": "pod-1",
                "isDir": False,
                "title": "Episode One",
                "status": "completed",
            }
        }
        set_json_response(mock_response, make_response(data))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.get_podcast_episode("ep-1")
        assert isinstance(result, PodcastEpisode)
        assert result.id == "ep-1"
        assert result.title == "Episode One"


# ============================================================================
# TOKEN INFO
# ============================================================================

class TestTokenInfo:
    """Tests for tokenInfo."""

    @pytest.mark.asyncio
    async def test_token_info(self, conn, mock_session, mock_response):
        """Test token_info returns a TokenInfo."""
        data = {"tokenInfo": {"username": "testuser"}}
        set_json_response(mock_response, make_response(data))
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await conn.token_info()
        assert isinstance(result, TokenInfo)
        assert result.username == "testuser"


# Mark all async tests
#pytestmark = pytest.mark.asyncio(loop_scope="function")
