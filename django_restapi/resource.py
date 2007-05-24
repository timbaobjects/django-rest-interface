from django.http import Http404, HttpResponseNotAllowed

class Resource(object):
    """
    Generic resource class that can be used for
    resources that are not based on Django models
    and is the basis for the model-bound ModelCollection
    and ModelResource classes.
    """
    def __init__(self, permitted_methods, mimetype=None):
        self.permitted_methods = [op.upper() for op in permitted_methods]
        self.mimetype = mimetype
        
    def get_url_pattern(self, base_url):
        return (r'^%s(?:(?P<ident>\d+)/?)?$', 'django_restapi.resource.dispatch' % 
                base_url, {'resource' : self})
    
    def dispatch(self, request,  ident=''):
        request_method = request.method.upper()
        if request_method not in self.permitted_methods:
            return HttpResponseNotAllowed(self.permitted_methods)
        if request_method == 'GET':
            return self.read(request, ident)
        elif request_method == 'POST':
            return self.create(request)
        elif request_method == 'PUT':
            return self.update(request, ident)
        elif request_method == 'DELETE':
            return self.delete(request, ident)
        else:
            raise Http404
        
    def create(self, request):
        raise Http404
    
    def read(self, request, ident):
        raise Http404
    
    def update(self, request, ident):
        raise Http404
    
    def delete(self, request, ident):
        raise Http404

def dispatch(request, resource, ident=''):
    return resource.dispatch(request, ident)
