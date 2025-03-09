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

from .media_base import MediaBase, get_key
from . import artist

class Song(MediaBase):
    def __init__(self, info):
        self._parent = get_key(info, 'parent')
        self._title = get_key(info, 'title')
        self._album = get_key(info, 'album')
        self._album_id = get_key(info, 'albumId')
        self._artist = get_key(info, 'artist')
        self._display_artist = get_key(info, 'displayArtist')
        self._display_album_artist = get_key(info, 'displayAlbumArtist')
        self._artist_id = get_key(info, 'artistId')
        self._artists = []
        if 'artists' in info and info['artists']:
            for entry in info['artists']:
                self._artists.append(artist.Artist(entry))
        self._album_artists = []
        if 'albumArtists' in info and info['albumArtists']:
            for entry in info['albumArtists']:
                self._album_artists.append(artist.Artist(entry))
        self._is_dir = get_key(info, 'isDir')
        self._created = get_key(info, 'created')
        self._duration = get_key(info, 'duration', 0)
        self._bit_rate = get_key(info, 'bitRate')
        self._size = get_key(info, 'size')
        self._suffix = get_key(info, 'suffix')
        self._content_type = get_key(info, 'contentType')
        self._is_video = get_key(info, 'isVideo')
        self._path = get_key(info, 'path')
        self._track = get_key(info, 'track', 1)
        self._disc_number = get_key(info, 'discNumber', 1)
        self._type = get_key(info, 'type')
        self._year = get_key(info, 'year')
        self._transcoded_content_type = get_key(info, 'transcodedContentType')
        self._transcoded_suffix = get_key(info, 'transcodedSuffix')
        super().__init__(info)

    def to_dict(self):
        ret = super().to_dict()
        ret['parent'] = self._parent
        ret['title'] = self._title
        ret['album'] = self._album
        ret['albumId'] = self._album_id
        ret['artist'] = self._artist
        ret['displayArtist'] = self._display_artist
        ret['displayAlbumArtist'] = self._display_album_artist
        ret['artistId'] = self._artist_id
        ret['isDir'] = self._is_dir
        ret['created'] = self._created
        ret['duration'] = self._duration
        ret['bitRate'] = self._bit_rate
        ret['size'] = self._size
        ret['suffix'] = self._suffix
        ret['contentType'] = self._content_type
        ret['isVideo'] = self._is_video
        ret['path'] = self._path
        ret['discNumber'] = self._disc_number
        ret['track'] = self._track
        ret['type'] = self._type
        ret['year'] = self._year
        ret['transcodedContentType'] = self._transcoded_content_type
        ret['transcodedSuffix'] = self._transcoded_suffix
        if self._artists:
            ret['artists'] = [entry.to_dict() for entry in self.artists]
        if self._album_artists:
            ret['albumArtists'] = [entry.to_dict() for entry in self._album_artists]
        return ret

    parent = property(lambda s: s._parent)
    title = property(lambda s: s._title)
    album = property(lambda s: s._album)
    album_id = property(lambda s: s._album_id)
    artist = property(lambda s: s._artist)
    display_artist = property(lambda s: s._display_artist)
    display_album_artist = property(lambda s: s._display_album_artist)
    artists = property(lambda s: s._artists)
    album_artists = property(lambda s: s._album_artists)
    artist_id = property(lambda s: s._artist_id)
    is_dir = property(lambda s: s._is_dir)
    created = property(lambda s: s._created)
    duration = property(lambda s: s._duration)
    bit_rate = property(lambda s: s._bit_rate)
    size = property(lambda s: s._size)
    suffix = property(lambda s: s._suffix)
    content_type = property(lambda s: s._content_type)
    is_video = property(lambda s: s._is_video)
    path = property(lambda s: s._path)
    track = property(lambda s: s._track)
    type = property(lambda s: s._type)
    year = property(lambda s: s._year)
    disc_number = property(lambda s: s._disc_number)
    transcoded_content_type = property(lambda s: s._transcoded_content_type)
    transcoded_suffix = property(lambda s: s._transcoded_suffix)
