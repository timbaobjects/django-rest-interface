"""
Model-bound resource class.
"""
from django import newforms as forms
from django.db.models.fields import AutoField, CharField, IntegerField, \
         PositiveIntegerField, SlugField, SmallIntegerField
from django.http import *
from resource import Resource, load_put_and_files

class InvalidURLField(Exception):
    """
    Raised if ModelResource.get_url_pattern() can't match
    the ident field of a ModelResource (usually 'id')
    against a regular expression.
    """
    pass

class Collection:
    """
    Resource for a collection of models (queryset).
    """
    
    def __init__(self, queryset, permitted_methods, responder, expose_fields, 
                 url, ident_field_name='id'):
        """
        queryset:
            determines the subset of objects (of a Django model)
            that make up this resource
        permitted_methods:
            the HTTP request methods that are allowed for this 
            resource e.g. ('GET', 'PUT')
        responder:
            the data format class that creates HttpResponse
            objects from single or multiple model objects and
            renders forms
        expose_fields:
            the model fields that can be accessed
            by the HTTP methods described in permitted_methods
        url:
            The URL of the collection of model objects for
            this resource, e.g. 'xml/choices/'
        ident_field_name:
            the name of a model field (a number field, a character 
            field or a slug field) that is used to construct the URL
            of individual resource objects from url.
        """
        self.queryset = queryset
        self.permitted_methods = [op.upper() for op in permitted_methods]
        self.responder = responder
        self.expose_fields = expose_fields # TODO: Use expose_fields
        self.url = url
        self.ident_field = self.queryset.model._meta.get_field(ident_field_name)
    
    def dispatch(self, request,  ident=''):
        """
        Redirects to one of the CRUD methods depending 
        on the HTTP method of the request. Checks whether
        the requested method is allowed for this resource.
        """
        # Check permission
        request_method = request.method.upper()
        if request_method not in self.permitted_methods:
            return HttpResponseNotAllowed(self.permitted_methods)
        
        # Remove queryset cache by cloning the queryset
        self.queryset = self.queryset._clone()

        # Redirect either to entry method
        # or to collection method
        if ident:
            entry = self.get_entry(ident)
            if request_method == 'GET':
                return entry.read(request)
            elif request_method == 'PUT':
                load_put_and_files(request)
                return entry.update(request)
            elif request_method == 'DELETE':
                return entry.delete(request)
        else:
            if request_method == 'GET':
                return self.read(request)
            elif request_method == 'POST':
                return self.create(request)
        
        # No other methods allowed
        return HttpResponseBadRequest()
    
    def create(self, request):
        """
        Creates a resource with attributes given by POST, then
        redirects to the resource URI. 
        """
        # Create a form filled with the POST data
        ResourceForm = forms.form_for_model(self.queryset.model)
        f = ResourceForm(request.POST)
        
        # If the data contains no errors, save the model,
        # return a "201 Created" response with the model's
        # URI in the location header and a representation
        # of the model in the response body.
        if f.is_valid():
            new_model = f.save()
            model_entry = Entry(self, new_model)
            response = model_entry.read(request)
            response.status_code = 201
            response.headers['Location'] = model_entry.get_url()
            return response
        
        # Otherwise return a 400 Bad Request error.
        return self.responder.error(request, 400, f.errors)
    
    def read(self, request):
        """
        Returns a representation of the queryset.
        The format depends on which responder (e.g. JSONResponder)
        is assigned to this ModelResource instance. Usually called by a
        HTTP request to the factory URI with method GET.
        """
        return self.responder.list(request, self.queryset)
    
    def get_entry(self, ident):
        """
        Returns a single Entry resource that is tied to a model.
        """
        try:
            model = self.queryset.get(**{self.ident_field.name : ident})
        except self.queryset.model.DoesNotExist:
            raise Http404
        return Entry(self, model)
    
    def get_url_pattern(self):
        """
        Returns an url pattern that redirects any calls to /[self.url]/
        and /[self.url]/[self.ident]/ indirectly (via the dispatch 
        helper function) to the dispatch method of this resource instance.
        """
        # Get the field class that identifies a specific resource 
        # object (usually the class of the primary key field).
        f = self.ident_field.__class__
        
        # Get the regular expression for this type of field
        if f in (AutoField, IntegerField, PositiveIntegerField, SmallIntegerField):
            ident_pattern = r'\d+'
        elif f == CharField:
            ident_pattern = r'\w+'
        elif f == SlugField:
            ident_pattern = r'[a-z0-9_-]+'
        else:
            raise InvalidURLField
        
        # Construct and return the URL pattern for this resource
        url_pattern = r'^%s(?:(?P<ident>%s)/?)?$' % (self.url, ident_pattern)
        return (url_pattern,  'django_restapi.resource.dispatch', {'resource' : self})

class Entry:
    """
    Resource for a single model.
    """
    
    def __init__(self, collection, model):
        self.collection = collection
        self.model = model
        
    def get_url(self):
        """
        Returns the URL for this resource object.
        """
        ident = getattr(self.model, self.collection.ident_field.name)
        return '%s%s/' % (self.collection.url, str(ident))

    def read(self, request):
        """
        Returns a representation of a single model..
        The format depends on which responder (e.g. JSONResponder)
        is assigned to this ModelResource instance. Usually called by a
        HTTP request to the resource/ URI with method GET.
        """
        return self.collection.responder.element(request, self.model)
    
    def update(self, request):
        """
        Changes the attributes of the resource identified by 'ident'
        and redirects to the resource URI. Usually called by a HTTP
        request to the resource URI with method PUT.
        """
        # Create a form from the model/PUT data
        ResourceForm = forms.form_for_instance(self.model)
        f = ResourceForm(request.PUT)
        
        # If the data contains no errors, save the model,
        # return a "200 Ok" response with the model's
        # URI in the location header and a representation
        # of the model in the response body.
        if f.is_valid():
            f.save()
            response = self.read(request)
            response.status_code = 200
            response.headers['Location'] = self.get_url()
            return response
        
        # Otherwise return a 400 Bad Request error.
        return self.collection.responder.error(request, 400, f.errors)
    
    def delete(self, request):
        """
        Deletes the resource identified by 'ident' and redirects to
        the list of resources. Usually called by a HTTP request to the 
        resource URI with method DELETE.
        """
        self.model.delete()
        return HttpResponseRedirect(self.collection.url)
    

