"""
Module contains classes for interacting with Telesocial REST API.

@copyright: Telesocial.com
@since: 2011-07-01
@version: 0.0.1
"""


# IMPORTS
import json
import urllib, urllib2

from collections import namedtuple

# META VARIABLES
__all__ = ['SimpleClient', 'RichClient']

# COMMON DEFINITIONS
Response = namedtuple('Response', 'code data')

class TelesocialError(Exception):
    """
    Base class for all errors originating from telesocial module.
    """
    def __init__(self, **kwargs):
        Exception.__init__(self)
        self.original = kwargs.pop('original', None)
        self.code = kwargs.pop('code', 500)
        self.message = kwargs.pop('message', 'Unknown error')

    def __str__(self):
        if self.original:
            return str(self.original)
        else:
            return '{0}: {1}'.format(self.code, self.message)

class TelesocialNetworkError(TelesocialError):
    def __init__(self, original):
        TelesocialError.__init__(self, original=original)

class TelesocialServiceError(TelesocialError):
    def __init__(self, code=None, message=None, **kwargs):
        TelesocialError.__init__(self, code=code, message=message, **kwargs)

def deep_find(data, key):
    """
    Returns value associated with `key` in arbitrary deep nested dictionaries.

    @type data: dict
    @param data: dict, possibly containing other dicts
    @type key: string
    @param key: key to find
    @return: value, associated with `key`
    """
    if key in data:
        return data[key]

    r = []
    for k in data:
        if isinstance(data[k], dict):
            a = deep_find(data[k], key)
            if a or a=='':
                r.append(a)
    return r[0]


