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

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Annotated
from mashumaro.config import BaseConfig
from mashumaro.mixins.json import DataClassJSONMixin
from mashumaro.types import Alias

class DataItem(DataClassJSONMixin):
    """ Base class for all Subsonic objects. """
    class Config(BaseConfig):
        """ Configuratoin for mashumaro. """
        omit_default = True
        forbid_extra_keys = False
        serialize_by_alias = True


@dataclass(kw_only=True)
class AlbumID3(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/albumid3/
    """
    id: str
    name: str
    song_count: Annotated[int, Alias("songCount")]
    duration: int
    created: str
    version: str | None = None
    artist: str | None = None
    artist_id: Annotated[str | None, Alias("artistId")] = None
    cover_art: Annotated[str | None, Alias("coverArt")] = None
    play_count: Annotated[int | None, Alias("playCount")] = None
    starred: str | None = None
    year: int | None = None
    genre: str | None = None
    played: str | None = None
    user_rating: Annotated[int | None, Alias("userRating")] = None
    record_labels: Annotated[list[RecordLabel] | None, Alias("recordLabels")] = None
    music_brainz_id: Annotated[str | None, Alias("musicBrainzId")] = None
    genres: list[ItemGenre] | None = None
    artists: list[ArtistID3] | None = None
    display_artist: Annotated[str | None, Alias("displayArtist")] = None
    release_types: Annotated[list[str] | None, Alias("releaseTypes")] = None
    moods: list[str] | None = None
    sort_name: Annotated[str | None, Alias("sortName")] = None
    original_release_date: Annotated[ItemDate | None, Alias("originalReleaseDate")] = None
    release_date: Annotated[ItemDate | None, Alias("releaseDate")] = None
    is_compilation: Annotated[bool | None, Alias("isCompilation")] = None
    explicit_status: Annotated[str | None, Alias("explicitStatus")] = None
    disc_titles: Annotated[list[DiscTitle] | None, Alias("discTitles")] = None


@dataclass(kw_only=True)
class AlbumID3WithSongs(AlbumID3):
    """
    https://opensubsonic.github.io/docs/responses/albumid3withsongs/
    """
    song: list[Child] | None = None


@dataclass(kw_only=True)
class Album(AlbumID3):
    """
    https://opensubsonic.github.io/docs/responses/album/
    This object is in the spec for backward compatibilty but, like AtristID3 and Artist,
    there is no difference in the required fields.
    """


@dataclass(kw_only=True)
class AlbumInfo(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/albuminfo/
    """
    notes: str | None = None
    music_brainz_id: Annotated[str | None, Alias("musicBrainzId")] = None
    last_fm_url: Annotated[str | None, Alias("lastFmUrl")] = None
    small_image_url: Annotated[str | None, Alias("smallImageUrl")] = None
    medium_image_url: Annotated[str | None, Alias("mediumImageUrl")] = None
    large_image_url: Annotated[str | None, Alias("largeImageUrl")] = None


@dataclass(kw_only=True)
class ArtistID3(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/artistid3/
    """
    id: str
    name: str
    album_count: Annotated[int | None, Alias("albumCount")] = None
    cover_art: Annotated[str | None, Alias("coverArt")] = None
    artist_image_url: Annotated[str | None, Alias("artistImageUrl")] = None
    starred: str | None = None
    music_brainz_id: Annotated[str | None, Alias("musicBrainzId")] = None
    sort_name: Annotated[str | None, Alias("sortName")] = None
    roles: list[str] | None = None
    disambiguation: str | None = None


@dataclass(kw_only=True)
class ArtistWithAlbumsID3(ArtistID3):
    """
    https://opensubsonic.github.io/docs/responses/artistwithalbumsid3/
    """
    album: list[AlbumID3] | None = None


@dataclass(kw_only=True)
class Artist(ArtistID3):
    """
    https://opensubsonic.github.io/docs/responses/artist/
    """
    user_rating: Annotated[int | None, Alias("userRating")] = None
    average_rating: Annotated[float | None, Alias("averageRating")] = None


@dataclass(kw_only=True)
class ArtistInfo(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/artistinfo/
    """
    biography: str | None = None
    music_brainz_id: Annotated[str | None, Alias("musicBrainzId")] = None
    last_fm_url: Annotated[str | None, Alias("lastFmUrl")] = None
    small_image_url: Annotated[str | None, Alias("smallImageUrl")] = None
    medium_image_url: Annotated[str | None, Alias("mediumImageUrl")] = None
    large_image_url: Annotated[str | None, Alias("largeImageUrl")] = None
    similar_artist: Annotated[list[Artist] | None, Alias("similarArtist")] = None


@dataclass(kw_only=True)
class ArtistInfo2(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/artistinfo2/
    """
    biography: str | None = None
    music_brainz_id: Annotated[str | None, Alias("musicBrainzId")] = None
    last_fm_url: Annotated[str | None, Alias("lastFmUrl")] = None
    small_image_url: Annotated[str | None, Alias("smallImageUrl")] = None
    medium_image_url: Annotated[str | None, Alias("mediumImageUrl")] = None
    large_image_url: Annotated[str | None, Alias("largeImageUrl")] = None
    similar_artist: Annotated[list[ArtistID3] | None, Alias("similarArtist")] = None


@dataclass(kw_only=True)
class Artists(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/indexes/
    """
    ignored_articles: Annotated[str, Alias("ignoredArticles")]
    shortcut: list[Artist] | None = None
    child: list[Child] | None = None
    index: list[IndexID3] | None = None


@dataclass(kw_only=True)
class Bookmark(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/bookmark/
    """
    position: int
    username: str
    created: str
    changed: str
    entry: Child
    comment: str | None = None


@dataclass(kw_only=True)
class ChatMessage(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/chatmessage/
    """
    username: str
    time: int
    message: str


@dataclass(kw_only=True)
class Movement(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/movement/
    """
    name: str
    number: int | None = None
    count: int | None = None


@dataclass(kw_only=True)
class Work(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/work/
    """
    name: str
    music_brainz_id: Annotated[str | None, Alias("musicBrainzId")] = None


@dataclass(kw_only=True)
class Child(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/child/
    """
    id: str
    is_dir: Annotated[bool, Alias("isDir")]
    title: str
    parent: str | None = None
    album: str | None = None
    artist: str | None = None
    track: int | None = None
    year: int | None = None
    genre: str | None = None
    cover_art: Annotated[str | None, Alias("coverArt")] = None
    size: int | None = None
    content_type: Annotated[str | None, Alias("contentType")]= None
    suffix: str | None = None
    transcoded_content_type: Annotated[str | None, Alias("transcodedContentType")] = None
    transcoded_suffix: Annotated[str | None, Alias("transcodedSuffix")] = None
    duration: int | None = None
    bit_rate: Annotated[int | None, Alias("bitRate")] = None
    bit_depth: Annotated[int | None, Alias("bitDepth")] = None
    sampling_rate: Annotated[int | None, Alias("samplingRate")] = None
    channel_count: Annotated[int | None, Alias("channelCount")] = None
    path: str | None = None
    is_video: Annotated[bool | None, Alias("isVideo")] = None
    user_rating: Annotated[int | None, Alias("userRating")] = None
    average_rating: Annotated[float | None, Alias("averageRating")] = None
    play_count: Annotated[int | None, Alias("playCount")] = None
    disc_number: Annotated[int | None, Alias("discNumber")] = None
    created: str | None = None
    starred: str | None = None
    album_id: Annotated[str | None, Alias("albumId")] = None
    artist_id: Annotated[str | None, Alias("artistId")] = None
    type: str | None = None
    media_type: Annotated[str | None, Alias("mediaType")] = None
    bookmark_position: Annotated[int | None, Alias("bookmarkPosition")] = None
    original_width: Annotated[int | None, Alias("originalWidth")] = None
    original_height: Annotated[int | None, Alias("originalHeight")] = None
    played: str | None = None
    bpm: int | None = None
    comment: str | None = None
    sort_name: Annotated[str | None, Alias("sortName")] = None
    music_brainz_id: Annotated[str | None, Alias("musicBrainzId")] = None
    genres: list[ItemGenre] | None = None
    artists: list[ArtistID3] | None = None
    album_artists: Annotated[list[ArtistID3] | None, Alias("albumArtists")] = None
    display_artist: Annotated[str | None, Alias("displayArtist")] = None
    display_album_artist: Annotated[str | None, Alias("displayAlbumArtist")] = None
    contributors: list[Contributor] | None = None
    display_composer: Annotated[str | None, Alias("displayComposer")] = None
    moods: list[str] | None = None
    replay_gain: Annotated[ReplayGain | None, Alias("replayGain")] = None
    explicit_status: Annotated[str | None, Alias("explicitStatus")] = None
    isrc: list[str] | None = None
    works: list[Work] | None = None
    movements: list[Movement] | None = None
    groupings: list[str] | None = None


@dataclass(kw_only=True)
class Contributor(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/contributor/
    """
    role: str
    artist: ArtistID3
    sub_role: Annotated[str | None, Alias("subRole")] = None


@dataclass(kw_only=True)
class Directory(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/directory/
    """
    id: str
    name: str
    parent: str | None = None
    starred: str | None = None
    user_rating: Annotated[int | None, Alias("userRating")] = None
    average_rating: Annotated[float | None, Alias("averageRating")] = None
    play_count: Annotated[int | None, Alias("playCount")] = None
    child: list[Child] | None = None


@dataclass(kw_only=True)
class DiscTitle(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/disctitle/
    """
    disc: int
    title: str
    cover_art: Annotated[str | None, Alias("coverArt")] = None


@dataclass(kw_only=True)
class Error(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/error/
    """
    code: int
    message: str | None = None
    help_url: Annotated[str | None, Alias("helpUrl")] = None


@dataclass(kw_only=True)
class Genre(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/genre/
    """
    value: str
    song_count: Annotated[int, Alias("songCount")]
    album_count: Annotated[int, Alias("albumCount")]


@dataclass(kw_only=True)
class Index(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/index_/
    """
    name: str
    artist: list[Artist] | None = None


@dataclass(kw_only=True)
class Indexes(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/indexes/
    """
    ignored_articles: Annotated[str, Alias("ignoredArticles")]
    last_modified: Annotated[int, Alias("lastModified")]
    shortcut: list[Artist] | None = None
    child: list[Child] | None = None
    index: list[Index] | None = None


@dataclass(kw_only=True)
class IndexID3(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/indexid3/
    """
    name: str
    artist: list[ArtistID3] | None = None


@dataclass(kw_only=True)
class InternetRadioStation(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/internetradiostation/
    """
    id: str
    name: str
    stream_url: Annotated[str, Alias("streamUrl")]
    home_page_url: Annotated[str | None, Alias("homePageUrl")] = None
    cover_art: Annotated[str | None, Alias("coverArt")] = None


@dataclass(kw_only=True)
class ItemDate(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/itemdate/
    """
    year: int | None = None
    month: int | None = None
    day: int | None = None


@dataclass(kw_only=True)
class ItemGenre(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/itemgenre/
    """
    name: str


@dataclass(kw_only=True)
class JukeboxPlaylist(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/jukeboxplaylist/
    """
    current_index: Annotated[int, Alias("currentIndex")]
    playing: bool
    gain: float
    position: int | None = None
    entry: list[Child] | None = None


@dataclass(kw_only=True)
class JukeboxStatus(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/jukeboxstatus/
    """
    current_index: Annotated[int, Alias("currentIndex")]
    playing: bool
    gain: float
    position: int | None = None


@dataclass(kw_only=True)
class License(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/license/
    """
    valid: bool
    email: str | None = None
    license_expires: Annotated[str | None, Alias("licenseExpires")] = None
    trial_expires: Annotated[str | None, Alias("trialExpires")] = None


@dataclass(kw_only=True)
class Line(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/line/
    """
    value: str
    start: float | None = None
    end: float | None = None


@dataclass(kw_only=True)
class Lyrics(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/lyrics/
    """
    value: str
    artist: str | None = None
    title: str | None = None


@dataclass(kw_only=True)
class MusicFolder(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/musicfolder/
    """
    id: int
    name: str | None = None


@dataclass(kw_only=True)
class NowPlayingEntry(Child):
    """
    https://opensubsonic.github.io/docs/responses/nowplayingentry/
    """
    username: str
    minutes_ago: Annotated[int, Alias("minutesAgo")]
    player_id: Annotated[int, Alias("playerId")]
    player_name: Annotated[str | None, Alias("playerName")] = None
    state: str | None = None
    position_ms: Annotated[int | None, Alias("positionMs")] = None
    playback_rate: Annotated[float | None, Alias("playbackRate")] = None


@dataclass(kw_only=True)
class OpenSubsonicExtension(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/opensubsonicextension/
    """
    name: str
    versions: list[int]


@dataclass(kw_only=True)
class Playlist(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/playlistwithsongs/
    """
    id: str
    name: str
    song_count: Annotated[int, Alias("songCount")]
    duration: int
    created: str
    changed: str
    comment: str | None = None
    owner: str | None = None
    public: bool | None = None
    cover_art: Annotated[str | None, Alias("coverArt")] = None
    allowed_user: Annotated[list[str] | None, Alias("allowedUser")] = None
    readonly: bool | None = None
    valid_until: Annotated[str | None, Alias("validUntil")] = None
    entry: list[Child] | None = None


@dataclass(kw_only=True)
class PlayQueue(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/playqueue/
    """
    username: str
    changed: str
    changed_by: Annotated[str, Alias("changedBy")]
    current: str | None = None
    position: int | None = None
    entry: list[Child] | None = None


@dataclass(kw_only=True)
class PlayQueueByIndex(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/playqueuebyindex/
    """
    username: str
    changed: str
    changed_by: Annotated[str, Alias("changedBy")]
    current_index: Annotated[int | None, Alias("currentIndex")] = None
    position: int | None = None
    entry: list[Child] | None = None


@dataclass(kw_only=True)
class PodcastChannel(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/podcastchannel/
    """
    id: str
    url: str
    status: PodcastStatus
    title: str | None = None
    description: str | None = None
    cover_art: Annotated[str | None, Alias("coverArt")] = None
    original_image_url: Annotated[str | None, Alias("originalImageUrl")] = None
    error_message: Annotated[str | None, Alias("errorMessage")] = None
    episode: list[PodcastEpisode] | None = None

@dataclass(kw_only=True)
class PodcastEpisode(Child):
    """
    https://opensubsonic.github.io/docs/responses/podcastepisode/
    """
    channel_id: Annotated[str, Alias("channelId")]
    status: PodcastStatus
    stream_id: Annotated[str | None, Alias("streamId")] = None
    description: str | None = None
    publish_date: Annotated[str | None, Alias("publishDate")] = None

class PodcastStatus(Enum):
    """
    https://opensubsonic.github.io/docs/responses/podcaststatus/
    """
    new = "new"
    downloading = "downloading"
    completed = "completed"
    error = "error"
    deleted = "deleted"
    skipped = "skipped"


@dataclass(kw_only=True)
class RecordLabel(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/recordlabel/
    """
    name: str


@dataclass(kw_only=True)
class ReplayGain(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/replaygain/
    """
    track_gain: Annotated[float | None, Alias("trackGain")] = None
    album_gain: Annotated[float | None, Alias("albumGain")] = None
    track_peak: Annotated[float | None, Alias("trackPeak")] = None
    album_peak: Annotated[float | None, Alias("albumPeak")] = None
    base_gain: Annotated[float | None, Alias("baseGain")] = None
    fallback_gain: Annotated[float | None, Alias("fallbackGain")] = None


@dataclass(kw_only=True)
class ScanStatus(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/scanstatus/
    """
    scanning: bool
    count: int | None = None


@dataclass(kw_only=True)
class SearchResult2(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/searchresult2/
    """
    artist: list[Artist] | None = None
    album: list[Child] | None = None
    song: list[Child] | None = None


@dataclass(kw_only=True)
class SearchResult3(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/searchresult3/
    """
    artist: list[ArtistID3] | None = None
    album: list[AlbumID3] | None = None
    song: list[Child] | None = None


@dataclass(kw_only=True)
class Share(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/share/
    """
    id: str
    url: str
    username: str
    created: str
    visit_count: Annotated[int, Alias("visitCount")]
    description: str | None = None
    expires: str | None = None
    last_visited: Annotated[str | None, Alias("lastVisited")] = None
    entry: list[Child] | None = None


@dataclass(kw_only=True)
class Starred(SearchResult2):
    """
    https://opensubsonic.github.io/docs/responses/starred/
    While named differently, this is the same as a search2 response
    """


@dataclass(kw_only=True)
class Starred2(SearchResult3):
    """
    https://opensubsonic.github.io/docs/responses/starred2/
    While named differently, this is the same as a search3 response
    """


@dataclass(kw_only=True)
class SonicMatch(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/sonicmatch/
    """
    entry: Child
    similarity: float


@dataclass(kw_only=True)
class StreamDetails(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/streamdetails/
    """
    protocol: str
    container: str
    codec: str
    audio_channels: Annotated[int | None, Alias("audioChannels")] = None
    audio_bitrate: Annotated[int | None, Alias("audioBitrate")] = None
    audio_profile: Annotated[str | None, Alias("audioProfile")] = None
    audio_samplerate: Annotated[int | None, Alias("audioSamplerate")] = None
    audio_bitdepth: Annotated[int | None, Alias("audioBitdepth")] = None


@dataclass(kw_only=True)
class TranscodeDecision(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/transcodedecision/
    """
    can_direct_play: Annotated[bool, Alias("canDirectPlay")]
    can_transcode: Annotated[bool, Alias("canTranscode")]
    transcode_reason: Annotated[list[str] | None, Alias("transcodeReason")] = None
    error_reason: Annotated[str | None, Alias("errorReason")] = None
    transcode_params: Annotated[str | None, Alias("transcodeParams")] = None
    source_stream: Annotated[StreamDetails | None, Alias("sourceStream")] = None
    transcode_stream: Annotated[StreamDetails | None, Alias("transcodeStream")] = None


@dataclass(kw_only=True)
class Cue(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/cue/
    """
    start: int
    byte_start: Annotated[int, Alias("byteStart")]
    byte_end: Annotated[int, Alias("byteEnd")]
    value: str
    end: int | None = None


@dataclass(kw_only=True)
class CueLine(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/cueline/
    """
    index: int
    value: str
    cue: list[Cue]
    start: int | None = None
    end: int | None = None
    agent_id: Annotated[str | None, Alias("agentId")] = None


@dataclass(kw_only=True)
class LyricsAgent(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/agent/
    """
    id: str
    role: str
    name: str | None = None


@dataclass(kw_only=True)
class StructuredLyrics(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/structuredlyrics/
    """
    lang: str
    synced: bool
    line: list[Line]
    display_artist: Annotated[str | None, Alias("displayArtist")] = None
    display_title: Annotated[str | None, Alias("displayTitle")] = None
    offset: float | None = None
    kind: str | None = None
    agents: list[LyricsAgent] | None = None
    cue_line: Annotated[list[CueLine] | None, Alias("cueLine")] = None


@dataclass(kw_only=True)
class TokenInfo(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/tokeninfo/
    """
    username: str


@dataclass(kw_only=True)
class TopSongs(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/topsongs/
    """
    song: list[Child] | None = None


@dataclass(kw_only=True)
class User(DataItem):
    """
    https://opensubsonic.github.io/docs/responses/user/
    """
    username: str
    scrobbling_enabled: Annotated[bool, Alias("scrobblingEnabled")]
    admin_role: Annotated[bool, Alias("adminRole")]
    settings_role: Annotated[bool, Alias("settingsRole")]
    download_role: Annotated[bool, Alias("downloadRole")]
    upload_role: Annotated[bool, Alias("uploadRole")]
    playlist_role: Annotated[bool, Alias("playlistRole")]
    cover_art_role: Annotated[bool, Alias("coverArtRole")]
    comment_role: Annotated[bool, Alias("commentRole")]
    podcast_role: Annotated[bool, Alias("podcastRole")]
    stream_role: Annotated[bool, Alias("streamRole")]
    jukebox_role: Annotated[bool, Alias("jukeboxRole")]
    share_role: Annotated[bool, Alias("shareRole")]
    video_conversion_role: Annotated[bool, Alias("videoConversionRole")]
    max_bit_rate: Annotated[int | None, Alias("maxBitRate")] = None
    avatar_last_changed: Annotated[str | None, Alias("avatarLastChanged")] = None
    folder: list[int] | None = None
