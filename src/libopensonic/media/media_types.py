from dataclasses import dataclass
from datetime import datetime


@dataclass
class ArtistID3:
    id                    : str
    name                  : str
    coverArt              : str
    artistImageURL        : str
    albumCount            : int
    starred               : datetime
    musicBrainzId         : str
    sortName              : str
    roles                 : list[str]


@dataclass
class Contributor:
    role                  : str
    subRole               : str
    artist                : ArtistID3


@dataclass
class ItemGenre:
    name                  : str


@dataclass
class ReplayGain:
    trackGain             : float
    albumGain             : float
    trackPeak             : float
    albumPeak             : float
    baseGain              : float
    fallbackGain          : float

    def __post_init__(self):
        if self.trackPeak < 0:
            raise ValueError("trackPeak must not be negative")
        if self.albumPeak < 0:
            raise ValueError("albumPeak must not be negative")

    
@dataclass
class Child:
    id                    : str
    parent                : str
    isDir                 : bool
    title                 : str
    album                 : str
    artist                : str
    track                 : int
    year                  : int
    genre                 : str
    coverArt              : str
    size                  : int
    contentType           : str
    suffix                : str
    transcodedContentType : str
    transcodedSuffix      : str
    duration              : int
    bitRate               : int
    bitDepth              : int
    samplingRate          : int
    channelCount          : int
    path                  : str
    isVideo               : bool
    userRating            : int
    averageRating         : float
    playCount             : int
    discNumber            : int
    created               : datetime
    starred               : datetime
    albumId               : str
    artistId              : str
    mediaType             : str
    bookmarkPosition      : int
    originalWidth         : int
    originalHeight        : int
    played                : datetime
    bpm                   : int
    comment               : str
    sortName              : str
    musicBrainzId         : str
    genres                : list[ItemGenre]
    artists               : list[ArtistID3]
    displayAlbumArtist    : str
    contributors          : list[Contributor]
    displayComposer       : str
    moods                 : list[str]
    replayGain            : ReplayGain
    explicitStatus        : str
