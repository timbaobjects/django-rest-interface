"""
Model-bound resource class.
"""
from django import newforms as forms
from django.conf.urls.defaults import patterns
from django.db.models.fields import AutoField, CharField, IntegerField, \
         PositiveIntegerField, SlugField, SmallIntegerField
from django.http import *
from django.newforms.util import ErrorDict
from django.utils.functional import curry
from django.utils.translation.trans_null import _
from resource import Resource, load_put_and_files, reverse

class InvalidModelData(Exception):
    """
    Raised if create/update fails because the PUT/POST 
    data is not appropriate.
    """
    def __init__(self, errors=ErrorDict()):
        self.errors = errors

class Collection(Resource):
    """
    Resource for a collection of models (queryset).
    """
    def __init__(self, queryset, responder, authentication=None, 
                 permitted_methods=None, expose_fields=None,
                 entry_class=None):
        """
        queryset:
            determines the subset of objects (of a Django model)
            that make up this resource
        responder:
            the data format instance that creates HttpResponse
            objects from single or multiple model objects and
            renders forms
        authentication:
            the authentication instance that checks whether a
            request is authenticated
        permitted_methods:
            the HTTP request methods that are allowed for this 
            resource e.g. ('GET', 'PUT')
        expose_fields:
            the model fields that can be accessed
            by the HTTP methods described in permitted_methods
        entry_class:
            class used for entries in create() and get_entry()
        """
        # Available data
        self.queryset = queryset
        
        # Output format / responder setup
        self.responder = responder
        if not expose_fields:
            expose_fields = [field.name for field in queryset.model._meta.fields]
        responder.expose_fields = expose_fields
        if hasattr(responder, 'create_form'):
            responder.create_form = curry(responder.create_form, queryset=queryset)
        if hasattr(responder, 'update_form'):
            responder.update_form = curry(responder.update_form, queryset=queryset)
                
        # Access restrictions
        Resource.__init__(self, authentication, permitted_methods)
        
        self.entry_class = entry_class or Entry
    
    def __call__(self, request, *args, **kwargs):
        """
        Redirects to one of the CRUD methods depending 
        on the HTTP method of the request. Checks whether
        the requested method is allowed for this resource.
        Catches errors.
        """
        # Check permission
        if self.authentication:
            if not self.authentication.is_authenticated(request):
                return self.authentication.challenge()
        request_method = request.method.upper()
        if request_method not in self.permitted_methods:
            return HttpResponseNotAllowed(self.permitted_methods)
        
        # Remove queryset cache by cloning the queryset
        self.queryset = self.queryset._clone()
        
        # Determine whether the collection or a specific
        # entry is requested. If not specified as a keyword
        # argument, assume that any args/kwargs are used to
        # select a specific entry from the collection.
        if kwargs.has_key('is_entry'):
            is_entry = kwargs.pop('is_entry')
        else:
            eval_args = tuple([x for x in args if x != ''])
            is_entry = bool(eval_args or kwargs)
        
        # Redirect either to entry method
        # or to collection method. Catch errors.
        try:
            if is_entry:
                entry = self.get_entry(*args, **kwargs)
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
        except (self.queryset.model.DoesNotExist, Http404):
            # 404 Page not found
            return self.responder.error(request, 404)
        except InvalidModelData, i:
            # 400 Bad Request error
            return self.responder.error(request, 400, i.errors)
        
        # No other methods allowed: Bad Request
        return self.responder.error(request, 400)
    
    def create(self, request):
        """
        Creates a resource with attributes given by POST, then
        redirects to the resource URI. 
        """
        # Create form filled with POST data
        ResourceForm = forms.form_for_model(self.queryset.model)
        f = ResourceForm(request.POST)
        
        # If the data contains no errors, save the model,
        # return a "201 Created" response with the model's
        # URI in the location header and a representation
        # of the model in the response body.
        if f.is_valid():
            new_model = f.save()
            model_entry = self.entry_class(self, new_model)
            response = model_entry.read(request)
            response.status_code = 201
            response.headers['Location'] = model_entry.get_url()
            return response

        # Otherwise return a 400 Bad Request error.
        raise InvalidModelData(f.errors)
    
    def read(self, request):
        """
        Returns a representation of the queryset.
        The format depends on which responder (e.g. JSONResponder)
        is assigned to this ModelResource instance. Usually called by a
        HTTP request to the factory URI with method GET.
        """
        return self.responder.list(request, self.queryset)
    
    def get_entry(self, pk_value):
        """
        Returns a single entry retrieved by filtering the 
        collection queryset by primary key value.
        """
        model = self.queryset.get(**{self.queryset.model._meta.pk.name : pk_value})
        entry = self.entry_class(self, model)
        return entry

class Entry(object):
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
        pk_value = getattr(self.model, self.model._meta.pk.name)
        return reverse(self.collection, (pk_value,))
    
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
        raise InvalidModelData(f.errors)
    
    def delete(self, request):
        """
        Deletes the model associated with the current entry.
        Usually called by a HTTP request to the entry URI
        with method DELETE.
        """
        self.model.delete()
        return HttpResponse(_("Object successfully deleted."), self.collection.responder.mimetype)
    