# SIMPLE CLIENT
class SimpleClient:
    """
    Provides basic interface to Telesocial REST API.
    Contains roughly one-to-one implementation of API methods.

    @group NetworkId methods: network_id_*
    @group Conference methods: conference_*
    @group Media methods: media_*
    """
    def __init__(self, appkey, host='api4.bitmouth.com', https=False):
        """
        Constructor

        @type appkey: string
        @param appkey: telesocial application key
        @type host: string
        @param host: API server hostname
        @type https: bool
        @param https: specifies whether to use HTTPS or not
        """
        self.appkey = appkey
        self.host = ('https://' if https else 'http://') + host

    def _do_raw(self, uri, params=None, method='get'):
        uri = '{0}/api/rest/{1}'.format(self.host, uri)

        params = params or {}
        if not 'appkey' in params:
            params['appkey'] = self.appkey
        query_string = urllib.urlencode(params, True)
        data = None

        method = method.upper()
        if method in ['POST']: #, 'DELETE']:
            data = query_string
        else:
            uri += '?'+query_string

        print 'URI: {0}\nDATA: {1}'.format(uri, data)
        req = urllib2.Request(uri, data) #, method=method)

        code = 500
        data = ''
        try:
            f = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if hasattr(e, 'reason'):
                raise TelesocialNetworkError(e)
            elif hasattr(e, 'code'):
                code = e.code
                data = e.read()
        else:
            code = f.getcode()
            data = f.read()
            f.close()

        return (code, data)

    def _do(self, *args, **kwargs):
        code, data = self._do_raw(*args, **kwargs)
        try:
            js = json.loads(data)
            print(js)
            return Response(code, json.loads(data))
        except:
            return Response(code, {})


    def get(self, uri, query=None):
        return self._do(uri, query)

    def post(self, uri, query=None):
        return self._do(uri, query, 'post')

    def delete(self, uri, query=None):
        return self._do(uri, query, 'delete')


    def version(self):
        """
        Returns 3-tuple containing version components of server API implementation.

        @rtype: tuple
        @return: 3-tuple of version components, like (1, 3, 10)
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        code, data = self._do_raw('version')
        try:
            return tuple(map(int, data.split('.')))
        except Exception, e:
            raise TelesocialServiceError(None, 'Invalid version response: {0}'.format(data))


    def network_id_register(self, network_id, phone=None, greeting_id=None):
        """
        Registers (network_id, phone number) pair for new network_id, or relates existing
        network_id to current application.

        @type network_id: string
        @param network_id: the network ID to be registered
        @type phone: string
        @param phone: the phone number to relate to the network ID
        @type greeting_id: string
        @param greeting_id: the media ID of the greeting to play to the potential registrant
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        uri = 'registrant/'
        params = {'networkid': network_id}
        if phone:
            params['phone'] = phone
        if greeting_id:
            params['greetingid'] = greeting_id
        res = self.post(uri, params)

        if 200 <= res.code < 300:
            return res
        raise TelesocialServiceError(res.code, deep_find(res.data, 'message'))

    def network_id_status(self, network_id, check_related=False):
        """
        Returns status of specified network_id.
        Determines if a network ID has been previously registered, or
        if a network ID has been previously registered and is associated with a particular
        application.

        @type network_id: string
        @param network_id: the network ID to check status on
        @type check_related: bool
        @param check_related: specifies whether to check if a network ID has
            been previously associated with a particular application
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        uri = 'registrant/{0}'.format(network_id)
        params = {}
        if check_related:
            params['query'] = 'related'
        res = self.post(uri, params)

        if res.code in [200, 401, 404]:
            return res
        raise TelesocialServiceError(res.code, deep_find(res.data, 'message'))

    def conference_create(self, network_id, greeting_id=None, recording_id=None):
        """
        Creates new conference call.

        @type network_id: string
        @param network_id: the network ID of the conference "leader"
        @type greeting_id: string
        @param greeting_id: the media ID of a pre-recorded greeting,
            to be played to conference participants when they answer their phones
        @type recording_id: string
        @param recording_id: the media ID to which the conference audio is to be recorded
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        uri = 'conference'
        params = {'networkid': network_id}
        if recording_id:
            params['recordingid'] = recording_id
        if greeting_id:
            params['greetingid'] = greeting_id
        res = self.post(uri, params)

        if 200 <= res.code < 300:
            return res
        raise TelesocialServiceError(res.code, deep_find(res.data, 'message'))

    def conference_add(self, conference_id, network_ids, greeting_id):
        """
        Adds one or more network_id(s) to conference.

        @type conference_id: string
        @param conference_id: target conference_id
        @type network_ids: string or [string]
        @param network_ids: one or more networkids to add to the conference
        @type greeting_id: string
        @param greeting_id: the media ID of a pre-recorded greeting,
            to be played to conference participants when they answer their phones
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        uri = 'conference/{0}'.format(conference_id)
        params = {'networkid': network_ids, 'action': 'add'}
        if greeting_id:
            params['greetingid'] = greeting_id
        res = self.post(uri, params)

        if 200 <= res.code < 300:
            return res
        raise TelesocialServiceError(res.code, deep_find(res.data, 'message'))

    def conference_close(self, conference_id):
        """
        Closes active conference.

        @type conference_id: string
        @param conference_id: the ID of the conference to close
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        uri = 'conference/{0}'.format(conference_id)
        params = {'action': 'close'}
        res = self.post(uri, params)

        if 200 <= res.code < 300:
            return res
        raise TelesocialServiceError(res.code, deep_find(res.data, 'message'))

    def conference_hangup(self, conference_id, network_id):
        """
        Terminates the specified conference leg.

        @type conference_id: string
        @param conference_id: the conference ID of the call
        @type network_id: string
        @param network_id: the network ID to terminate from the call
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        uri = 'conference/{0}/{1}'.format(conference_id, network_id)
        params = {'action': 'hangup'}
        res = self.post(uri, params)

        if 200 <= res.code < 300:
            return res
        raise TelesocialServiceError(res.code, deep_find(res.data, 'message'))

    def conference_move(self, from_id, to_id, network_id):
        """
        Moves a call leg from one conference to another.

        @type from_id: string
        @param from_id: the conference ID of a conference that networkid is currently participating in
        @type to_id: string
        @param to_id: the conference ID to which the networkid should be moved
        @type network_id: string
        @param network_id: the network ID to be moved between conferences
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        uri = 'conference/{0}/{1}'.format(from_id, network_id)
        params = {'toconferenceid': to_id, 'action': 'move'}
        res = self.post(uri, params)

        if 200 <= res.code < 300:
            return res
        raise TelesocialServiceError(res.code, deep_find(res.data, 'message'))

    def conference_mute(self, conference_id, network_id, mute=True):
        """
        Mutes or un-mutes the specified call leg.

        @type conference_id: string
        @param conference_id: the conference ID on which to perform muting
        @type network_id: string
        @param network_id: the network ID to be muted
        @type mute: bool
        @param mute: specifies whether to mute network_id or unmute
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        uri = 'conference/{0}/{1}'.format(conference_id, network_id)
        params = {'action': 'mute' if mute else 'unmute'}
        res = self.post(uri, params)

        if 200 <= res.code < 300:
            return res
        raise TelesocialServiceError(res.code, deep_find(res.data, 'message'))

    def conference_unmute(self, conference_id, network_id):
        """
        Un-mutes the specified call leg. Wrapper around conference_mute.

        @type conference_id: string
        @param conference_id: the conference ID on which to perform unmuting
        @type network_id: string
        @param network_id: the network ID to be unmuted
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self.conference_mute(conference_id, network_id, False)


    def media_create(self):
        """
        Creates a new Media ID.

        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        uri = 'media'
        params = {}
        res = self.post(uri, params)

        if 200 <= res.code < 300:
            return res
        raise TelesocialServiceError(res.code, deep_find(res.data, 'message'))

    def media_record(self, media_id, network_id, greeting_id=None):
        """
        Causes the specified networkid to be called and played a "record greeting" prompt.
        The status of the recording can subsequently be determined by calling the
        "media status" method and supplying the appropriate Media ID.

        @type media_id: string
        @param media_id: the media ID to associate with the recorded audio
        @type network_id: string
        @param network_id: the network ID to call
        @type greeting_id: string
        @param greeting_id: the media ID of the greeting to play when the phone is answered
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        uri = 'media/{0}'.format(media_id)
        params = {'networkid': network_id, 'action': 'record'}
        if greeting_id:
            params['greetingid'] = greeting_id
        res = self.post(uri, params)

        if 200 <= res.code < 300:
            return res
        raise TelesocialServiceError(res.code, deep_find(res.data, 'message'))

    def media_blast(self, media_id, network_id, greeting_id=None):
        """
        Causes the specified networkid to be called and played a previously-recorded audio clip.

        @type media_id: string
        @param media_id: the audio media to play
        @type network_id: string
        @param network_id: the network ID to call
        @type greeting_id: string
        @param greeting_id: the media ID of the greeting to play when the phone is answered
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        uri = 'media/{0}'.format(media_id)
        params = {'networkid': network_id, 'action': 'blast'}
        if greeting_id:
            params['greetingid'] = greeting_id
        res = self.post(uri, params)

        if 200 <= res.code < 300:
            return res
        raise TelesocialServiceError(res.code, deep_find(res.data, 'message'))

    def media_status(self, media_id):
        """
        Retrieves status information about the Media ID and the operation in progress, if any.

        @type media_id: string
        @param media_id: the id of the media to retrieve status for
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        uri = 'media/status/{0}'.format(media_id)
        params = {}
        res = self.post(uri, params)

        if 200 <= res.code < 300:
            return res
        raise TelesocialServiceError(res.code, deep_find(res.data, 'message'))

    def media_request_upload_grant(self, media_id):
        """
        Requests permission to upload a file.

        @type media_id: string
        @param media_id: the media ID that is to be associated with the uploaded file
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        uri = 'media/{0}'.format(media_id)
        params = {'action': 'upload_grant'}
        res = self.post(uri, params)

        if 200 <= res.code < 300:
            return res
        raise TelesocialServiceError(res.code, deep_find(res.data, 'message'))

    def media_remove(self, media_id):
        """
        Requests remove a media instance.

        @type media_id: string
        @param media_id: the ID of the media to be removed
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        uri = 'media/{0}'.format(media_id)
        params = {'action': 'remove'}
        res = self.post(uri, params)

        if 200 <= res.code < 300:
            return res
        raise TelesocialServiceError(res.code, deep_find(res.data, 'message'))


