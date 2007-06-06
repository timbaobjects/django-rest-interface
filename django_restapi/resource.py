"""
Generic resource class.
"""
from django.http import Http404, HttpResponseNotAllowed, HttpResponseBadRequest, QueryDict

class Resource(object):
    """
    Generic resource class that can be used for
    resources that are not based on Django models
    and is the basis for the model_resource.ModelResource
    class.
    """
    def __init__(self, permitted_methods, mimetype=None):
        """
        permitted_methods:
            the HTTP request methods that are allowed for this
            resource e.g. ('GET', 'PUT')
        mimetype:
            if the default None is not changed, any HttpResponse calls
            use settings.DEFAULT_CONTENT_TYPE and 
            settings.DEFAULT_CHARSET
        """
        self.permitted_methods = [op.upper() for op in permitted_methods]
        self.mimetype = mimetype
    
    def get_url_pattern(self, base_url):
        """
        Returns an url pattern that redirects any calls to /[base_url]/
        and /[base_url]/[id]/ indirectly (via the dispatch helper function)
        to the dispatch method of this resource instance.
        """
        return (r'^%s(?:(?P<ident>\d+)/?)?$' % base_url,
                'django_restapi.resource.dispatch', {'resource' : self})
    
    def dispatch(self, request):
        """
        Redirects to one of the CRUD methods depending 
        on the HTTP method of the request. Checks whether
        the requested method is allowed for this resource.
        """
        request_method = request.method.upper()
        if request_method not in self.permitted_methods:
            return HttpResponseNotAllowed(self.permitted_methods)
        if request_method == 'GET':
            return self.read(request)
        elif request_method == 'POST':
            return self.create(request)
        elif request_method == 'PUT':
            # PUT and POST requests only differ in REQUEST_METHOD,
            # not in the way data is encoded.
            # TODO: Handle FILES
            request.PUT = QueryDict(request.raw_post_data)
            return self.update(request)
        elif request_method == 'DELETE':
            return self.delete(request)
        else:
            raise Http404
    
    # The four CRUD methods that any class that 
    # inherits from Resource may to implement:
    
    def create(self, request):
        raise Http404
    
    def read(self, request):
        raise Http404
    
    def update(self, request):
        raise Http404
    
    def delete(self, request):
        raise Http404

def dispatch(request, resource, ident=''):
    """
    Helper function that redirects a call from Django's
    url patterns that has a resource instance as an
    argument to the dispatch method of the instance.
    """
    return resource.dispatch(request, ident)
    