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

from netrc import netrc
from hashlib import md5
import os
import requests

from . import errors
from .media.podcast_channel import PodcastChannel
from .media.podcast_channel import PodcastEpisode
from .media.artist import (Artist, ArtistInfo)
from .media.song import (Song)
from .media.album import (Album, AlbumInfo)
from .media.index import Index
from .media.playlist import Playlist
from .media.media_types import Child

API_VERSION = '1.16.1'


def pretty_print_post(req):
    print('{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))



class Connection:
    def __init__(self, baseUrl, username=None, password=None, port=4040,
            serverPath='', appName='py-opensonic', apiVersion=API_VERSION,
            insecure=False, useNetrc=None, legacyAuth=False, useGET=False, useViews=True):
        """
        This will create a connection to your subsonic server

        baseUrl:str         The base url for your server. Be sure to use
                            "https" for SSL connections.  If you are using
                            a port other than the default 4040, be sure to
                            specify that with the port argument.  Do *not*
                            append it here.

                            ex: http://subsonic.example.com

                            If you are running subsonic under a different
                            path, specify that with the "serverPath" arg,
                            *not* here.  For example, if your subsonic
                            lives at:

                            https://mydomain.com:8080/path/to/subsonic/rest

                            You would set the following:

                            baseUrl = "https://mydomain.com"
                            port = 8080
                            serverPath = "/path/to/subsonic/rest"
        username:str        The username to use for the connection.  This
                            can be None if `useNetrc' is True (and you
                            have a valid entry in your netrc file)
        password:str        The password to use for the connection.  This
                            can be None if `useNetrc' is True (and you
                            have a valid entry in your netrc file)
        port:int            The port number to connect on.  The default for
                            unencrypted subsonic connections is 4040
        serverPath:str      The base resource path for the subsonic views.
                            This is useful if you have your subsonic server
                            behind a proxy and the path that you are proxying
                            is different from the default of '/rest'.
                            Ex:
                                serverPath='/path/to/subs'

                              The full url that would be built then would be
                              (assuming defaults and using "example.com" and
                              you are using the "ping" view):

                                http://example.com:4040/path/to/subs/ping
        appName:str         The name of your application.
        apiVersion:str      The API version you wish to use for your
                            application.  Subsonic will throw an error if you
                            try to use/send an api version higher than what
                            the server supports.  See the Subsonic API docs
                            to find the Subsonic version -> API version table.
                            This is useful if you are connecting to an older
                            version of Subsonic.
        insecure:bool       This will allow you to use self signed
                            certificates when connecting if set to True.
        useNetrc:str|bool   You can either specify a specific netrc
                            formatted file or True to use your default
                            netrc file ($HOME/.netrc).
        legacyAuth:bool     Use pre-1.13.0 API version authentication
        useGET:bool         Use a GET request instead of the default POST
                            request.  This is not recommended as request
                            URLs can get very long with some API calls
        useViews:bool       The original Subsonic wanted API clients
                            user the .view end points instead of just the method
                            name. Disable this to drop the .view extension to
                            method name, e.g. ping instead of ping.view
        """
        self.setBaseUrl(baseUrl)
        self._username = username
        self._rawPass = password
        self._legacyAuth = legacyAuth
        self._useGET = useGET
        self._useViews = useViews
        self._apiVersion = apiVersion

        self._netrc = None
        if useNetrc is not None:
            self._process_netrc(useNetrc)
        elif username is None or password is None:
            raise errors.CredentialError('You must specify either a username/password '
                'combination or "useNetrc" must be either True or a string '
                'representing a path to a netrc file')

        self.setPort(port)
        self.setAppName(appName)
        self.setServerPath(serverPath)
        self.setInsecure(insecure)


    # Properties
    def setBaseUrl(self, url):
        self._baseUrl = url
        if '://' in url:
            self._hostname = url.split('://')[1].strip()
        else:
            self._hostname = url
    baseUrl = property(lambda s: s._baseUrl, setBaseUrl)


    def setPort(self, port):
        self._port = int(port)
    port = property(lambda s: s._port, setPort)


    def setUsername(self, username):
        self._username = username
    username = property(lambda s: s._username, setUsername)


    def setPassword(self, password):
        self._rawPass = password
        # Redo the opener with the new creds
    password = property(lambda s: s._rawPass, setPassword)


    apiVersion = property(lambda s: s._apiVersion)


    def setAppName(self, appName):
        self._appName = appName
    appName = property(lambda s: s._appName, setAppName)


    def setServerPath(self, path):
        sep = ''
        if path != '' and not path.endswith('/'):
            sep = '/'
        self._serverPath = f"{path}{sep}rest".strip('/')
    serverPath = property(lambda s: s._serverPath, setServerPath)


    def setInsecure(self, insecure):
        self._insecure = insecure
    insecure = property(lambda s: s._insecure, setInsecure)


    def setLegacyAuth(self, lauth):
        self._legacyAuth = lauth
    legacyAuth = property(lambda s: s._legacyAuth, setLegacyAuth)


    def setGET(self, get):
        self._useGET = get
    useGET = property(lambda s: s._useGET, setGET)


    # API methods
    def ping(self):
        """
        since: 1.0.0

        Returns a boolean True if the server is alive, False otherwise
        """
        methodName = 'ping'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        if dres['status'] == 'ok':
            return True
        elif dres['status'] == 'failed':
            exc = errors.getExcByCode(dres['error']['code'])
            raise exc(dres['error']['message'])
        return False


    def getLicense(self):
        """
        since: 1.0.0

        Gets details related to the software license

        Returns a dict like the following:

        {u'license': {u'date': u'2010-05-21T11:14:39',
                      u'email': u'email@example.com',
                      u'key': u'12345678901234567890123456789012',
                      u'valid': True},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getLicense'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres
    

    def getOpenSubsonicExtensions(self):
        """
        since OpenSubsonic 1

        List the OpenSubsonic extensions supported by this server.

        Returns a dict like the following:
        {u'openSubsonicExtensions': [
            {u'name': u'template',
             u'versions': [1,2]},
            {u'name': u'transcodeOffset',
             u'versions': [1]}]
        }
        """
        methodName = 'getOpenSubsonicExtensions'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def getScanStatus(self):
        """
        since: 1.15.0

        returns the current status for media library scanning.
        takes no extra parameters.

        returns a dict like the following:

        {'status': 'ok', 'version': '1.15.0',
        'scanstatus': {'scanning': true, 'count': 4680}}

        'count' is the total number of items to be scanned
        """
        methodName = 'getScanStatus'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def startScan(self):
        """
        since: 1.15.0

        Initiates a rescan of the media libraries.
        Takes no extra parameters.

        returns a dict like the following:

        {'status': 'ok', 'version': '1.15.0',
        'scanstatus': {'scanning': true, 'count': 0}}

        'scanning' changes to false when a scan is complete
        'count' starts a 0 and ends at the total number of items scanned

        """
        methodName = 'startScan'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def getMusicFolders(self):
        """
        since: 1.0.0

        Returns all configured music folders

        Returns a dict like the following:

        {u'musicFolders': {u'musicFolder': [{u'id': 0, u'name': u'folder1'},
                                    {u'id': 1, u'name': u'folder2'},
                                    {u'id': 2, u'name': u'folder3'}]},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getMusicFolders'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def getNowPlaying(self):
        """
        since: 1.0.0

        Returns what is currently being played by all users

        Returns a dict of username string to media.Album
        """
        methodName = 'getNowPlaying'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        playing = {}
        for entry in dres['nowPlaying']['entry']:
            playing[entry['username']] = Song(entry)
        return playing


    def getIndexes(self, musicFolderId=None, ifModifiedSince=0):
        """
        since: 1.0.0

        Returns an indexed structure of all artists

        musicFolderId:int       If this is specified, it will only return
                                artists for the given folder ID from
                                the getMusicFolders call
        ifModifiedSince:int     If specified, return a result if the artist
                                collection has changed since the given
                                unix timestamp

        Returns a list of media.Index

        """
        methodName = 'getIndexes'

        q = self._getQueryDict({'musicFolderId': musicFolderId,
            'ifModifiedSince': self._ts2milli(ifModifiedSince)})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        indices = [Index(entry) for entry in dres['indexes']['index']]
        return indices


    def getMusicDirectory(self, mid):
        """
        since: 1.0.0

        Returns a listing of all files in a music directory.  Typically used
        to get a list of albums for an artist or list of songs for an album.

        mid:str     The string ID value which uniquely identifies the
                    folder.  Obtained via calls to getIndexes or
                    getMusicDirectory.  REQUIRED

        Returns a dict like the following:

        {u'directory': {u'child': [{u'artist': u'A Tribe Called Quest',
                            u'coverArt': u'223484',
                            u'id': u'329084',
                            u'isDir': True,
                            u'parent': u'234823940',
                            u'title': u'Beats, Rhymes And Life'},
                           {u'artist': u'A Tribe Called Quest',
                            u'coverArt': u'234823794',
                            u'id': u'238472893',
                            u'isDir': True,
                            u'parent': u'2308472938',
                            u'title': u'Midnight Marauders'},
                           {u'artist': u'A Tribe Called Quest',
                            u'coverArt': u'39284792374',
                            u'id': u'983274892',
                            u'isDir': True,
                            u'parent': u'9823749',
                            u'title': u"People's Instinctive Travels And The Paths Of Rhythm"},
                           {u'artist': u'A Tribe Called Quest',
                            u'coverArt': u'289347293',
                            u'id': u'3894723934',
                            u'isDir': True,
                            u'parent': u'9832942',
                            u'title': u'The Anthology'},
                           {u'artist': u'A Tribe Called Quest',
                            u'coverArt': u'923847923',
                            u'id': u'29834729',
                            u'isDir': True,
                            u'parent': u'2934872893',
                            u'title': u'The Love Movement'},
                           {u'artist': u'A Tribe Called Quest',
                            u'coverArt': u'9238742893',
                            u'id': u'238947293',
                            u'isDir': True,
                            u'parent': u'9432878492',
                            u'title': u'The Low End Theory'}],
                u'id': u'329847293',
                u'name': u'A Tribe Called Quest'},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getMusicDirectory'

        res = self._doRequest(methodName, {'id': mid})
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def search(self, artist=None, album=None, title=None, any=None,
            count=20, offset=0, newerThan=None):
        """
        since: 1.0.0

        DEPRECATED SINCE API 1.4.0!  USE search2() INSTEAD!

        Returns a listing of files matching the given search criteria.
        Supports paging with offset

        artist:str      Search for artist
        album:str       Search for album
        title:str       Search for title of song
        any:str         Search all fields
        count:int       Max number of results to return [default: 20]
        offset:int      Search result offset.  For paging [default: 0]
        newerThan:int   Return matches newer than this timestamp
        """
        if artist == album == title == any == None:
            raise errors.ArgumentError('Invalid search.  You must supply search '
                'criteria')
        methodName = 'search'

        q = self._getQueryDict({'artist': artist, 'album': album,
            'title': title, 'any': any, 'count': count, 'offset': offset,
            'newerThan': self._ts2milli(newerThan)})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def search2(self, query, artistCount=20, artistOffset=0, albumCount=20,
            albumOffset=0, songCount=20, songOffset=0, musicFolderId=None):
        """
        since: 1.4.0

        Returns albums, artists and songs matching the given search criteria.
        Supports paging through the result.

        query:str           The search query
        artistCount:int     Max number of artists to return [default: 20]
        artistOffset:int    Search offset for artists (for paging) [default: 0]
        albumCount:int      Max number of albums to return [default: 20]
        albumOffset:int     Search offset for albums (for paging) [default: 0]
        songCount:int       Max number of songs to return [default: 20]
        songOffset:int      Search offset for songs (for paging) [default: 0]
        musicFolderId:int   Only return dresults from the music folder
                            with the given ID. See getMusicFolders

        Returns a dict containing 3 keys, 'artists', 'albums', and 'songs' with each
        holding a list of media.Artist, media.Album, or media.Song respectively
        """
        methodName = 'search2'

        q = self._getQueryDict({'query': query, 'artistCount': artistCount,
            'artistOffset': artistOffset, 'albumCount': albumCount,
            'albumOffset': albumOffset, 'songCount': songCount,
            'songOffset': songOffset, 'musicFolderId': musicFolderId})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        found = {}
        if 'artist' in dres['searchResult2']:
            found['artists'] = [Artist(entry) for entry in dres['searchResult2']['artist']]
        else:
            found['artists'] = []
        if 'album' in dres['searchResult2']:
            found['albums'] = [Album(entry) for entry in dres['searchResult2']['album']]
        else:
            found['albums'] = []
        if 'song' in dres['searchResult2']:
            found['songs'] = [Song(entry) for entry in dres['searchResult2']['song']]
        else:
            found['songs'] = []
        return found


    def search3(self, query, artistCount=20, artistOffset=0, albumCount=20,
            albumOffset=0, songCount=20, songOffset=0, musicFolderId=None):
        """
        since: 1.8.0

        Works the same way as search2, but uses ID3 tags for
        organization

        query:str           The search query
        artistCount:int     Max number of artists to return [default: 20]
        artistOffset:int    Search offset for artists (for paging) [default: 0]
        albumCount:int      Max number of albums to return [default: 20]
        albumOffset:int     Search offset for albums (for paging) [default: 0]
        songCount:int       Max number of songs to return [default: 20]
        songOffset:int      Search offset for songs (for paging) [default: 0]
        musicFolderId:int   Only return dresults from the music folder
                            with the given ID. See getMusicFolders

        Returns a dict containing 3 keys, 'artists', 'albums', and 'songs' with each
        holding a list of media.Artist, media.Album, or media.Song respectively
        """
        methodName = 'search3'

        q = self._getQueryDict({'query': query, 'artistCount': artistCount,
            'artistOffset': artistOffset, 'albumCount': albumCount,
            'albumOffset': albumOffset, 'songCount': songCount,
            'songOffset': songOffset, 'musicFolderId': musicFolderId})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        found = {}
        if 'artist' in dres['searchResult3']:
            found['artists'] = [Artist(entry) for entry in dres['searchResult3']['artist']]
        else:
            found['artists'] = []
        if 'album' in dres['searchResult3']:
            found['albums'] = [Album(entry) for entry in dres['searchResult3']['album']]
        else:
            found['albums'] = []
        if 'song' in dres['searchResult3']:
            found['songs'] = [Song(entry) for entry in dres['searchResult3']['song']]
        else:
            found['songs'] = []
        return found


    def getPlaylists(self, username=None):
        """
        since: 1.0.0

        Returns the ID and name of all saved playlists
        The "username" option was added in 1.8.0.

        username:str        If specified, return playlists for this user
                            rather than for the authenticated user.  The
                            authenticated user must have admin role
                            if this parameter is used

        Returns a list of media.Playlist

        note:       The Playlist objects returned are not the full playlist
                    (with tracks) but meant to give the basic details of what
                    playlists are available. For the full object see getPlaylist()
        """
        methodName = 'getPlaylists'

        q = self._getQueryDict({'username': username})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return [Playlist(entry) for entry in dres['playlists']['playlist']]


    def getPlaylist(self, pid):
        """
        since: 1.0.0

        Returns a listing of files in a saved playlist

        id:str      The ID of the playlist as returned in getPlaylists()

        Returns a media.Playlist complete with all tracks

        """
        methodName = 'getPlaylist'

        res = self._doRequest(methodName, {'id': pid})
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return Playlist(dres['playlist'])


    def createPlaylist(self, playlistId=None, name=None, songIds=None):
        """
        since: 1.2.0

        Creates OR updates a playlist.  If updating the list, the
        playlistId is required.  If creating a list, the name is required.

        playlistId:str      The ID of the playlist to UPDATE
        name:str            The name of the playlist to CREATE
        songIds:list        The list of songIds to populate the list with in
                            either create or update mode.  Note that this
                            list will replace the existing list if updating

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'createPlaylist'

        if songIds is None:
            songIds = []

        if playlistId == name == None:
            raise errors.ArgumentError('You must supply either a playlistId or a name')
        if playlistId is not None and name is not None:
            raise errors.ArgumentError('You can only supply either a playlistId '
                 'OR a name, not both')

        q = self._getQueryDict({'playlistId': playlistId, 'name': name})

        res = self._doRequestWithList(methodName, 'songId', songIds, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def deletePlaylist(self, pid):
        """
        since: 1.2.0

        Deletes a saved playlist

        pid:str     ID of the playlist to delete, as obtained by getPlaylists

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'deletePlaylist'

        res = self._doRequest(methodName, {'id': pid})
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def download(self, sid):
        """
        since: 1.0.0

        Downloads a given music file.

        sid:str     The ID of the music file to download.

        Returns the file-like object for reading or raises an exception
        on error
        """
        methodName = 'download'

        res = self._doRequest(methodName, {'id': sid})
        dres = self._handleBinRes(res)
        if isinstance(dres, dict):
            self._checkStatus(dres)
        return dres


    def stream(self, sid, maxBitRate=0, tformat=None, timeOffset=None,
            size=None, estimateContentLength=False, converted=False):
        """
        since: 1.0.0

        Downloads a given music file.

        sid:str         The ID of the music file to download.
        maxBitRate:int  (since: 1.2.0) If specified, the server will
                        attempt to limit the bitrate to this value, in
                        kilobits per second. If set to zero (default), no limit
                        is imposed. Legal values are: 0, 32, 40, 48, 56, 64,
                        80, 96, 112, 128, 160, 192, 224, 256 and 320.
        tformat:str     (since: 1.6.0) Specifies the target format
                        (e.g. "mp3" or "flv") in case there are multiple
                        applicable transcodings (since: 1.9.0) You can use
                        the special value "raw" to disable transcoding
        timeOffset:int  (since: 1.6.0) Only applicable to video
                        streaming.  Start the stream at the given
                        offset (in seconds) into the video
        size:str        (since: 1.6.0) The requested video size in
                        WxH, for instance 640x480
        estimateContentLength:bool  (since: 1.8.0) If set to True,
                                    the HTTP Content-Length header
                                    will be set to an estimated
                                    value for trancoded media
        converted:bool  (since: 1.14.0) Only applicable to video streaming.
                        Subsonic can optimize videos for streaming by
                        converting them to MP4. If a conversion exists for
                        the video in question, then setting this parameter
                        to "true" will cause the converted video to be
                        returned instead of the original.

        Returns the file-like object for reading or raises an exception
        on error
        """
        methodName = 'stream'

        q = self._getQueryDict({'id': sid, 'maxBitRate': maxBitRate,
            'format': tformat, 'timeOffset': timeOffset, 'size': size,
            'estimateContentLength': estimateContentLength,
            'converted': converted})

        res = self._doRequest(methodName, q, is_stream=True)
        dres = self._handleBinRes(res)
        if isinstance(dres, dict):
            self._checkStatus(dres)
        return dres


    def getCoverArt(self, aid, size=None):
        """
        since: 1.0.0

        Returns a cover art image

        aid:str     ID string for the cover art image to download
        size:int    If specified, scale image to this size

        Returns the file-like object for reading or raises an exception
        on error
        """
        methodName = 'getCoverArt'

        q = self._getQueryDict({'id': aid, 'size': size})

        res = self._doRequest(methodName, q, is_stream=True)
        dres = self._handleBinRes(res)
        if isinstance(dres, dict):
            self._checkStatus(dres)
        return dres


    def scrobble(self, sid, submission=True, listenTime=None):
        """
        since: 1.5.0

        "Scrobbles" a given music file on last.fm.  Requires that the user
        has set this up.

        Since 1.8.0 you may specify multiple id (and optionally time)
        parameters to scrobble multiple files.

        Since 1.11.0 this method will also update the play count and
        last played timestamp for the song and album. It will also make
        the song appear in the "Now playing" page in the web app, and
        appear in the list of songs returned by getNowPlaying

        sid:str             The ID of the file to scrobble
        submission:bool     Whether this is a "submission" or a "now playing"
                            notification
        listenTime:int      (Since 1.8.0) The time (unix timestamp) at
                            which the song was listened to.

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'scrobble'

        q = self._getQueryDict({'id': sid, 'submission': submission,
            'time': self._ts2milli(listenTime)})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def changePassword(self, username, password):
        """
        since: 1.1.0

        Changes the password of an existing Subsonic user.  Note that the
        user performing this must have admin privileges

        username:str        The username whose password is being changed
        password:str        The new password of the user

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'changePassword'

        # There seems to be an issue with some subsonic implementations
        # not recognizing the "enc:" precursor to the encoded password and
        # encodes the whole "enc:<hex>" as the password.  Weird.
        #q = {'username': username, 'password': hexPass.lower()}
        q = {'username': username, 'password': password}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def getUser(self, username):
        """
        since: 1.3.0

        Get details about a given user, including which auth roles it has.
        Can be used to enable/disable certain features in the client, such
        as jukebox control

        username:str        The username to retrieve.  You can only retrieve
                            your own user unless you have admin privs.

        Returns a dict like the following:

        {u'status': u'ok',
         u'user': {u'adminRole': False,
               u'commentRole': False,
               u'coverArtRole': False,
               u'downloadRole': True,
               u'jukeboxRole': False,
               u'playlistRole': True,
               u'podcastRole': False,
               u'settingsRole': True,
               u'streamRole': True,
               u'uploadRole': True,
               u'username': u'test'},
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getUser'

        q = {'username': username}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def getUsers(self):
        """
        since 1.8.0

        Gets a list of users

        returns a dict like the following

        {u'status': u'ok',
         u'users': {u'user': [{u'adminRole': True,
                   u'commentRole': True,
                   u'coverArtRole': True,
                   u'downloadRole': True,
                   u'jukeboxRole': True,
                   u'playlistRole': True,
                   u'podcastRole': True,
                   u'scrobblingEnabled': True,
                   u'settingsRole': True,
                   u'shareRole': True,
                   u'streamRole': True,
                   u'uploadRole': True,
                   u'username': u'user1'},
                   ...
                   ...
                   ]},
         u'version': u'1.10.2',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getUsers'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def createUser(self, username, password, email,
            ldapAuthenticated=False, adminRole=False, settingsRole=True,
            streamRole=True, jukeboxRole=False, downloadRole=False,
            uploadRole=False, playlistRole=False, coverArtRole=False,
            commentRole=False, podcastRole=False, shareRole=False,
            videoConversionRole=False, musicFolderId=None):
        """
        since: 1.1.0

        Creates a new subsonic user, using the parameters defined.  See the
        documentation at http://subsonic.org for more info on all the roles.

        username:str        The username of the new user
        password:str        The password for the new user
        email:str           The email of the new user
        <For info on the boolean roles, see http://subsonic.org for more info>
        musicFolderId:int   These are the only folders the user has access to

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'createUser'
        hexPass = 'enc:%s' % self._hexEnc(password)

        q = self._getQueryDict({
            'username': username, 'password': hexPass, 'email': email,
            'ldapAuthenticated': ldapAuthenticated, 'adminRole': adminRole,
            'settingsRole': settingsRole, 'streamRole': streamRole,
            'jukeboxRole': jukeboxRole, 'downloadRole': downloadRole,
            'uploadRole': uploadRole, 'playlistRole': playlistRole,
            'coverArtRole': coverArtRole, 'commentRole': commentRole,
            'podcastRole': podcastRole, 'shareRole': shareRole,
            'videoConversionRole': videoConversionRole,
            'musicFolderId': musicFolderId
        })

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def updateUser(self, username,  password=None, email=None,
            ldapAuthenticated=False, adminRole=False, settingsRole=True,
            streamRole=True, jukeboxRole=False, downloadRole=False,
            uploadRole=False, playlistRole=False, coverArtRole=False,
            commentRole=False, podcastRole=False, shareRole=False,
            videoConversionRole=False, musicFolderId=None, maxBitRate=0):
        """
        since 1.10.1

        Modifies an existing Subsonic user.

        username:str        The username of the user to update.
        musicFolderId:int   Only return dresults from the music folder
                            with the given ID. See getMusicFolders
        maxBitRate:int      The max bitrate for the user.  0 is unlimited

        All other args are the same as create user and you can update
        whatever item you wish to update for the given username.

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'updateUser'
        if password is not None:
            password = 'enc:%s' % self._hexEnc(password)
        q = self._getQueryDict({'username': username, 'password': password,
            'email': email, 'ldapAuthenticated': ldapAuthenticated,
            'adminRole': adminRole,
            'settingsRole': settingsRole, 'streamRole': streamRole,
            'jukeboxRole': jukeboxRole, 'downloadRole': downloadRole,
            'uploadRole': uploadRole, 'playlistRole': playlistRole,
            'coverArtRole': coverArtRole, 'commentRole': commentRole,
            'podcastRole': podcastRole, 'shareRole': shareRole,
            'videoConversionRole': videoConversionRole,
            'musicFolderId': musicFolderId, 'maxBitRate': maxBitRate
        })
        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def deleteUser(self, username):
        """
        since: 1.3.0

        Deletes an existing Subsonic user.  Of course, you must have admin
        rights for this.

        username:str        The username of the user to delete

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'deleteUser'

        q = {'username': username}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def getChatMessages(self, since=1):
        """
        since: 1.2.0

        Returns the current visible (non-expired) chat messages.

        since:int       Only return messages newer than this timestamp

        NOTE: All times returned are in MILLISECONDS since the Epoch, not
              seconds!

        Returns a dict like the following:
        {u'chatMessages': {u'chatMessage': {u'message': u'testing 123',
                                            u'time': 1303411919872L,
                                            u'username': u'admin'}},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getChatMessages'

        q = {'since': self._ts2milli(since)}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def addChatMessage(self, message):
        """
        since: 1.2.0

        Adds a message to the chat log

        message:str     The message to add

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'addChatMessage'

        q = {'message': message}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def getAlbumList(self, ltype, size=10, offset=0, fromYear=None,
            toYear=None, genre=None, musicFolderId=None):
        """
        since: 1.2.0

        Returns a list of random, newest, highest rated etc. albums.
        Similar to the album lists on the home page of the Subsonic
        web interface

        ltype:str       The list type. Must be one of the following: random,
                        newest, highest, frequent, recent,
                        (since 1.8.0 -> )starred, alphabeticalByName,
                        alphabeticalByArtist
                        Since 1.10.1 you can use byYear and byGenre to
                        list albums in a given year range or genre.
        size:int        The number of albums to return. Max 500
        offset:int      The list offset. Use for paging. Max 5000
        fromYear:int    If you specify the ltype as "byYear", you *must*
                        specify fromYear
        toYear:int      If you specify the ltype as "byYear", you *must*
                        specify toYear
        genre:str       The name of the genre e.g. "Rock".  You must specify
                        genre if you set the ltype to "byGenre"
        musicFolderId:str   Only return albums in the music folder with
                            the given ID. See getMusicFolders()

        Returns a list of media.Album
        """
        methodName = 'getAlbumList'

        q = self._getQueryDict({'type': ltype, 'size': size,
            'offset': offset, 'fromYear': fromYear, 'toYear': toYear,
            'genre': genre, 'musicFolderId': musicFolderId})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        if 'album' not in dres['albumList']:
            return []
        return [Album(entry) for entry in dres['albumList']['album']]


    def getAlbumList2(self, ltype, size=10, offset=0, fromYear=None,
            toYear=None, genre=None):
        """
        since 1.8.0

        Returns a list of random, newest, highest rated etc. albums.
        This is similar to getAlbumList, but uses ID3 tags for
        organization

        ltype:str       The list type. Must be one of the following: random,
                        newest, highest, frequent, recent,
                        (since 1.8.0 -> )starred, alphabeticalByName,
                        alphabeticalByArtist
                        Since 1.10.1 you can use byYear and byGenre to
                        list albums in a given year range or genre.
        size:int        The number of albums to return. Max 500
        offset:int      The list offset. Use for paging. Max 5000
        fromYear:int    If you specify the ltype as "byYear", you *must*
                        specify fromYear
        toYear:int      If you specify the ltype as "byYear", you *must*
                        specify toYear
        genre:str       The name of the genre e.g. "Rock".  You must specify
                        genre if you set the ltype to "byGenre"

        Returns a list of media.Album
        """
        methodName = 'getAlbumList2'

        q = self._getQueryDict({'type': ltype, 'size': size,
            'offset': offset, 'fromYear': fromYear, 'toYear': toYear,
            'genre': genre})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        if 'album' not in dres['albumList2']:
            return []
        return [Album(entry) for entry in dres['albumList2']['album']]


    def getRandomSongs(self, size=10, genre=None, fromYear=None,
            toYear=None, musicFolderId=None):
        """
        since 1.2.0

        Returns random songs matching the given criteria

        size:int            The max number of songs to return. Max 500
        genre:str           Only return songs from this genre
        fromYear:int        Only return songs after or in this year
        toYear:int          Only return songs before or in this year
        musicFolderId:str   Only return songs in the music folder with the
                            given ID.  See getMusicFolders

        Returns a list of media.Song
        """
        methodName = 'getRandomSongs'

        q = self._getQueryDict({'size': size, 'genre': genre,
            'fromYear': fromYear, 'toYear': toYear,
            'musicFolderId': musicFolderId})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return [Song(entry) for entry in dres['randomSongs']['song']]


    def getLyrics(self, artist=None, title=None):
        """
        since: 1.2.0

        Searches for and returns lyrics for a given song

        artist:str      The artist name
        title:str       The song title

        Returns a dict like the following for
        getLyrics('Bob Dylan', 'Blowin in the wind'):

        {u'lyrics': {u'artist': u'Bob Dylan',
             u'content': u"How many roads must a man walk down<snip>",
             u'title': u"Blowin' in the Wind"},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getLyrics'

        q = self._getQueryDict({'artist': artist, 'title': title})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres
    

    def getLyricsBySongId(self, song_id):
        """
        Since Open Subsonic ver 1

        Retrieves all structured lyrics from the server for a given song.
        The lyrics can come from embedded tags (SYLT/USLT), LRC file/text
        file, or any other external source.

        id:str          The id of the requested songA

        Returns a dict like the following object:

        {u"lyricsList": {
          u"structuredLyrics": [
          {
            u"displayArtist": u"Muse",
            u"displayTitle": u"Hysteria",
            u"lang": u"eng",
            u"offset": -100,
            u"synced": true,
            u"line": [ {
              u"start": 0,
              u"value": u"It's bugging me"
            }, {
              u"start": 2000,
              u"value": u"Grating me"
            }, {
              u"start": 3001,
              u"value": u"And twisting me around..."
            } ] },
          {
            u"displayArtist": u"Muse",
            u"displayTitle": u"Hysteria",
            u"lang": u"und",
            u"offset": 100,
            u"synced": false,
            u"line": [ {
              u"value": u"It's bugging me"
            }, {
              u"value": u"Grating me"
            }, {
              u"value": u"And twisting me around..."
            } ] }
         ]
        }
        """
        methodName = 'getLyricsBySongId'

        q = self._getQueryDict({'id': song_id})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def jukeboxControl(self, action, index=None, sids=None, gain=None,
            offset=None):
        """
        since: 1.2.0

        NOTE: Some options were added as of API version 1.7.0

        Controls the jukebox, i.e., playback directly on the server's
        audio hardware. Note: The user must be authorized to control
        the jukebox

        action:str      The operation to perform. Must be one of: get,
                        start, stop, skip, add, clear, remove, shuffle,
                        setGain, status (added in API 1.7.0),
                        set (added in API 1.7.0)
        index:int       Used by skip and remove. Zero-based index of the
                        song to skip to or remove.
        sids:str        Used by "add" and "set". ID of song to add to the
                        jukebox playlist. Use multiple id parameters to
                        add many songs in the same request.  Whether you
                        are passing one song or many into this, this
                        parameter MUST be a list
        gain:float      Used by setGain to control the playback volume.
                        A float value between 0.0 and 1.0
        offset:int      (added in API 1.7.0) Used by "skip".  Start playing
                        this many seconds into the track.
        """
        methodName = 'jukeboxControl'

        if sids is None:
            sids = []

        q = self._getQueryDict({'action': action, 'index': index,
            'gain': gain, 'offset': offset})

        res = None
        if action == 'add':
            # We have to deal with the sids
            if not (isinstance(sids, list) or isinstance(sids, tuple)):
                raise errors.ArgumentError('If you are adding songs, "sids" must '
                    'be a list or tuple!')
            res = self._doRequestWithList(methodName, 'id', sids, q)
        else:
            res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def getPodcasts(self, incEpisodes=True, pid=None):
        """
        since: 1.6.0

        Returns all podcast channels the server subscribes to and their
        episodes.

        incEpisodes:bool    (since: 1.9.0) Whether to include Podcast
                            episodes in the returned result.
        pid:str             (since: 1.9.0) If specified, only return
                            the Podcast channel with this ID.

        Returns a list of media.PodcastChannel
        """
        methodName = 'getPodcasts'

        q = self._getQueryDict({'includeEpisodes': incEpisodes,
            'id': pid})
        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return [PodcastChannel(entry) for entry in dres['podcasts']['channel']]


    def getShares(self):
        """
        since: 1.6.0

        Returns information about shared media this user is allowed to manage

        Note that entry can be either a single dict or a list of dicts

        Returns a dict like the following:

        {u'status': u'ok',
         u'version': u'1.6.0',
         u'xmlns': u'http://subsonic.org/restapi',
         u'shares': {u'share': [
             {u'created': u'2011-08-18T10:01:35',
              u'entry': {u'artist': u'Alice In Chains',
                         u'coverArt': u'2f66696c65732f6d7033732f412d4d2f416c69636520496e20436861696e732f416c69636520496e20436861696e732f636f7665722e6a7067',
                         u'id': u'2f66696c65732f6d7033732f412d4d2f416c69636520496e20436861696e732f416c69636520496e20436861696e73',
                         u'isDir': True,
                         u'parent': u'2f66696c65732f6d7033732f412d4d2f416c69636520496e20436861696e73',
                         u'title': u'Alice In Chains'},
              u'expires': u'2012-08-18T10:01:35',
              u'id': 0,
              u'url': u'http://crustymonkey.subsonic.org/share/BuLbF',
              u'username': u'admin',
              u'visitCount': 0
             }]}
        }
        """
        methodName = 'getShares'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def createShare(self, shids=None, description=None, expires=None):
        """
        since: 1.6.0

        Creates a public URL that can be used by anyone to stream music
        or video from the Subsonic server. The URL is short and suitable
        for posting on Facebook, Twitter etc. Note: The user must be
        authorized to share (see Settings > Users > User is allowed to
        share files with anyone).

        shids:list[str]              A list of ids of songs, albums or videos
                                    to share.
        description:str             A description that will be displayed to
                                    people visiting the shared media
                                    (optional).
        expires:float               A timestamp pertaining to the time at
                                    which this should expire (optional)

        This returns a structure like you would get back from getShares()
        containing just your new share.
        """
        methodName = 'createShare'

        if shids is None:
            shids = []

        q = self._getQueryDict({'description': description,
            'expires': self._ts2milli(expires)})
        res = self._doRequestWithList(methodName, 'id', shids, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def updateShare(self, shid, description=None, expires=None):
        """
        since: 1.6.0

        Updates the description and/or expiration date for an existing share

        shid:str            The id of the share to update
        description:str     The new description for the share (optional).
        expires:float       The new timestamp for the expiration time of this
                            share (optional).
        """
        methodName = 'updateShare'

        q = self._getQueryDict({'id': shid, 'description': description,
            expires: self._ts2milli(expires)})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def deleteShare(self, shid):
        """
        since: 1.6.0

        Deletes an existing share

        shid:str        The id of the share to delete

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'deleteShare'

        q = self._getQueryDict({'id': shid})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def setRating(self, item_id, rating):
        """
        since: 1.6.0

        Sets the rating for a music file

        item_id:str          The id of the item (song/artist/album) to rate
        rating:int      The rating between 1 and 5 (inclusive), or 0 to remove
                        the rating

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'setRating'

        try:
            rating = int(rating)
        except Exception as exc:
            raise errors.ArgumentError('Rating must be an integer between 0 and 5: '
                '%r' % rating) from exc
        if rating < 0 or rating > 5:
            raise errors.ArgumentError('Rating must be an integer between 0 and 5: '
                '%r' % rating)

        q = self._getQueryDict({'id': item_id, 'rating': rating})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def getArtists(self):
        """
        since 1.8.0

        Similar to getIndexes(), but this method uses the ID3 tags to
        determine the artist

        Returns a list of media.Index
        """
        methodName = 'getArtists'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)

        return [Index(entry) for entry in dres['artists']['index']]


    def getArtist(self, artist_id):
        """
        since 1.8.0

        Returns the info (albums) for an artist.  This method uses
        the ID3 tags for organization

        artist_id:str      The artist ID

        Returns media.Artist
        """
        methodName = 'getArtist'

        q = self._getQueryDict({'id': artist_id})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return Artist(dres['artist'])


    def getAlbum(self, album_id):
        """
        since 1.8.0

        Returns the info and songs for an album.  This method uses
        the ID3 tags for organization

        album_id:str      The album ID

        Returns a media.Album
        """
        methodName = 'getAlbum'

        q = self._getQueryDict({'id': album_id})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return Album(dres['album'])


    def getSong(self, sid):
        """
        since 1.8.0

        Returns the info for a song.  This method uses the ID3
        tags for organization

        sid:str      The song ID

        Returns a media.Song
        """
        methodName = 'getSong'

        q = self._getQueryDict({'id': sid})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return Song(dres['song'])


    def getSong2(self, sid):
        """
        since 1.8.0

        Returns the info for a song.  This method uses the ID3
        tags for organization

        sid:str      The song ID

        Returns a media.Song
        """
        methodName = 'getSong'

        q = self._getQueryDict({'id': sid})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return Child(**dres['song'])


    def getVideos(self):
        """
        since 1.8.0

        Returns all video files

        Returns a dict like the following:
            {u'status': u'ok',
             u'version': u'1.8.0',
             u'videos': {u'video': {u'bitRate': 384,
                        u'contentType': u'video/x-matroska',
                        u'created': u'2012-08-26T13:36:44',
                        u'duration': 1301,
                        u'id': 130,
                        u'isDir': False,
                        u'isVideo': True,
                        u'path': u'South Park - 16x07 - Cartman Finds Love.mkv',
                        u'size': 287309613,
                        u'suffix': u'mkv',
                        u'title': u'South Park - 16x07 - Cartman Finds Love',
                        u'transcodedContentType': u'video/x-flv',
                        u'transcodedSuffix': u'flv'}},
             u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getVideos'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def getStarred(self, musicFolderId=None):
        """
        since 1.8.0

        musicFolderId:int   Only return dresults from the music folder
                            with the given ID. See getMusicFolders

        Returns a dict like the following:
            {u'artists': [media.Artist],
             u'albums': [media.Album],
             u'songs': [media.Song]}
        """
        methodName = 'getStarred'

        q = {}
        if musicFolderId:
            q['musicFolderId'] = musicFolderId

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        starred = dres['starred']
        ret = {}
        if 'artist' in starred:
            ret['artists'] = [Artist(entry) for entry in starred['artist']]
        else:
            ret['artists'] = []
        if 'album' in starred:
            ret['albums'] = [Album(entry) for entry in starred['album']]
        else:
            ret['albums'] = []
        if 'song' in starred:
            ret['songs'] = [Song(entry) for entry in starred['song']]
        else:
            ret['songs'] = []
        return ret


    def getStarred2(self, musicFolderId=None):
        """
        since 1.8.0

        musicFolderId:int   Only return dresults from the music folder
                            with the given ID. See getMusicFolders

        Returns starred songs, albums and artists like getStarred(),
        but this uses ID3 tags for organization

        Returns a dict like the following:
            {u'artists': [media.Artist],
             u'albums': [media.Album],
             u'songs': [media.Song]}
        """
        methodName = 'getStarred2'

        q = {}
        if musicFolderId:
            q['musicFolderId'] = musicFolderId

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        starred = dres['starred2']
        ret = {}
        if 'artist' in starred:
            ret['artists'] = [Artist(entry) for entry in starred['artist']]
        else:
            ret['artists'] = []
        if 'album' in starred:
            ret['albums'] = [Album(entry) for entry in starred['album']]
        else:
            ret['albums'] = []
        if 'song' in starred:
            ret['songs'] = [Song(entry) for entry in starred['song']]
        else:
            ret['songs'] = []
        return ret


    def updatePlaylist(self, lid, name=None, comment=None, songIdsToAdd=None,
            songIndexesToRemove=None):
        """
        since 1.8.0

        Updates a playlist.  Only the owner of a playlist is allowed to
        update it.

        lid:str                 The playlist id
        name:str                The human readable name of the playlist
        comment:str             The playlist comment
        songIdsToAdd:list       A list of song IDs to add to the playlist
        songIndexesToRemove:list    Remove the songs at the
                                    0 BASED INDEXED POSITIONS in the
                                    playlist, NOT the song ids.  Note that
                                    this is always a list.

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'updatePlaylist'

        if songIdsToAdd is None:
            songIdsToAdd = []

        if songIndexesToRemove is None:
            songIndexesToRemove = []

        q = self._getQueryDict({'playlistId': lid, 'name': name,
            'comment': comment})
        if not isinstance(songIdsToAdd, list) or isinstance(songIdsToAdd,
                tuple):
            songIdsToAdd = [songIdsToAdd]
        if not isinstance(songIndexesToRemove, list) or isinstance(
                songIndexesToRemove, tuple):
            songIndexesToRemove = [songIndexesToRemove]
        listMap = {'songIdToAdd': songIdsToAdd,
            'songIndexToRemove': songIndexesToRemove}
        res = self._doRequestWithLists(methodName, listMap, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def getAvatar(self, username):
        """
        since 1.8.0

        Returns the avatar for a user or None if the avatar does not exist

        username:str    The user to retrieve the avatar for

        Returns the requests.Response object for reading on success or raises
        and exception
        """
        methodName = 'getAvatar'

        q = {'username': username}

        res = self._doRequest(methodName, q)
        dres = self._handleBinRes(res)
        if isinstance(dres, dict):
            self._checkStatus(dres)
        return dres


    def star(self, sids=None, albumIds=None, artistIds=None):
        """
        since 1.8.0

        Attaches a star to songs, albums or artists

        sids:list       A list of song IDs to star
        albumIds:list   A list of album IDs to star.  Use this rather than
                        "sids" if the client access the media collection
                        according to ID3 tags rather than file
                        structure
        artistIds:list  The ID of an artist to star.  Use this rather
                        than sids if the client access the media
                        collection according to ID3 tags rather
                        than file structure

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'star'

        if sids is None:
            sids = []
        if albumIds is None:
            albumIds = []
        if artistIds is None:
            artistIds = []

        if not isinstance(sids, list) or isinstance(sids, tuple):
            sids = [sids]
        if not isinstance(albumIds, list) or isinstance(albumIds, tuple):
            albumIds = [albumIds]
        if not isinstance(artistIds, list) or isinstance(artistIds, tuple):
            artistIds = [artistIds]
        listMap = {'id': sids,
            'albumId': albumIds,
            'artistId': artistIds}
        res = self._doRequestWithLists(methodName, listMap)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def unstar(self, sids=None, albumIds=None, artistIds=None):
        """
        since 1.8.0

        Removes a star to songs, albums or artists.  Basically, the
        same as star in reverse

        sids:list       A list of song IDs to star
        albumIds:list   A list of album IDs to star.  Use this rather than
                        "sids" if the client access the media collection
                        according to ID3 tags rather than file
                        structure
        artistIds:list  The ID of an artist to star.  Use this rather
                        than sids if the client access the media
                        collection according to ID3 tags rather
                        than file structure

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'unstar'

        if sids is None:
            sids = []
        if albumIds is None:
            albumIds = []
        if artistIds is None:
            artistIds = []

        if not isinstance(sids, list) or isinstance(sids, tuple):
            sids = [sids]
        if not isinstance(albumIds, list) or isinstance(albumIds, tuple):
            albumIds = [albumIds]
        if not isinstance(artistIds, list) or isinstance(artistIds, tuple):
            artistIds = [artistIds]
        listMap = {'id': sids,
            'albumId': albumIds,
            'artistId': artistIds}
        res = self._doRequestWithLists(methodName, listMap)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def getGenres(self):
        """
        since 1.9.0

        Returns all genres
        """
        methodName = 'getGenres'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def getSongsByGenre(self, genre, count=10, offset=0, musicFolderId=None):
        """
        since 1.9.0

        Returns list of media.Songs in a given genre

        genre:str       The genre, as returned by getGenres()
        count:int       The maximum number of songs to return.  Max is 500
                        default: 10
        offset:int      The offset if you are paging.  default: 0
        musicFolderId:int   Only return dresults from the music folder
                            with the given ID. See getMusicFolders
        """
        methodName = 'getSongsByGenre'

        q = self._getQueryDict({'genre': genre,
            'count': count,
            'offset': offset,
            'musicFolderId': musicFolderId,
        })

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return [Song(entry) for entry in dres['songsByGenre']['song']]


    def hls (self, mid, bitrate=None):
        """
        since 1.8.0

        Creates an HTTP live streaming playlist for streaming video or
        audio HLS is a streaming protocol implemented by Apple and
        works by breaking the overall stream into a sequence of small
        HTTP-based file downloads. It's supported by iOS and newer
        versions of Android. This method also supports adaptive
        bitrate streaming, see the bitRate parameter.

        mid:str     The ID of the media to stream
        bitrate:str If specified, the server will attempt to limit the
                    bitrate to this value, in kilobits per second. If
                    this parameter is specified more than once, the
                    server will create a variant playlist, suitable
                    for adaptive bitrate streaming. The playlist will
                    support streaming at all the specified bitrates.
                    The server will automatically choose video dimensions
                    that are suitable for the given bitrates.
                    (since: 1.9.0) you may explicitly request a certain
                    width (480) and height (360) like so:
                    bitRate=1000@480x360

        Returns the raw m3u8 file as a string
        """
        methodName = 'hls'

        q = self._getQueryDict({'id': mid, 'bitrate': bitrate})
        res = self._doRequest(methodName, q)
        dres = self._handleBinRes(res)
        if isinstance(dres, dict):
            self._checkStatus(dres)
        return dres.read()


    def refreshPodcasts(self):
        """
        since: 1.9.0

        Tells the server to check for new Podcast episodes. Note: The user
        must be authorized for Podcast administration

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'refreshPodcasts'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def createPodcastChannel(self, url):
        """
        since: 1.9.0

        Adds a new Podcast channel.  Note: The user must be authorized
        for Podcast administration

        url:str     The URL of the Podcast to add

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'createPodcastChannel'

        q = {'url': url}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def deletePodcastChannel(self, pid):
        """
        since: 1.9.0

        Deletes a Podcast channel.  Note: The user must be authorized
        for Podcast administration

        pid:str         The ID of the Podcast channel to delete

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'deletePodcastChannel'

        q = {'id': pid}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def deletePodcastEpisode(self, pid):
        """
        since: 1.9.0

        Deletes a Podcast episode.  Note: The user must be authorized
        for Podcast administration

        pid:str         The ID of the Podcast episode to delete

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'deletePodcastEpisode'

        q = {'id': pid}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def downloadPodcastEpisode(self, pid):
        """
        since: 1.9.0

        Tells the server to start downloading a given Podcast episode.
        Note: The user must be authorized for Podcast administration

        pid:str         The ID of the Podcast episode to download

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'downloadPodcastEpisode'

        q = {'id': pid}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def getInternetRadioStations(self):
        """
        since: 1.9.0

        Returns all internet radio stations
        """
        methodName = 'getInternetRadioStations'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def createInternetRadioStation(self, streamUrl, name, homepageUrl=None):
        """
        since 1.16.0

        Create an internet radio station

        streamUrl:str   The stream URL for the station
        name:str        The user-defined name for the station
        homepageUrl:str The homepage URL for the station
        """
        methodName = 'createInternetRadioStation'

        q = self._getQueryDict({
            'streamUrl': streamUrl, 'name': name, 'homepageUrl': homepageUrl})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def updateInternetRadioStation(self, iid, streamUrl, name,
            homepageUrl=None):
        """
        since 1.16.0

        Create an internet radio station

        iid:str         The ID for the station
        streamUrl:str   The stream URL for the station
        name:str        The user-defined name for the station
        homepageUrl:str The homepage URL for the station
        """
        methodName = 'updateInternetRadioStation'

        q = self._getQueryDict({
            'id': iid, 'streamUrl': streamUrl, 'name': name,
            'homepageUrl': homepageUrl,
        })

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def deleteInternetRadioStation(self, iid):
        """
        since 1.16.0

        Create an internet radio station

        iid:str         The ID for the station
        """
        methodName = 'deleteInternetRadioStation'

        q = {'id': iid}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def getBookmarks(self):
        """
        since: 1.9.0

        Returns all bookmarks for this user.  A bookmark is a position
        within a media file
        """
        methodName = 'getBookmarks'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def createBookmark(self, mid, position, comment=None):
        """
        since: 1.9.0

        Creates or updates a bookmark (position within a media file).
        Bookmarks are personal and not visible to other users

        mid:str         The ID of the media file to bookmark.  If a bookmark
                        already exists for this file, it will be overwritten
        position:int    The position (in milliseconds) within the media file
        comment:str     A user-defined comment

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'createBookmark'

        q = self._getQueryDict({'id': mid, 'position': position,
            'comment': comment})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def deleteBookmark(self, mid):
        """
        since: 1.9.0

        Deletes the bookmark for a given file

        mid:str     The ID of the media file to delete the bookmark from.
                    Other users' bookmarks are not affected

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        methodName = 'deleteBookmark'

        q = {'id': mid}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def getArtistInfo(self, aid, count=20, includeNotPresent=False):
        """
        since: 1.11.0

        Returns artist info with biography, image URLS and similar artists
        using data from last.fm

        aid:str                 The ID of the artist, album or song
        count:int               The max number of similar artists to return
        includeNotPresent:bool  Whether to return artists that are not
                                present in the media library
        """
        methodName = 'getArtistInfo'

        q = {'id': aid, 'count': count,
            'includeNotPresent': includeNotPresent}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return ArtistInfo(dres['artistInfo'])


    def getArtistInfo2(self, aid, count=20, includeNotPresent=False):
        """
        since: 1.11.0

        Similar to getArtistInfo(), but organizes music according to ID3 tags

        aid:str                 The ID of the artist, album or song
        count:int               The max number of similar artists to return
        includeNotPresent:bool  Whether to return artists that are not
                                present in the media library
        """
        methodName = 'getArtistInfo2'

        q = {'id': aid, 'count': count,
            'includeNotPresent': includeNotPresent}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return ArtistInfo(dres['artistInfo2'])


    def getSimilarSongs(self, iid, count=50):
        """
        since 1.11.0

        Returns a random collection of songs from the given artist and
        similar artists, using data from last.fm. Typically used for
        artist radio features. As a list of media.Song

        iid:str     The artist, album, or song ID
        count:int   Max number of songs to return
        """
        methodName = 'getSimilarSongs'

        q = {'id': iid, 'count': count}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        if 'similarSongs' not in dres or 'song' not in dres['similarSongs']:
            return []
        return [Song(entry) for entry in dres['similarSongs']['song']]


    def getSimilarSongs2(self, iid, count=50):
        """
        since 1.11.0

        Similar to getSimilarSongs(), but organizes music according to
        ID3 tags

        iid:str     The artist, album, or song ID
        count:int   Max number of songs to return
        """
        methodName = 'getSimilarSongs2'

        q = {'id': iid, 'count': count}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        if 'similarSongs2' not in dres or 'song' not in dres['similarSongs2']:
            return []
        return [Song(entry) for entry in dres['similarSongs2']['song']]


    def savePlayQueue(self, qids, current=None, position=None):
        """
        since 1.12.0

        qid:list[int]       The list of song ids in the play queue
        current:int         The id of the current playing song
        position:int        The position, in milliseconds, within the current
                            playing song

        Saves the state of the play queue for this user. This includes
        the tracks in the play queue, the currently playing track, and
        the position within this track. Typically used to allow a user to
        move between different clients/apps while retaining the same play
        queue (for instance when listening to an audio book).
        """
        methodName = 'savePlayQueue'

        if not isinstance(qids, (tuple, list)):
            qids = [qids]

        q = self._getQueryDict({'current': current, 'position': position})

        res = self._doRequestWithLists(methodName, {'id': qids}, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def getPlayQueue(self):
        """
        since 1.12.0

        Returns the state of the play queue for this user (as set by
        savePlayQueue). This includes the tracks in the play queue,
        the currently playing track, and the position within this track.
        Typically used to allow a user to move between different
        clients/apps while retaining the same play queue (for instance
        when listening to an audio book).
        """
        methodName = 'getPlayQueue'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def getTopSongs(self, artist, count=50):
        """
        since 1.13.0

        Returns the top songs for a given artist as a List of media.Song

        artist:str      The artist to get songs for
        count:int       The number of songs to return
        """
        methodName = 'getTopSongs'

        q = {'artist': artist, 'count': count}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        if 'topSongs' not in dres or 'song' not in dres['topSongs']:
            return []
        return [Song(entry) for entry in dres['topSongs']['song']]


    def getNewestPodcasts(self, count=20):
        """
        since 1.13.0

        Returns the most recently published Podcast episodes as a list of media.PodcastEpisode

        count:int       The number of episodes to return
        """
        methodName = 'getNewestPodcasts'

        q = {'count': count}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        if 'newestPodcasts' not in dres or 'episode' not in dres['newestPodcasts']:
            return []
        return [PodcastEpisode(entry) for entry in dres['newestPodcasts']['episode']]


    def getVideoInfo(self, vid):
        """
        since 1.14.0

        Returns details for a video, including information about available
        audio tracks, subtitles (captions) and conversions.

        vid:int     The video ID
        """
        methodName = 'getVideoInfo'

        q = {'id': int(vid)}
        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def getAlbumInfo(self, aid):
        """
        since 1.14.0

        Returns the album notes, image URLs, etc., using data from last.fm

        aid:int     The album ID

        Returns media.AlbumInfo
        """
        methodName = 'getAlbumInfo'

        q = {'id': aid}
        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return AlbumInfo(dres['albumInfo'])


    def getAlbumInfo2(self, aid):
        """
        since 1.14.0

        Same as getAlbumInfo, but uses ID3 tags

        aid:int     The album ID

        Returns media.AlbumInfo
        """
        methodName = 'getAlbumInfo2'

        q = {'id': aid}
        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return AlbumInfo(dres['albumInfo'])


    def getCaptions(self, vid, fmt=None):
        """
        since 1.14.0

        Returns captions (subtitles) for a video.  Use getVideoInfo for a list
        of captions.

        vid:int         The ID of the video
        fmt:str         Preferred captions format ("srt" or "vtt")
        """
        methodName = 'getCaptions'

        q = self._getQueryDict({'id': int(vid), 'format': fmt})
        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    #
    # Private internal methods
    #
    def _getQueryDict(self, d):
        """
        Given a dictionary, it cleans out all the values set to None
        """
        for k, v in list(d.items()):
            if v is None:
                del d[k]
        return d


    def _getBaseQdict(self):
        qdict = {
            'f': 'json',
            'v': self._apiVersion,
            'c': self._appName,
            'u': self._username,
        }

        if self._legacyAuth:
            qdict['p'] = 'enc:%s' % self._hexEnc(self._rawPass)
        else:
            salt = self._getSalt()
            token = md5((self._rawPass + salt).encode('utf-8')).hexdigest()
            qdict.update({
                's': salt,
                't': token,
            })

        return qdict


    def _doRequest(self, methodName, query=None, is_stream=False):
        qdict = self._getBaseQdict()
        if query is not None:
            qdict.update(query)

        if self._useViews:
            methodName += '.view'
        url = f"{self._baseUrl}:{self._port}/{self._serverPath}/{methodName}"

        if self._useGET:
            res = requests.get(url, params=qdict, stream=is_stream, timeout=(30, 60))
        else:
            res = requests.post(url, data=qdict, stream=is_stream, timeout=(30, 60))

        return res


    def _doRequestWithList(self, methodName, listName, alist, query=None):
        """
        Like _getRequest, but allows appending a number of items with the
        same key (listName).  This bypasses the limitation of urlencode()
        """
        qdict = self._getBaseQdict()
        if query is not None:
            qdict.update(query)
        qdict[listName] = alist

        if self._useViews:
            methodName += '.view'
        url = f"{self._baseUrl}:{self._port}/{self._serverPath}/{methodName}"

        if self._useGET:
            res = requests.get(url, params=qdict, timeout=(30, 60))
        else:
            res = requests.post(url, data=qdict, timeout=(30, 60))

        return res


    def _doRequestWithLists(self, methodName, listMap, query=None):
        """
        Like _getRequestWithList(), but you must pass a dictionary
        that maps the listName to the list.  This allows for multiple
        list parameters to be used, like in updatePlaylist()

        methodName:str        The name of the method
        listMap:dict        A mapping of listName to a list of entries
        query:dict          The normal query dict
        """
        qdict = self._getBaseQdict()
        if query is not None:
            qdict.update(query)
        qdict.update(listMap)

        if self._useViews:
            methodName += '.view'

        url = f"{self._baseUrl}:{self._port}/{self._serverPath}/{methodName}"

        if self._useGET:
            res = requests.get(url, params=qdict, timeout=(60,300))
        else:
            res = requests.post(url, data=qdict, timeout=(60,300))

        return res


    def _handleInfoRes(self, res):
        # Returns a parsed dictionary version of the result
        res.raise_for_status()
        dres = res.json()
        return dres['subsonic-response']


    def _handleBinRes(self, res):
        res.raise_for_status()
        contType = res.headers['Content-Type'] if 'Content-Type' in res.headers else None

        if contType:
            if contType.startswith('text/html') or \
                    contType.startswith('application/json'):
                dres = res.json()
                return dres['subsonic-response']
        return res


    def _checkStatus(self, result):
        if result['status'] == 'ok':
            return True
        elif result['status'] == 'failed':
            exc = errors.getExcByCode(result['error']['code'])
            raise exc(result['error']['message'])


    def _hexEnc(self, raw):
        """
        Returns a "hex encoded" string per the Subsonic api docs

        raw:str     The string to hex encode
        """
        ret = ''
        for c in raw:
            ret += '%02X' % ord(c)
        return ret


    def _ts2milli(self, ts):
        """
        For whatever reason, Subsonic uses timestamps in milliseconds since
        the unix epoch.  I have no idea what need there is of this precision,
        but this will just multiply the timestamp times 1000 and return the int
        """
        if ts is None:
            return None
        return int(ts * 1000)


    def _fixLastModified(self, data):
        """
        This will recursively walk through a data structure and look for
        a dict key/value pair where the key is "lastModified" and change
        the shitty java millisecond timestamp to a real unix timestamp
        of SECONDS since the unix epoch.  JAVA SUCKS!
        """
        if isinstance(data, dict):
            for k, v in list(data.items()):
                if k == 'lastModified':
                    data[k] = int(v) / 1000.0
                    return
                elif isinstance(v, (tuple, list, dict)):
                    return self._fixLastModified(v)
        elif isinstance(data, (list, tuple)):
            for item in data:
                if isinstance(item, (list, tuple, dict)):
                    return self._fixLastModified(item)


    def _process_netrc(self, use_netrc):
        """
        The use_netrc var is either a boolean, which means we should use
        the user's default netrc, or a string specifying a path to a
        netrc formatted file

        use_netrc:bool|str      Either set to True to use the user's default
                                netrc file or a string specifying a specific
                                netrc file to use
        """
        if not use_netrc:
            raise errors.CredentialError('useNetrc must be either a boolean "True" '
                'or a string representing a path to a netrc file, '
                'not {0}'.format(repr(use_netrc)))
        if isinstance(use_netrc, bool) and use_netrc:
            self._netrc = netrc()
        else:
            # This should be a string specifying a path to a netrc file
            self._netrc = netrc(os.path.expanduser(use_netrc))
        auth = self._netrc.authenticators(self._hostname)
        if not auth:
            raise errors.CredentialError('No machine entry found for {0} in '
                'your netrc file'.format(self._hostname))

        # If we get here, we have credentials
        self._username = auth[0]
        self._rawPass = auth[2]


    def _getSalt(self, length=16):
        salt = md5(os.urandom(100)).hexdigest()
        return salt[:length]

