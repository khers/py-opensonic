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
from warnings import deprecated

from requests import get, post, Response

from . import errors
from .media.media_types import (Album, AlbumID3, AlbumInfo, ArtistID3, ArtistInfo, ArtistInfo2,
                                Artists, Bookmark, ChatMessage, Child, Directory, Error, Genre,
                                Indexes, InternetRadioStation, JukeboxPlaylist, JukeboxStatus,
                                Lyrics, MusicFolder, NowPlayingEntry, OpenSubsonicExtension,
                                Playlist, PlayQueue, PodcastChannel, PodcastEpisode, ScanStatus,
                                SearchResult2, SearchResult3, Share, Starred, Starred2,
                                StructuredLyrics, User)

API_VERSION = '1.16.1'


def pretty_print_post(req: str) -> None:
    print('{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join(f'{k}: {v}' for k, v in req.headers.items()),
        req.body,
    ))


class Connection:
    def __init__(self, baseUrl: str, username: str=None, password:str=None,
                port: int=4040, serverPath: str='', appName: str='py-opensonic',
                apiVersion: str=API_VERSION, insecure: bool=False, useNetrc: str=None,
                legacyAuth: bool=False, useGET: bool=False, useViews: bool=True):
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
    def setBaseUrl(self, url: str) -> None:
        self._baseUrl = url
        if '://' in url:
            self._hostname = url.split('://')[1].strip()
        else:
            self._hostname = url
    baseUrl = property(lambda s: s._baseUrl, setBaseUrl)


    def setPort(self, port: int) -> None:
        self._port = port
    port = property(lambda s: s._port, setPort)


    def setUsername(self, username: str) -> None:
        self._username = username
    username = property(lambda s: s._username, setUsername)


    def setPassword(self, password: str) -> None:
        self._rawPass = password
        # Redo the opener with the new creds
    password = property(lambda s: s._rawPass, setPassword)


    apiVersion = property(lambda s: s._apiVersion)


    def setAppName(self, appName: str) -> None:
        self._appName = appName
    appName = property(lambda s: s._appName, setAppName)


    def setServerPath(self, path: str) -> None:
        sep = ''
        if path != '' and not path.endswith('/'):
            sep = '/'
        self._serverPath = f"{path}{sep}rest".strip('/')
    serverPath = property(lambda s: s._serverPath, setServerPath)


    def setInsecure(self, insecure: bool) -> None:
        self._insecure = insecure
    insecure = property(lambda s: s._insecure, setInsecure)


    def setLegacyAuth(self, lauth: bool) -> None:
        self._legacyAuth = lauth
    legacyAuth = property(lambda s: s._legacyAuth, setLegacyAuth)


    def setGET(self, get: bool) -> None:
        self._useGET = get
    useGET = property(lambda s: s._useGET, setGET)


    # API methods
    def ping(self) -> bool:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/ping/

        Returns a boolean True if the server is alive, raises the returned error
        """
        methodName = 'ping'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        if dres['status'] == 'ok':
            return True
        elif dres['status'] == 'failed':
            err = Error.from_dict(dres['error'])
            exc = errors.getExcByCode(err.code)
            raise exc(err.message)
        return False


    def getLicense(self) -> dict:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/getlicense/

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
    

    def getOpenSubsonicExtensions(self) -> OpenSubsonicExtension:
        """
        since OpenSubsonic 1

        https://opensubsonic.netlify.app/docs/endpoints/getopensubsonicextensions/

        List the OpenSubsonic extensions supported by this server.

        Returns a list of media.OpenSubsonicExtenstion
        """
        methodName = 'getOpenSubsonicExtensions'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        print(dres)
        return [OpenSubsonicExtension.from_dict(o) for o in dres['openSubsonicExtensions']]


    def getScanStatus(self) -> ScanStatus:
        """
        since: 1.15.0

        https://opensubsonic.netlify.app/docs/endpoints/getscanstatus/

        returns the current status for media library scanning.
        takes no extra parameters.

        returns a media.ScanStatus

        'scanning' changes to false when a scan is complete
        'count' is the total number of items to be scanned
        """
        methodName = 'getScanStatus'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return ScanStatus.from_dict(dres['scanstatus'])


    def startScan(self) -> ScanStatus:
        """
        since: 1.15.0

        https://opensubsonic.netlify.app/docs/endpoints/startscan/

        Initiates a rescan of the media libraries.
        Takes no extra parameters.

        returns a media.ScanStatus

        'scanning' changes to false when a scan is complete
        'count' starts a 0 and ends at the total number of items scanned

        """
        methodName = 'startScan'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return ScanStatus.from_dict(dres['scanstatus'])


    def getMusicFolders(self) -> list[MusicFolder]:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/getmusicfolders/

        Returns all configured music folders

        Returns a List of media.MusicFolder
        """
        methodName = 'getMusicFolders'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return [MusicFolder.from_dict(f) for f in dres["musicFolders"]]


    def getNowPlaying(self) -> list[NowPlayingEntry]:
        """
        since: 1.0.0

        Returns what is currently being played by all users

        Returns a list of media.NowPlayingEntry
        """
        methodName = 'getNowPlaying'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return [NowPlayingEntry.from_dict(n) for n in dres['nowPlaying']['entry']]


    def getIndexes(self, musicFolderId: int=None, ifModifiedSince: int=None) -> Indexes:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/getindexes/

        Returns an indexed structure of all artists

        musicFolderId:int       If this is specified, it will only return
                                artists for the given folder ID from
                                the getMusicFolders call
        ifModifiedSince:int     If specified, return a result if the artist
                                collection has changed since the given
                                unix timestamp

        Returns a media.Indexes

        """
        methodName = 'getIndexes'

        q = self._getQueryDict({'musicFolderId': musicFolderId,
            'ifModifiedSince': self._ts2milli(ifModifiedSince)})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return Indexes.from_dict(dres['indexes'])


    def getMusicDirectory(self, mid: str) -> Directory:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/getindexes/ 

        Returns a listing of all files in a music directory.  Typically used
        to get a list of albums for an artist or list of songs for an album.

        mid:str     The string ID value which uniquely identifies the
                    folder.  Obtained via calls to getIndexes or
                    getMusicDirectory.  REQUIRED

        Returns a media.Directory
        """
        methodName = 'getMusicDirectory'

        res = self._doRequest(methodName, {'id': mid})
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return Directory.from_dict(dres['directory'])


    @deprecated("The search method has been deprecated since 1.4.0, use search[2|3] instead")
    def search(self, artist=None, album=None, title=None, any=None,
            count=20, offset=0, newerThan=None):
        """
        since: 1.0.0

        DEPRECATED SINCE API 1.4.0!  USE search2() INSTEAD!
        """
        raise NotImplementedError("search is deprecated in favor of search2 or search3")


    def search2(self, query: str, artistCount: int=20, artistOffset: int=0,
                albumCount: int=20, albumOffset: int=0, songCount: int=20,
                songOffset: int=0, musicFolderId: int=None) -> SearchResult2:
        """
        since: 1.4.0

        https://opensubsonic.netlify.app/docs/endpoints/search2/

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

        Returns a media.SearchResult2
        """
        methodName = 'search2'

        q = self._getQueryDict({'query': query, 'artistCount': artistCount,
            'artistOffset': artistOffset, 'albumCount': albumCount,
            'albumOffset': albumOffset, 'songCount': songCount,
            'songOffset': songOffset, 'musicFolderId': musicFolderId})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return SearchResult2.from_dict(dres['searchResult2'])


    def search3(self, query: str, artistCount: int=20, artistOffset: int=0,
                albumCount: int=20, albumOffset: int=0, songCount: int=20,
                songOffset: int=0, musicFolderId: int=None) -> SearchResult3:
        """
        since: 1.8.0

        Works the same way as search2, but uses ID3 tags for
        organization

        https://opensubsonic.netlify.app/docs/endpoints/search3/

        query:str           The search query
        artistCount:int     Max number of artists to return [default: 20]
        artistOffset:int    Search offset for artists (for paging) [default: 0]
        albumCount:int      Max number of albums to return [default: 20]
        albumOffset:int     Search offset for albums (for paging) [default: 0]
        songCount:int       Max number of songs to return [default: 20]
        songOffset:int      Search offset for songs (for paging) [default: 0]
        musicFolderId:int   Only return dresults from the music folder
                            with the given ID. See getMusicFolders

        Returns a media.SearchResult3
        """
        methodName = 'search3'

        q = self._getQueryDict({'query': query, 'artistCount': artistCount,
            'artistOffset': artistOffset, 'albumCount': albumCount,
            'albumOffset': albumOffset, 'songCount': songCount,
            'songOffset': songOffset, 'musicFolderId': musicFolderId})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return SearchResult3.from_dict(dres['searchResult3'])


    def getPlaylists(self, username: str=None) -> list[Playlist]:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/getplaylists/

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
        return [Playlist.from_dict(entry) for entry in dres['playlists']['playlist']]


    def getPlaylist(self, pid: str) -> Playlist:
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
        return Playlist.from_dict(dres['playlist'])


    def createPlaylist(self, playlistId: str=None, name: str=None,
                       songIds: list[str]=None) -> bool:
        """
        since: 1.2.0

        https://opensubsonic.netlify.app/docs/endpoints/createplaylist/

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


    def deletePlaylist(self, pid: str) -> bool:
        """
        since: 1.2.0

        https://opensubsonic.netlify.app/docs/endpoints/deleteplaylist/

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


    def download(self, sid: str) -> Response:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/download/

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


    def stream(self, sid: str, maxBitRate: int=0, tformat: str=None,
               timeOffset: int=None, size: str=None,
               estimateContentLength: bool=False, converted: bool=False) -> Response:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/stream/

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


    def getCoverArt(self, aid: str, size: int=None) -> Response:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/getcoverart/

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


    def scrobble(self, sid: str, submission: bool=True, listenTime: int=None) -> bool:
        """
        since: 1.5.0

        https://opensubsonic.netlify.app/docs/endpoints/scrobble/

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


    def changePassword(self, username: str, password: str) -> bool:
        """
        since: 1.1.0

        https://opensubsonic.netlify.app/docs/endpoints/changepassword/

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


    def getUser(self, username: str) -> User:
        """
        since: 1.3.0

        https://opensubsonic.netlify.app/docs/endpoints/getuser/

        Get details about a given user, including which auth roles it has.
        Can be used to enable/disable certain features in the client, such
        as jukebox control

        username:str        The username to retrieve.  You can only retrieve
                            your own user unless you have admin privs.

        Returns a media.User
        """
        methodName = 'getUser'

        q = {'username': username}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return User.from_dict(dres['user'])


    def getUsers(self) -> list[User]:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getusers/

        Gets a list of users

        returns a list of media.User

        """
        methodName = 'getUsers'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return [User.from_dict(u) for u in dres['users']['user']]


    def createUser(self, username: str, password: str, email: str,
            ldapAuthenticated: bool=False, adminRole: bool=False,
            settingsRole: bool=True, streamRole: bool=True, jukeboxRole: bool=False,
            downloadRole: bool=False, uploadRole: bool=False,
            playlistRole: bool=False, coverArtRole: bool=False,
            commentRole: bool=False, podcastRole: bool=False, shareRole: bool=False,
            videoConversionRole: bool=False, musicFolderId: int=None) -> bool:
        """
        since: 1.1.0

        https://opensubsonic.netlify.app/docs/endpoints/createuser/

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


    def updateUser(self, username: str,  password: str=None, email: str=None,
            ldapAuthenticated: bool=False, adminRole: bool=False,
            settingsRole: bool=True, streamRole: bool=True, jukeboxRole: bool=False,
            downloadRole: bool=False, uploadRole: bool=False,
            playlistRole: bool=False, coverArtRole: bool=False,
            commentRole: bool=False, podcastRole: bool=False, shareRole: bool=False,
            videoConversionRole: bool=False, musicFolderId: int=None,
            maxBitRate: int=0) -> bool:
        """
        since 1.10.1

        https://opensubsonic.netlify.app/docs/endpoints/updateuser/

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


    def deleteUser(self, username: str) -> bool:
        """
        since: 1.3.0

        https://opensubsonic.netlify.app/docs/endpoints/deleteuser/

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


    def getChatMessages(self, since: int=1) -> list[ChatMessage]:
        """
        since: 1.2.0

        https://opensubsonic.netlify.app/docs/endpoints/getchatmessages/

        Returns the current visible (non-expired) chat messages.

        since:int       Only return messages newer than this timestamp

        NOTE: All times returned are in MILLISECONDS since the Epoch, not
              seconds!

        Returns a list of media.ChatMessage
        """
        methodName = 'getChatMessages'

        q = {'since': self._ts2milli(since)}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return [ChatMessage.from_dict(dres['chatMessages']['chatMessage'])]


    def addChatMessage(self, message: str) -> bool:
        """
        since: 1.2.0

        https://opensubsonic.netlify.app/docs/endpoints/addchatmessage/

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


    def getAlbumList(self, ltype: str, size: int=10, offset: int=0, fromYear: int=None,
            toYear: int=None, genre: str=None, musicFolderId: str=None) -> list[Album]:
        """
        since: 1.2.0

        https://opensubsonic.netlify.app/docs/endpoints/getalbumlist/

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
        return [Album.from_dict(entry) for entry in dres['albumList']['album']]


    def getAlbumList2(self, ltype: str, size: int=10, offset: int=0,
                      fromYear: int=None, toYear: int=None,
                      genre: str=None) -> list[AlbumID3]:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getalbumlist2/

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
        return [AlbumID3.from_dict(entry) for entry in dres['albumList2']['album']]


    def getRandomSongs(self, size: int=10, genre: str=None, fromYear: int=None,
            toYear: int=None, musicFolderId: str=None) -> list[Child]:
        """
        since 1.2.0

        Returns random songs matching the given criteria

        size:int            The max number of songs to return. Max 500
        genre:str           Only return songs from this genre
        fromYear:int        Only return songs after or in this year
        toYear:int          Only return songs before or in this year
        musicFolderId:str   Only return songs in the music folder with the
                            given ID.  See getMusicFolders

        Returns a list of media.Child
        """
        methodName = 'getRandomSongs'

        q = self._getQueryDict({'size': size, 'genre': genre,
            'fromYear': fromYear, 'toYear': toYear,
            'musicFolderId': musicFolderId})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return [Child.from_dict(entry) for entry in dres['randomSongs']['song']]


    def getLyrics(self, artist: str=None, title: str=None) -> Lyrics:
        """
        since: 1.2.0

        https://opensubsonic.netlify.app/docs/endpoints/getlyrics/

        Searches for and returns lyrics for a given song

        artist:str      The artist name
        title:str       The song title

        Returns a 

        """
        methodName = 'getLyrics'

        q = self._getQueryDict({'artist': artist, 'title': title})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return Lyrics.from_dict(dres['lyrics'])
    

    def getLyricsBySongId(self, song_id: str) -> list[StructuredLyrics]:
        """
        Since Open Subsonic ver 1

        https://opensubsonic.netlify.app/docs/endpoints/getlyricsbysongid/

        Retrieves all structured lyrics from the server for a given song.
        The lyrics can come from embedded tags (SYLT/USLT), LRC file/text
        file, or any other external source.

        id:str          The id of the requested songA

        Returns a list of media.StructuredLyrics
        """
        methodName = 'getLyricsBySongId'

        q = self._getQueryDict({'id': song_id})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return [StructuredLyrics.from_dict(l) for l in dres['lyricsList']['structuredLyrics']]


    def jukeboxControl(self, action:str, index: int=None, sids: str=None,
                       gain: float=None, offset: int=None) -> JukeboxStatus|JukeboxPlaylist:
        """
        since: 1.2.0

        https://opensubsonic.netlify.app/docs/endpoints/jukeboxcontrol/

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

        Returns a media.JukeboxPlaylist if action == 'get', JukeboxStatus otherwise
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

        if action == 'get':
            return JukeboxPlaylist.from_dict(dres['jukeboxPlaylist'])

        return JukeboxStatus.from_dict(dres['jukeboxStatus'])


    def getPodcasts(self, incEpisodes: bool=True, pid: str=None) -> list[PodcastChannel]:
        """
        since: 1.6.0

        https://opensubsonic.netlify.app/docs/endpoints/getpodcasts/

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
        return [PodcastChannel.from_dict(entry) for entry in dres['podcasts']['channel']]


    def getShares(self) -> list[Share]:
        """
        since: 1.6.0

        https://opensubsonic.netlify.app/docs/endpoints/getshares/

        Returns information about shared media this user is allowed to manage

        Note that entry can be either a single dict or a list of dicts

        Returns a list of media.Share
        """
        methodName = 'getShares'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return [Share.from_dict(s) for s in dres['shares']['share']]


    def createShare(self, shids: list[str]=None, description: str=None, expires: float=None) -> Share:
        """
        since: 1.6.0

        https://opensubsonic.netlify.app/docs/endpoints/createshare/

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

        This returns a media.Share
        """
        methodName = 'createShare'

        if shids is None:
            shids = []

        q = self._getQueryDict({'description': description,
            'expires': self._ts2milli(expires)})
        res = self._doRequestWithList(methodName, 'id', shids, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return Share.from_dict(dres['shares']['share'][0])


    def updateShare(self, shid: str, description: str=None, expires: float=None) -> bool:
        """
        since: 1.6.0

        https://opensubsonic.netlify.app/docs/endpoints/updateshare/

        Updates the description and/or expiration date for an existing share

        shid:str            The id of the share to update
        description:str     The new description for the share (optional).
        expires:float       The new timestamp for the expiration time of this
                            share (optional).

        Returns True on success
        """
        methodName = 'updateShare'

        q = self._getQueryDict({'id': shid, 'description': description,
            expires: self._ts2milli(expires)})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def deleteShare(self, shid: str) -> bool:
        """
        since: 1.6.0

        https://opensubsonic.netlify.app/docs/endpoints/deleteshare/

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


    def setRating(self, item_id: str, rating: int) -> bool:
        """
        since: 1.6.0

        https://opensubsonic.netlify.app/docs/endpoints/setrating/

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
            raise errors.ArgumentError(f'Rating must be an integer between 0 and 5: {rating}') from exc
        if rating < 0 or rating > 5:
            raise errors.ArgumentError(f'Rating must be an integer between 0 and 5: {rating}')

        q = self._getQueryDict({'id': item_id, 'rating': rating})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def getArtists(self) -> Artists:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getartists/

        Similar to getIndexes(), but this method uses the ID3 tags to
        determine the artist

        Returns a media.Artists
        """
        methodName = 'getArtists'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)

        return Artists.from_dict(dres['artists'])


    def getArtist(self, artist_id: str) -> ArtistID3:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getartist/

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
        return ArtistID3.from_dict(dres['artist'])


    def getAlbum(self, album_id: str) -> AlbumID3:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getalbum/

        Returns the info and songs for an album.  This method uses
        the ID3 tags for organization

        album_id:str      The album ID

        Returns a media.AlbumID3
        """
        methodName = 'getAlbum'

        q = self._getQueryDict({'id': album_id})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return AlbumID3.from_dict(dres['album'])


    def getSong(self, sid: str) -> Child:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getsong/

        Returns the info for a song.  This method uses the ID3
        tags for organization

        sid:str      The song ID

        Returns a media.Child
        """
        methodName = 'getSong'

        q = self._getQueryDict({'id': sid})

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return Child.from_dict(dres['song'])


    def getVideos(self) -> dict:
        """
        since 1.8.0

        Returns all video files

        Returns a dict
        """
        methodName = 'getVideos'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return dres


    def getStarred(self, musicFolderId: str=None) -> Starred:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getstarred/

        musicFolderId:str   Only return dresults from the music folder
                            with the given ID. See getMusicFolders

        Returns a media.Starred
        """
        methodName = 'getStarred'

        q = {}
        if musicFolderId:
            q['musicFolderId'] = musicFolderId

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return Starred.from_dict(dres['starred'])


    def getStarred2(self, musicFolderId: str=None) -> Starred2:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getstarred2/

        musicFolderId:int   Only return dresults from the music folder
                            with the given ID. See getMusicFolders

        Returns starred songs, albums and artists like getStarred(),
        but this uses ID3 tags for organization

        Returns a media.Starred2
        """
        methodName = 'getStarred2'

        q = {}
        if musicFolderId:
            q['musicFolderId'] = musicFolderId

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return Starred2.from_dict(dres['starred2'])


    def updatePlaylist(self, lid: str, name: str=None, comment: str=None,
                       songIdsToAdd: list[str]=None,
                       songIndexesToRemove: list[int]=None) -> bool:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/updateplaylist/

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


    def getAvatar(self, username: str) -> Response:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getavatar/

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


    def star(self, sids: list[str]=None, albumIds: list[str]=None, artistIds: list[str]=None) -> bool:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/star/

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


    def unstar(self, sids: list[str]=None, albumIds: list[str]=None, artistIds: list[str]=None) -> bool:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/unstar/

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


    def getGenres(self) -> list[Genre]:
        """
        since 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/getgenres/

        Returns all genres
        """
        methodName = 'getGenres'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return [Genre.from_dict(g) for g in dres['genres']['genre']]


    def getSongsByGenre(self, genre: str, count: int=10, offset: int=0, musicFolderId: str=None) -> list[Child]:
        """
        since 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/getsongsbygenre/

        Returns list of media.Child in a given genre

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
        return [Child.from_dict(entry) for entry in dres['songsByGenre']['song']]


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


    def refreshPodcasts(self) -> bool:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/refreshpodcasts/

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


    def createPodcastChannel(self, url: str) -> bool:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/createpodcastchannel/

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


    def deletePodcastChannel(self, pid: str) -> bool:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/deletepodcastchannel/

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


    def deletePodcastEpisode(self, pid: str) -> bool:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/deletepodcastepisode/

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


    def downloadPodcastEpisode(self, pid: str) -> bool:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/downloadpodcastepisode/

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


    def getInternetRadioStations(self) -> list[InternetRadioStation]:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/getinternetradiostations/

        Returns all internet radio stations
        """
        methodName = 'getInternetRadioStations'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return [InternetRadioStation.from_dict(i) for i in dres['internetRadioStations']['internetRadioStation']]


    def createInternetRadioStation(self, streamUrl: str, name: str, homepageUrl: str=None) -> bool:
        """
        since 1.16.0

        https://opensubsonic.netlify.app/docs/endpoints/createinternetradiostation/

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
        return True


    def updateInternetRadioStation(self, iid: str, streamUrl: str, name: str,
            homepageUrl: str=None) -> bool:
        """
        since 1.16.0

        https://opensubsonic.netlify.app/docs/endpoints/updateinternetradiostation/

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
        return True


    def deleteInternetRadioStation(self, iid: str) -> bool:
        """
        since 1.16.0

        https://opensubsonic.netlify.app/docs/endpoints/deleteinternetradiostation/

        Create an internet radio station

        iid:str         The ID for the station
        """
        methodName = 'deleteInternetRadioStation'

        q = {'id': iid}

        res = self._doRequest(methodName, q)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return True


    def getBookmarks(self) -> list[Bookmark]:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/getbookmarks/

        Returns all bookmarks for this user.  A bookmark is a position
        within a media file
        """
        methodName = 'getBookmarks'

        res = self._doRequest(methodName)
        dres = self._handleInfoRes(res)
        self._checkStatus(dres)
        return [Bookmark.from_dict(b) for b in dres['bookmarks']['bookmark']]


    def createBookmark(self, mid: str, position: int, comment: str=None) -> bool:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/createbookmark/

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


    def deleteBookmark(self, mid: str) -> bool:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/deletebookmark/

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


    def getArtistInfo(self, aid: str, count: int=20, includeNotPresent: bool=False) -> ArtistInfo:
        """
        since: 1.11.0

        https://opensubsonic.netlify.app/docs/endpoints/getartistinfo/

        Returns a media.ArtistInfo

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
        return ArtistInfo.from_dict(dres['artistInfo'])


    def getArtistInfo2(self, aid: str, count: int=20, includeNotPresent: bool=False) -> ArtistInfo2:
        """
        since: 1.11.0

        https://opensubsonic.netlify.app/docs/endpoints/getartistinfo2/

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
        return ArtistInfo2.from_dict(dres['artistInfo2'])


    def getSimilarSongs(self, iid: str, count: int=50) -> list[Child]:
        """
        since 1.11.0

        https://opensubsonic.netlify.app/docs/endpoints/getsimilarsongs/

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
        return [Child.from_dict(entry) for entry in dres['similarSongs']['song']]


    def getSimilarSongs2(self, iid: str, count: int=50) -> list[Child]:
        """
        since 1.11.0

        https://opensubsonic.netlify.app/docs/endpoints/getsimilarsongs2/

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
        return [Child.from_dict(entry) for entry in dres['similarSongs2']['song']]


    def savePlayQueue(self, qids, current=None, position=None) -> bool:
        """
        since 1.12.0

        https://opensubsonic.netlify.app/docs/endpoints/saveplayqueue/

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
        return True


    def getPlayQueue(self) -> PlayQueue:
        """
        since 1.12.0

        https://opensubsonic.netlify.app/docs/endpoints/getplayqueue/

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
        return PlayQueue.from_dict(dres['playQueue'])


    def getTopSongs(self, artist: str, count: int=50) -> list[Child]:
        """
        since 1.13.0

        https://opensubsonic.netlify.app/docs/endpoints/gettopsongs/

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
        return [Child.from_dict(entry) for entry in dres['topSongs']['song']]


    def getNewestPodcasts(self, count: int=20) -> list[PodcastEpisode]:
        """
        since 1.13.0

        https://opensubsonic.netlify.app/docs/endpoints/getnewestpodcasts/

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
        return [PodcastEpisode.from_dict(entry) for entry in dres['newestPodcasts']['episode']]


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


    def getAlbumInfo(self, aid: str) -> AlbumInfo:
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
        return AlbumInfo.from_dict(dres['albumInfo'])


    def getAlbumInfo2(self, aid: str) -> AlbumInfo:
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
        return AlbumInfo.from_dict(dres['albumInfo'])


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
    def _getQueryDict(self, d: dict) -> dict:
        """
        Given a dictionary, it cleans out all the values set to None
        """
        for k, v in list(d.items()):
            if v is None:
                del d[k]
        return d


    def _getBaseQdict(self) -> dict:
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


    def _doRequest(self, methodName: str, query: dict=None, is_stream: bool=False) -> Response:
        qdict = self._getBaseQdict()
        if query is not None:
            qdict.update(query)

        if self._useViews:
            methodName += '.view'
        url = f"{self._baseUrl}:{self._port}/{self._serverPath}/{methodName}"

        if self._useGET:
            res = get(url, params=qdict, stream=is_stream, timeout=(30, 60))
        else:
            res = post(url, data=qdict, stream=is_stream, timeout=(30, 60))

        return res


    def _doRequestWithList(self, methodName: str, listName: str, alist: list,
                           query: dict=None) -> Response:
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
            res = get(url, params=qdict, timeout=(30, 60))
        else:
            res = post(url, data=qdict, timeout=(30, 60))

        return res


    def _doRequestWithLists(self, methodName: str, listMap: dict, query: dict=None) -> Response:
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
            res = get(url, params=qdict, timeout=(60,300))
        else:
            res = post(url, data=qdict, timeout=(60,300))

        return res


    def _handleInfoRes(self, res: Response) -> dict:
        # Returns a parsed dictionary version of the result
        res.raise_for_status()
        dres = res.json()
        return dres['subsonic-response']


    def _handleBinRes(self, res: Response) -> Response:
        res.raise_for_status()
        contType = res.headers['Content-Type'] if 'Content-Type' in res.headers else None

        if contType:
            if contType.startswith('text/html') or \
                    contType.startswith('application/json'):
                dres = res.json()
                return dres['subsonic-response']
        return res


    def _checkStatus(self, result: dict) -> bool:
        if result['status'] == 'ok':
            return True
        elif result['status'] == 'failed':
            exc = errors.getExcByCode(result['error']['code'])
            raise exc(result['error']['message'])


    def _hexEnc(self, raw: str) -> str:
        """
        Returns a "hex encoded" string per the Subsonic api docs

        raw:str     The string to hex encode
        """
        ret = ''
        for c in raw:
            ret += '%02X' % ord(c)
        return ret


    def _ts2milli(self, ts: int) -> int:
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
    

