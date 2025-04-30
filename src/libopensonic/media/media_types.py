from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from mashumaro.config import BaseConfig
from mashumaro.mixins.json import DataClassJSONMixin

class DataItem(DataClassJSONMixin): 
    class Config(BaseConfig):
        omit_default = True


@dataclass(kw_only=True)
class AlbumID3(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/albumid3/
    """
    id                    : str
    name                  : str
    songCount             : int
    duration              : int
    created               : str
    version               : str = None
    artist                : str = None
    artistId              : str = None
    coverArt              : str = None
    playCount             : int = None
    starred               : str = None
    year                  : int = None
    genre                 : str = None
    played                : str = None
    userRating            : int = None
    recordLabels          : list[RecordLabel] = None
    musicBrainzId         : str = None
    genres                : list[ItemGenre] = None
    artists               : list[ArtistID3] = None
    displayArtist         : str = None
    releaseTypes          : list[str] = None
    moods                 : list[str] = None
    sortName              : str = None
    originalReleaseDate   : ItemDate = None
    releaseDate           : ItemDate = None
    isCompilation         : bool = False
    explicitStatus        : str = None
    discTitles            : list[DiscTitle] = None
    song                  : list[Child] = None


@dataclass(kw_only=True)
class Album(AlbumID3):
    """
    https://opensubsonic.netlify.app/docs/responses/album/
    This object is in the spec for backward compatibilty but, like AtristID3 and Artist,
    there is no difference in the required fields.
    """


@dataclass(kw_only=True)
class AlbumInfo(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/albuminfo/
    """
    notes                 : str = None
    musicBrainzId         : str = None
    lastFmUrl             : str = None
    smallImageUrl         : str = None
    mediumImageUrl        : str = None
    largeImageUrl         : str = None


@dataclass(kw_only=True)
class ArtistID3(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/artistid3/
    """
    id                    : str
    name                  : str
    albumCount            : int = None
    coverArt              : str = None
    artistImageURL        : str = None
    starred               : str = None
    album                 : list[AlbumID3] = None
    musicBrainzId         : str = None
    sortName              : str = None
    roles                 : list[str] = None


@dataclass(kw_only=True)
class Artist(ArtistID3):
    """
    https://opensubsonic.netlify.app/docs/responses/artist/
    
    While the spec has this object, it has the same required memebers as ArtistID3.
    """


@dataclass(kw_only=True)
class ArtistInfo(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/artistinfo/
    """
    biography             : str = None
    musicBrainzId         : str = None
    lastFmUrl             : str = None
    smallImageUrl         : str = None
    mediumImageUrl        : str = None
    largeImageUrl         : str = None
    similarArtist         : list[Artist] = None


@dataclass(kw_only=True)
class ArtistInfo2(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/artistinfo2/
    """
    biography             : str = None
    musicBrainzId         : str = None
    lastFmUrl             : str = None
    smallImageUrl         : str = None
    mediumImageUrl        : str = None
    largeImageUrl         : str = None
    similarArtist         : list[ArtistID3] = None


@dataclass(kw_only=True)
class Artists(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/indexes/
    """
    ignoredArticles       : str
    shortcut              : list[Artist] = None
    child                 : list[Child] = None
    index                 : list[Index] = None


@dataclass(kw_only=True)
class Bookmark(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/bookmark/
    """
    position              : int
    username              : str
    created               : str
    changed               : str
    entry                 : Child
    comment               : str = None


@dataclass(kw_only=True)
class ChatMessage(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/chatmessage/
    """
    username              : str
    time                  : int
    message               : str


@dataclass(kw_only=True)
class Child(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/child/
    """
    id                    : str
    isDir                 : bool
    title                 : str
    parent                : str = None
    album                 : str = None
    artist                : str = None
    track                 : int = None
    year                  : int = None
    genre                 : str = None
    coverArt              : str = None
    size                  : int = None
    contentType           : str = None
    suffix                : str = None
    transcodedContentType : str = None
    transcodedSuffix      : str = None
    duration              : int = None
    bitRate               : int = None
    bitDepth              : int = None
    samplingRate          : int = None
    channelCount          : int = None
    path                  : str = None
    isVideo               : bool = None
    userRating            : int = None
    averageRating         : float = None
    playCount             : int = None
    discNumber            : int = None
    created               : str = None
    starred               : str = None
    albumId               : str = None
    artistId              : str = None
    type                  : str = None
    mediaType             : str = None
    bookmarkPosition      : int = None
    originalWidth         : int = None
    originalHeight        : int = None
    played                : str = None
    bpm                   : int = None
    comment               : str = None
    sortName              : str = None
    musicBrainzId         : str = None
    genres                : list[ItemGenre] = None
    artists               : list[ArtistID3] = None
    albumArtists          : list[ArtistID3] = None
    displayArtist         : str = None
    displayAlbumArtist    : str = None
    contributors          : list[Contributor] = None
    displayComposer       : str = None
    moods                 : list[str] = None
    replayGain            : dict = None
    explicitStatus        : str = None


@dataclass(kw_only=True)
class Contributor(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/contributor/
    """
    role                  : str
    artist                : ArtistID3
    subRole               : str = None


@dataclass(kw_only=True)
class Directory(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/directory/
    """
    id                    : str
    name                  : str
    parent                : str = None
    starred               : str = None
    userRating            : int = None
    averageRating         : float = None
    playCount             : int = None
    child                 : list[Child] = None


@dataclass(kw_only=True)
class DiscTitle(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/disctitle/
    """
    disc                  : int
    title                 : str


@dataclass(kw_only=True)
class Error(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/error/
    """
    code                  : int
    message               : str = None
    helpUrl               : str = None


@dataclass(kw_only=True)
class Genre(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/genre/
    """
    value                 : str
    songCount             : int
    albumCount            : int


@dataclass(kw_only=True)
class Index(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/index_/
    """
    name                  : str
    artist                : list[Artist] = None


@dataclass(kw_only=True)
class Indexes(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/indexes/
    """
    ignoredArticles       : str
    lastModified          : int
    shortcut              : list[Artist] = None
    child                 : list[Child] = None
    index                 : list[Index] = None


@dataclass(kw_only=True)
class IndexID3(Index):
    """
    https://opensubsonic.netlify.app/docs/responses/indexid3/
    """


@dataclass(kw_only=True)
class InternetRadioStation(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/internetradiostation/
    """
    id                    : str
    name                  : str
    streamUrl             : str
    homePageUrl           : str = None


@dataclass(kw_only=True)
class ItemDate(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/itemdate/
    """
    year                  : int = None
    month                 : int = None
    day                   : int = None


@dataclass(kw_only=True)
class ItemGenre(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/itemgenre/
    """
    name                  : str


@dataclass(kw_only=True)
class JukeboxPlaylist(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/jukeboxplaylist/
    """
    currentIndex          : int
    playing               : bool
    gain                  : float
    position              : int = None
    entry                 : list[Child] = None


@dataclass(kw_only=True)
class JukeboxStatus(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/jukeboxstatus/
    """
    currentIndex          : int
    playing               : bool
    gain                  : float
    position              : int = None


@dataclass(kw_only=True)
class Line(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/line/
    """
    value                 : str
    start                 : float = None


@dataclass(kw_only=True)
class Lyrics(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/lyrics/
    """
    value                 : str
    artist                : str = None
    title                 : str = None


@dataclass(kw_only=True)
class MusicFolder(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/musicfolder/
    """
    id                    : int
    name                  : str = None


@dataclass(kw_only=True)
class NowPlayingEntry(Child):
    """
    https://opensubsonic.netlify.app/docs/responses/nowplayingentry/
    """
    username              : str
    minutesAgo            : int
    playerId              : int
    playerName            : str = None


@dataclass(kw_only=True)
class OpenSubsonicExtension(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/opensubsonicextension/
    """
    name                  : str
    versions              : list[int]


@dataclass(kw_only=True)
class Playlist(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/playlistwithsongs/
    """
    id                    : str
    name                  : str
    songCount             : int
    duration              : int
    created               : str
    changed               : str
    comment               : str = None
    owner                 : str = None
    public                : bool = None
    coverArt              : str = None
    allowedUser           : list[str] = None
    entry                 : list[Child] = None


@dataclass(kw_only=True)
class PlayQueue(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/playqueue/
    """
    username              : str
    changed               : str
    changedBy             : str
    current               : str = None
    position              : int = None
    entry                 : list[Child] = None


@dataclass(kw_only=True)
class PodcastChannel(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/podcastchannel/
    """
    id                    : str
    url                   : str
    status                : PodcastStatus
    title                 : str = None
    description           : str = None
    coverArt              : str = None
    originalImageUrl      : str = None
    errorMessage          : str = None
    episode               : list[PodcastEpisode] = None

@dataclass(kw_only=True)
class PodcastEpisode(Child):
    """
    https://opensubsonic.netlify.app/docs/responses/podcastepisode/
    """
    channelId             : str
    status                : PodcastStatus
    streamId              : str
    description           : str = None
    publishDate           : str = None


class PodcastStatus(Enum):
    """
    https://opensubsonic.netlify.app/docs/responses/podcaststatus/
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
    https://opensubsonic.netlify.app/docs/responses/recordlabel/
    """
    name                  : str


@dataclass(kw_only=True)
class ReplayGain(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/replaygain/
    """
    trackGain             : float = None
    albumGain             : float = None
    trackPeak             : float = None
    albumPeak             : float = None
    baseGain              : float = None
    fallbackGain          : float = None


@dataclass(kw_only=True)
class ScanStatus(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/scanstatus/
    """
    scanning              : bool
    count                 : int = None


@dataclass(kw_only=True)
class SearchResult2(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/searchresult2/
    """
    artist                : list[Artist] = None
    album                 : list[Album] = None
    song                  : list[Child] = None


@dataclass(kw_only=True)
class SearchResult3(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/searchresult3/
    """
    artist                : list[ArtistID3] = None
    album                 : list[AlbumID3] = None
    song                  : list[Child] = None


@dataclass(kw_only=True)
class Share(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/share/
    """
    id                    : str
    url                   : str
    username              : str
    created               : str
    visitCount            : int
    description           : str = None
    expires               : str = None
    lastVisited           : str = None
    entry                 : list[Child] = None


@dataclass(kw_only=True)
class Starred(SearchResult2):
    """
    https://opensubsonic.netlify.app/docs/responses/starred/
    While named differently, this is the same as a search2 response
    """


@dataclass(kw_only=True)
class Starred2(SearchResult3):
    """
    https://opensubsonic.netlify.app/docs/responses/starred2/
    While named differently, this is the same as a search3 response
    """


@dataclass(kw_only=True)
class StructuredLyrics(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/structuredlyrics/
    """
    lang                  : str
    synced                : bool
    line                  : list[Line]
    displayArtist         : str = None
    displayTitle          : str = None
    offset                : float = None


@dataclass(kw_only=True)
class TokenInfo(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/tokeninfo/
    """
    username              : str


@dataclass(kw_only=True)
class TopSongs(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/topsongs/
    """
    song                  : list[Child] = None


@dataclass(kw_only=True)
class User(DataItem):
    """
    https://opensubsonic.netlify.app/docs/responses/user/
    """
    username              : str
    scrobblingEnabled     : bool
    adminRole             : bool
    settingsRole          : bool
    downloadRole          : bool
    uploadRole            : bool
    playlistRole          : bool
    coverArtRole          : bool
    commentRole           : bool
    podcastRole           : bool
    streamRole            : bool
    jukeboxRole           : bool
    shareRole             : bool
    videoConversionRole   : bool
    maxBitRate            : int = None
    avatarLastChanged     : str = None
    folder                : list[int] = None
