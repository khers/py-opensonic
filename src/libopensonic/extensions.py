"""
This file is part of py-opensonic.

py-opensonic is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

py-opensonic is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with py-opensonic.  If not, see <http://www.gnu.org/licenses/>
"""


class Extensions:
    """Extension name constants as returned by get_open_subsonic_extensions().

    Use these to check server capability rather than comparing against
    magic strings:

        exts = {e.name for e in await conn.get_open_subsonic_extensions()}
        if Extensions.PLAYBACK_REPORT in exts:
            await conn.report_playback(...)

    Docs: https://opensubsonic.github.io/docs/extensions/
    """

    API_KEY_AUTHENTICATION = "apiKeyAuthentication"
    """Enables API-key-only auth and the token_info() endpoint."""

    FORM_POST = "formPost"
    """Server accepts credentials in the POST body instead of the URL."""

    GET_PODCAST_EPISODE = "getPodcastEpisode"
    """Enables get_podcast_episode(), and adds id support to
    download_podcast_episode() and delete_podcast_episode()."""

    INDEX_BASED_QUEUE = "indexBasedQueue"
    """Enables get_play_queue_by_index() and save_play_queue_by_index()."""

    PLAYBACK_REPORT = "playbackReport"
    """Enables report_playback()."""

    SONG_LYRICS = "songLyrics"
    """Enables get_lyrics_by_song_id() and adds structured-lyrics fields."""

    SONIC_SIMILARITY = "sonicSimilarity"
    """Enables get_sonic_similar_tracks() and find_sonic_path()."""

    TOP_SONGS_BY_ARTIST_ID = "topSongsByArtistId"
    """Enables passing an artist ID (instead of name) to get_top_songs()."""

    TRANSCODE_OFFSET = "transcodeOffset"
    """Enables the offset parameter on get_transcode_stream()."""

    TRANSCODING = "transcoding"
    """Enables get_transcode_decision() and get_transcode_stream()."""
