"""
Model-bound resource class.
"""
from django import newforms as forms
from django.conf.urls.defaults import patterns
from django.db.models.fields import AutoField, CharField, IntegerField, \
         PositiveIntegerField, SlugField, SmallIntegerField
from django.http import *
from django.newforms.util import ErrorDict
from resource import load_put_and_files

def dispatch(request, resource, is_entry, **url_parts):
    """
    Helper function that redirects a call from Django's
    url patterns that has a resource instance as an
    argument to the dispatch method of the instance.
    """
    return resource.dispatch(request, is_entry, **url_parts)

class InvalidURLField(Exception):
    """
    Raised if ModelResource.get_url_pattern() can't match
    the ident field of a ModelResource (usually 'id')
    against a regular expression.
    """
    pass

class InvalidModelData(Exception):
    """
    Raised if create/update fails because the PUT/POST 
    data is not appropriate.
    """
    def __init__(self, errors=ErrorDict()):
        self.errors = errors

class Collection:
    """
    Resource for a collection of models (queryset).
    """
    
    def __init__(self, queryset, responder, permitted_methods=None, expose_fields=None,
                 base_url=None, entry_url=None, ident_field_name=None):
        """
        queryset:
            determines the subset of objects (of a Django model)
            that make up this resource
        responder:
            the data format class that creates HttpResponse
            objects from single or multiple model objects and
            renders forms
        permitted_methods:
            the HTTP request methods that are allowed for this 
            resource e.g. ('GET', 'PUT')
        expose_fields:
            the model fields that can be accessed
            by the HTTP methods described in permitted_methods
        ident_field_name:
            the name of a model field (a number field, a character 
            field or a slug field) that is used to construct the URL
            of individual resource objects from the URL.
        get_model_func:
            optional customized function that takes a key-value dict
            parsed from an url as an argument and returns an entry
        base_url:
            The URL of the collection of model objects for
            this resource, e.g. 'xml/choices/'
        entry_url:
            The URL for single entries of this collection,
            e.g. 'xml/choices/(?P<ident>\d+)/?'. 
            If entry_url does not contain "(?P<ident>)", you need
            to overwrite get_entry in order to retain a working
            URL-to-model mapping.
        """
        # Available data
        self.queryset = queryset
        
        # Output format
        self.responder = responder
        
        # Access restrictions
        if permitted_methods:
            self.permitted_methods = [op.upper() for op in permitted_methods]
        else:
            self.permitted_methods = ["GET"]
        if expose_fields:
            self.expose_fields = expose_fields
        else:
            self.expose_fields = [field.name for field in queryset.model._meta.fields]
        responder.expose_fields = self.expose_fields
        
        # URL generation
        if ident_field_name:
            self.ident_field = self.queryset.model._meta.get_field(ident_field_name)
        else:
            self.ident_field = self.queryset.model._meta.pk
        self.base_url = base_url or self.default_base_url()
        self.entry_url = entry_url or self.default_entry_url()
    
    def dispatch(self, request, is_entry, **url_parts):
        """
        Redirects to one of the CRUD methods depending 
        on the HTTP method of the request. Checks whether
        the requested method is allowed for this resource.
        Catches errors.
        """
        
        # Check permission
        request_method = request.method.upper()
        if request_method not in self.permitted_methods:
            return HttpResponseNotAllowed(self.permitted_methods)
        
        # Remove queryset cache by cloning the queryset
        self.queryset = self.queryset._clone()
        
        # Redirect either to entry method
        # or to collection method. Catch errors.
        try:
            if is_entry:
                entry = self.get_entry(url_parts)    
                if request_method == 'GET':
                    return entry.read(request, url_parts)
                elif request_method == 'PUT':
                    load_put_and_files(request)
                    return entry.update(request, url_parts)
                elif request_method == 'DELETE':
                    return entry.delete(request, url_parts)
            else:
                if request_method == 'GET':
                    return self.read(request, url_parts)
                elif request_method == 'POST':
                    return self.create(request, url_parts)
        except (self.queryset.model.DoesNotExist, Http404):
            # 404 Page not found
            return self.responder.error(request, 404)
        except InvalidModelData, i:
            # 400 Bad Request error.
            return self.responder.error(request, 400, i.errors)
        
        # No other methods allowed
        return HttpResponseBadRequest()
    
    def create(self, request, url_parts={}):
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
        raise InvalidModelData(f.errors)
    
    def read(self, request, url_parts={}):
        """
        Returns a representation of the queryset.
        The format depends on which responder (e.g. JSONResponder)
        is assigned to this ModelResource instance. Usually called by a
        HTTP request to the factory URI with method GET.
        """
        return self.responder.list(request, self.queryset)
    
    def get_entry(self, url_parts):
        """
        Returns a single entry if it can identify a model from the
        regex dict url_parts.
        """
        assert url_parts.get('ident')
        model = self.queryset.get(**{self.ident_field.name : url_parts['ident']})
        entry = Entry(self, model)
        return entry
    
    def default_base_url(self):
        """
        Returns a default url for the collection, e.g.
        "api/poll/".
        """
        return r'api/%s/' % self.queryset.model._meta.module_name
        
    def default_entry_url(self):
        """
        Returns a default url regex pattern that looks like this:
        [collection url]/[entry identifier]/, e.g.
        "api/poll/[poll_id]/".
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
        return r'%s(?P<ident>%s)/?' % (self.base_url, ident_pattern)
    
    def get_url_pattern(self):
        return patterns('',
            (r'^%s$' % self.entry_url, 'django_restapi.model_resource.dispatch', {'is_entry' : True, 'resource' : self}),
            (r'^%s$' % self.base_url, 'django_restapi.model_resource.dispatch', {'is_entry' : False, 'resource' : self}))

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
        return '%s%s/' % (self.collection.base_url, str(ident))

    def read(self, request, url_parts={}):
        """
        Returns a representation of a single model..
        The format depends on which responder (e.g. JSONResponder)
        is assigned to this ModelResource instance. Usually called by a
        HTTP request to the resource/ URI with method GET.
        """
        return self.collection.responder.element(request, self.model)
    
    def update(self, request, url_parts={}):
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
        raise InvalidModelData(f.errors)
    
    def delete(self, request, url_parts={}):
        """
        Deletes the resource identified by 'ident' and redirects to
        the list of resources. Usually called by a HTTP request to the 
        resource URI with method DELETE.
        """
        self.model.delete()
        return HttpResponse(_("Object successfully deleted."), self.collection.responder.mimetype)
    