# RICH CLIENT
class RichClientItem:
    """
    Base class for API items like Media, Conference or NetworkID

    @type _id: string
    @ivar _id: item id
    @type _c: SimpleClient
    @ivar _c: reference to related SimpleClient instance
    """
    def __init__(self, id, client):
        """
        Constructor.

        @type id: string
        @param id: item id
        @type client: SimpleClient
        @param client: reference to related SimpleClient instance
        """
        self._id = id
        self._c = client

    def __repr__(self):
        """
        Returns text representation of an item.

        @rtype: string
        @return: text representation
        """
        return '{0}({1!r}, {2!r})'.format(self.__class__.__name__, self._id, self._c)

    def __str__(self):
        """
        Returns item id as a string, allowing direct usage of derived class instances
        in place of string IDs.

        @rtype: string
        @return: item id
        """
        return self._id

    def __len__(self):
        """
        Rasies TypeError, to workaround bug in urllib2.urlencode function.
        @raise TypeError: always
        """
        raise TypeError()

    @property
    def id(self):
        """
        Provides convinient access to item ID.

        @rtype: string
        @return: item ID
        """
        return self._id


class NetworkId(RichClientItem):
    """
    NetworkId item, storing network_id and providing convenient access to
    network_id related methods.
    """
    def __init__(self, *args, **kwargs):
        """
        Constructor.

        @see: RichClientItem.__init__
        """
        RichClientItem.__init__(self, *args, **kwargs)

    @property
    def exists(self):
        """
        Determines if specified network_id was previously registered.

        @rtype: bool
        @return: True, if network_id was previously registered
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        res = self._c.network_id_status(self._id, True)
        if res.code in [200, 401]:
            return True
        return False

    @property
    def related(self):
        """
        Determines if specified network_id was previously registered
        AND associated with current application.

        @rtype: bool
        @return: True, if network_id was previously registered AND associated
            with current application
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        res = self._c.network_id_status(self._id, True)
        if res.code == 200:
            return True
        return False

    def blast(self, media_id, greeting_id=None):
        """
        Causes this networkid to be called and played a previously-recorded audio clip.

        @see: SimpleClient.media_blast
        @type media_id: string
        @param media_id: the audio media to play
        @type greeting_id: string
        @param greeting_id: the media ID of the greeting to play when the phone is answered
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.media_blast(media_id, self._id, greeting_id)

    def record(self, media_id, greeting_id=None):
        """
        Causes this networkid to be called and played a "record greeting" prompt.
        The status of the recording can subsequently be determined by calling the
        "media status" method and supplying the appropriate Media ID.

        @see: SimpleClient.media_record
        @type media_id: string
        @param media_id: the media ID to associate with the recorded audio
        @type greeting_id: string
        @param greeting_id: the media ID of the greeting to play when the phone is answered
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.media_record(media_id, self._id, greeting_id)

    def add(self, conference_id, greeting_id=None):
        """
        Adds this network_id to specified conference.

        @see: SimpleClient.conference_add
        @type conference_id: string
        @param conference_id: target conference_id
        @type greeting_id: string
        @param greeting_id: the media ID of a pre-recorded greeting,
            to be played to conference participants when they answer their phones
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.conference_add(conference_id, self._id, greeting_id)

    def hangup(self, conference_id):
        """
        Terminates this conference leg.

        @see: SimpleClient.conference_hangup
        @type conference_id: string
        @param conference_id: the conference ID of the call
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.conference_hangup(conference_id, self._id)

    def move(self, from_id, to_id):
        """
        Moves this call leg from one conference to another.

        @see: SimpleClient.conference_move
        @type from_id: string
        @param from_id: the conference ID of a conference that networkid is currently participating in
        @type to_id: string
        @param to_id: the conference ID to which the networkid should be moved
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.conference_move(from_id, to_id, self._id)

    def mute(self, conference_id):
        """
        Mutes this call leg.

        @see: SimpleClient.conference_mute
        @type conference_id: string
        @param conference_id: the conference ID on which to perform muting
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.conference_mute(conference_id, self._id)

    def unmute(self, conference_id):
        """
        Unmutes this call leg

        @see: SimpleClient.conference_unmute
        @type conference_id: string
        @param conference_id: the conference ID on which to perform unmuting
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.conference_unmute(conference_id, self._id)


class Conference(RichClientItem):
    """
    Conference item, storing conference_id and providing convenient access to
    conference related methods.
    """
    def __init__(self, *args, **kwargs):
        """
        Constructor.

        @see: RichClientItem.__init__
        """
        RichClientItem.__init__(self, *args, **kwargs)

    def add(self, network_ids, greeting_id=None):
        """
        Adds one or more network_id(s) to this conference.

        @see: SimpleClient.conference_add
        @type network_ids: string or [string]
        @param network_ids: one or more networkids to add to the conference
        @type greeting_id: string
        @param greeting_id: the media ID of a pre-recorded greeting,
            to be played to conference participants when they answer their phones
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.conference_add(self._id, network_ids, greeting_id)

    def close(self):
        """
        Closes this conference, if it is active.

        @see: SimpleClient.conference_close
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.conference_close(self._id)

    def hangup(self, network_id):
        """
        Terminates the specified call leg from this conference.

        @see: SimpleClient.conference_hangup
        @type network_id: string
        @param network_id: the network ID to terminate from the call
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.conference_hangup(self._id, network_id)

    def move(self, to_id, network_id):
        """
        Moves a call leg from this conference to another.

        @see: SimpleClient.conference_move
        @type to_id: string
        @param to_id: the conference ID to which the networkid should be moved
        @type network_id: string
        @param network_id: the network ID to be moved between conferences
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.conference_move(self._id, to_conference, network_id)

    def mute(self, network_id):
        """
        Mutes the specified call leg.

        @see: SimpleClient.conference_mute
        @type network_id: string
        @param network_id: the network ID to be muted
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.conference_mute(self._id, network_id)

    def unmute(self, network_id):
        """
        Un-mutes the specified call leg.

        @see: SimpleClient.conference_unmute
        @type network_id: string
        @param network_id: the network ID to be unmuted
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.conference_unmute(self._id, network_id)


class Media(RichClientItem):
    """
    Media item, storing media_id and providing convenient access to
    media related methods and properties.
    """
    def __init__(self, *args, **kwargs):
        """
        Constructor.

        @see: RichClientItem.__init__
        """
        RichClientItem.__init__(self, *args, **kwargs)

    @property
    def content_exists(self):
        """
        Determines if media content exists for this Media ID.

        @rtype: bool
        @return: True, if media content exists for this Media ID.
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        res = self._c.media_status(self._id)
        if res.code == 200:
            return True
        return False

    @property
    def download_url(self):
        """
        Determines downloadUrl for this media_id if media content exists.

        @rtype: string or None
        @return: url of media content, if such content exists, or None
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        res = self._c.media_status(self._id)
        if res.code == 200:
            try:
                return res.data['MediaResponse']['downloadUrl']
            except Exception, e:
                raise TelesocialServiceError(original=e)
        return None

    @property
    def size(self):
        """
        Determines size of the media content for this media_id.

        @rtype: number or None
        @return: size of media content, if such content exists, or None
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        res = self._c.media_status(self._id)
        if res.code == 200:
            try:
                return res.data['MediaResponse']['fileSize']
            except Exception, e:
                raise TelesocialServiceError(original=e)
        return None

    @property
    def upload_grant(self):
        """
        Requests permission to upload a file.

        @see: SimpleClient.media_request_upload_grant
        @rtype: number
        @return: grant id
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        res = self._c.media_request_upload_grant(self._id)
        try:
            return res.data['UploadResponse']['grantId']
        except Exception, e:
            raise TelesocialServiceError(original=e)

    def record(self, network_id, greeting_id=None):
        """
        Causes the specified networkid to be called and played a "record greeting" prompt.

        @see: SimpleClient.media_record
        @type network_id: string
        @param network_id: the network ID to call
        @type greeting_id: string
        @param greeting_id: the media ID of the greeting to play when the phone is answered
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.media_record(self._id, network_id, greeting_id)

    def blast(self, network_id, greeting_id=None):
        """
        Causes the specified networkid to be called and played a previously-recorded audio clip.

        @see: SimpleClient.media_record
        @type network_id: string
        @param network_id: the network ID to call
        @type greeting_id: string
        @param greeting_id: the media ID of the greeting to play when the phone is answered
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.media_blast(self._id, network_id, greeting_id)

    def status(self):
        """
        Retrieves unmodified status information about this Media ID.

        @see: SimpleClient.media_status
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.media_status(self._id)

    def remove(self):
        """
        Requests remove of this media instance.

        @see: SimpleClient.media_remove
        @rtype: Response
        @return: server response
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.media_remove(self._id)


class RichClient:
    """
    More Object Oriented wrapper around SimpleClient. Provides the same functions
    in a bit friendlier way.

    @type _c: SimpleClient
    @ivar _c: reference to related SimpleClient instance
    """
    def __init__(self, *args, **kwargs):
        """
        Constructor.

        @see: SimpleClient.__init__
        """
        self._c = SimpleClient(*args, **kwargs)

    def version(self):
        """
        Returns 3-tuple containing version components of server API implementation.

        @rtype: tuple
        @return: 3-tuple of version components, like (1, 3, 10)
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        return self._c.version()

    def register_network_id(self, network_id, phone=None, greeting_id=None):
        """
        Registers (network_id, phone number) pair for new network_id, or relates existing
        network_id to current application.

        @see: SimpleClient.network_id_register
        @type network_id: string
        @param network_id: the network ID to be registered
        @type phone: string
        @param phone: the phone number to relate to the network ID
        @type greeting_id: string
        @param greeting_id: the media ID of the greeting to play to the potential registrant
        @rtype: NetworkId
        @return: NetworkId item, binded to registered network_id and usgin current SimpleClient
            instance
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        res = self._c.network_id_register(network_id, phone, greeting_id)
        return self.get_network_id(network_id)

    def get_network_id(self, id):
        """
        Create NetworkId item using specified id and current SimpleClient instance.

        @type id: string
        @param id: the network ID to be wrapped into NetworkId item
        @rtype: NetworkId
        @return: NetworkId instance
        """
        return NetworkId(id, self._c)

    def create_conference(self, network_id, greeting_id=None, recording_id=None):
        """
        Creates new conference call and returns corresponding Conference item.

        @see: SimpleClient.conference_create
        @type network_id: string
        @param network_id: the network ID of the conference "leader"
        @type greeting_id: string
        @param greeting_id: the media ID of a pre-recorded greeting,
            to be played to conference participants when they answer their phones
        @type recording_id: string
        @param recording_id: the media ID to which the conference audio is to be recorded
        @rtype: Conference
        @return: Conference item
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        res = self._c.conference_create(network_id, greeting_id, recording_id)
        try:
            return self.get_conference(res.data['ConferenceResponse']['conferenceId'])
        except Exception, e:
            raise TelesocialServiceError(original=e)

    def get_conference(self, id):
        """
        Create NetworkId item using specified id and current SimpleClient instance.

        @type id: string
        @param id: the conference ID to be wrapped into Conference item
        @rtype: Conference
        @return: Conference instance
        """
        return Conference(id, self._c)

    def create_media(self):
        """
        Creates a new Media ID and returns corresponding Media item.

        @see: SimpleClient.media_create
        @rtype: Media
        @return: Media instance
        @raise TelesocialNetworkError: on any connection problems
        @raise TelesocialServiceError: on invalid or unexpected response
        """
        res = self._c.media_create()
        try:
            return self.get_media(res.data['MediaResponse']['mediaId'])
        except Exception, e:
            raise TelesocialServiceError(original=e)

    def get_media(self, id):
        """
        Create Media item using specified id and current SimpleClient instance.

        @type id: string
        @param id: the media ID to be wrapped into Media item
        @rtype: Media
        @return: Media instance
        """
        return Media(id, self._c)
