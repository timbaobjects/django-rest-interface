from django.http import HttpResponse
from django.utils.translation import gettext as _
import md5, time, random

def djangouser_auth(username, password):
    """
    Check username and password against
    django.contrib.auth.models.User
    """
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(username=username)
        if user.check_password(password):
            return True
        else:
            return False
    except User.DoesNotExist:
        return False

class HttpBasicAuthentication(object):
    """
    HTTP/1.0 basic authentication.
    """    
    def __init__(self, authfunc=djangouser_auth, realm=_('Restricted Access')):
        """
        realm:
            An identifier for the authority that is requesting
            authorization
        authfunc:
            A user-defined function which takes a username and
            password as its first and second arguments respectively
            and returns True if the user is authenticated
        """
        self.realm = realm
        self.authfunc = authfunc
    
    def challenge(self):
        """
        Returns a HttpResponse that asks for appropriate
        authorization.
        """
        # TODO: Mimetype, response content need to match
        # responder class.
        response =  HttpResponse(_('Authorization Required'), mimetype="text/plain")
        response['WWW-Authenticate'] = 'Basic realm="%s"' % self.realm
        response.status_code = 401
        return response
    
    def is_authenticated(self, request):
        """
        Checks whether a request comes from an authorized user.
        """
        if not request.META.has_key('HTTP_AUTHORIZATION'):
            return False
        (authmeth, auth) = request.META['HTTP_AUTHORIZATION'].split(' ',1)
        if authmeth.lower() != 'basic':
            return False
        auth = auth.strip().decode('base64')
        username, password = auth.split(':',1)
        return self.authfunc(username=username, password=password)

def digest_password(realm, username, password):
    """
    Construct the appropriate hashcode needed for HTTP digest
    """
    return md5.md5("%s:%s:%s" % (username, realm, password)).hexdigest()

class HttpDigestAuthentication(object):
    """
    HTTP/1.1 digest authentication (RFC 2617).
    Uses code from the Python Paste Project (MIT Licence).
    """    
    def __init__(self, authfunc, realm=_('Restricted Access')):
        """
        realm:
            An identifier for the authority that is requesting
            authorization
        authfunc:
            A user-defined function which takes a username and
            a realm as its first and second arguments respectively
            and returns the combined md5 hash of username,
            authentication realm and password.
        """
        self.realm = realm
        self.authfunc = authfunc
        self.nonce    = {} # list to prevent replay attacks
    
    def challenge(self, stale = ''):
        """
        Returns a HttpResponse that asks for appropriate
        authorization.
        """
        nonce  = md5.md5(
            "%s:%s" % (time.time(), random.random())).hexdigest()
        opaque = md5.md5(
            "%s:%s" % (time.time(), random.random())).hexdigest()
        self.nonce[nonce] = None
        parts = {'realm': self.realm, 'qop': 'auth',
                 'nonce': nonce, 'opaque': opaque }
        if stale:
            parts['stale'] = 'true'
        head = ", ".join(['%s="%s"' % (k, v) for (k, v) in parts.items()])
        response =  HttpResponse(_('Authorization Required'), mimetype="text/plain")
        response['WWW-Authenticate'] = 'Digest %s' % head
        response.status_code = 401
        # TODO: Mimetype, response content need to match
        # responder class.
        return response
    
    def is_authenticated(self, request):
        """
        Checks whether a request comes from an authorized user.
        """
        if not request.META.has_key('HTTP_AUTHORIZATION'):
            return False
        fullpath = request.META['SCRIPT_NAME'] + request.META['PATH_INFO']
        (authmeth, auth) = request.META['HTTP_AUTHORIZATION'].split(" ", 1)
        if authmeth.lower() != 'digest':
            return False
        amap = {}
        for itm in auth.split(", "):
            (k,v) = [s.strip() for s in itm.split("=", 1)]
            amap[k] = v.replace('"', '')
        try:
            username = amap['username']
            authpath = amap['uri']
            nonce    = amap['nonce']
            realm    = amap['realm']
            response = amap['response']
            assert authpath.split("?", 1)[0] in fullpath
            assert realm == self.realm
            qop      = amap.get('qop', '')
            cnonce   = amap.get('cnonce', '')
            nc       = amap.get('nc', '00000000')
            if qop:
                assert 'auth' == qop
                assert nonce and nc
        except:
            return False
        ha1 = self.authfunc(realm, username)
        ha2 = md5.md5('%s:%s' % (request.method, fullpath)).hexdigest()
        if qop:
            chk = "%s:%s:%s:%s:%s:%s" % (ha1, nonce, nc, cnonce, qop, ha2)
        else:
            chk = "%s:%s:%s" % (ha1, nonce, ha2)
        if response != md5.md5(chk).hexdigest():
            if nonce in self.nonce:
                del self.nonce[nonce]
            return False
        pnc = self.nonce.get(nonce,'00000000')
        if nc <= pnc:
            if nonce in self.nonce:
                del self.nonce[nonce]
            return False # stale = True
        self.nonce[nonce] = nc
        return True