"""
Model-bound resource class.
"""
from django import forms
from django.db.models.fields import AutoField, CharField, IntegerField, \
         PositiveIntegerField, SlugField, SmallIntegerField
from django.http import Http404, HttpResponseRedirect
from resource import Resource

class InvalidURLField(Exception):
    """
    Raised if ModelResource.get_url_pattern() can't match
    the ident field of a ModelResource (usually 'id')
    against a regular expression.
    """
    pass

class ModelResource(Resource):
    """
    Resource for Django models.
    """
    def __init__(self, queryset, permitted_methods, responder, expose_fields, 
                 base_url, ident_field='id'):
        # queryset -- determines of which subset of a Django model objects
        #                       this resource consists.
        # permitted_methods -- the HTTP request methods that
        #                       are allowed for this resource e.g. ('GET', 'PUT')
        # responder -- the data format class that creates HttpResponse
        #                       objects from single or multiple model objects and
        #                       renders forms
        # expose_fields -- the model fields that can be accessed
        #                       by the HTTP methods described in permitted_methods
        # base_url -- The URL of the collection of model objects for
        #                       this resource, e.g. 'xml/choices/'
        # ident_field -- the name of a model field (a number field, a character 
        #                       field or a slug field) that is used to construct the URL
        #                       of individual resource objects from base_url.
        self.queryset = queryset
        self.expose_fields = expose_fields
        self.responder = responder
        self.ident_field = ident_field
        self.base_url = base_url
        Resource.__init__(self, permitted_methods, responder.mimetype)
    
    def get_url_pattern(self):
        """
        Returns an url pattern that redirects any calls to /[self.base_url]/
        and /[self.base_url]/[self.ident_field]/ indirectly (via the dispatch 
        helper function) to the dispatch method of this resource instance.
        """
        # Get the field with the name specified in self.ident_field
        f = self.queryset.model._meta.get_field(self.ident_field).__class__
        
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
        url_pattern = r'^%s(?:(?P<ident>%s)/?)?$' % (self.base_url, ident_pattern)
        return (url_pattern,  'django_restapi.resource.dispatch', {'resource' : self})
    
    def get_resource_url(self, ident=''):
        """
        Returns the URL of a specific resource object if ident is given,
        otherwise the base URL of the resource.
        """
        if not ident:
            return self.base_url
        return '%s%s/' % (self.base_url, str(ident))
    
    def create(self, request):
        """
        Creates a resource with attributes given by POST, then
        redirects to the resource URI. 
        """
        manipulator = self.queryset.model.AddManipulator()
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            manipulator.do_html2python(new_data)
            new_object = manipulator.save(new_data)
            new_object_url = self.get_resource_url(getattr(new_object, self.ident_field))
            return HttpResponseRedirect(new_object_url)
        # TODO: What happens if there are errors?
        form = forms.FormWrapper(manipulator, new_data, errors)
        raise Exception('Model data errors are not handled yet.')
    
    def read(self, request, ident):
        """
        Returns a representation of the resource identified by 'ident'
        in a format depending on which responder (e.g. JSONResponder)
        was assigned to this ModelResource instance. Usually called by a
        HTTP request to the resource URI with method GET.
        """
        if ident:
            resource_object = self.queryset.get(**{self.ident_field : ident})
            return self.responder.element(resource_object)
        else:
            return self.responder.list(self.queryset)
    
    def update(self, request, ident):
        """
        Changes the attributes of the resource identified by 'ident'
        and redirects to the resource URI. Usually called by a HTTP
        request to the resource URI with method PUT.
        """
        try:
            # TODO: Make sure ident_field is the primary key,
            # otherwise get the primary key for the object
            # identified by ident
            manipulator = self.queryset.model.ChangeManipulator(ident)
        except self.queryset.model.DoesNotExist:
            raise Http404
        new_data = request.POST.copy()         # TODO: PUT instead of POST
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            manipulator.do_html2python(new_data)
            manipulator.save(new_data)
            return HttpResponseRedirect(self.get_resource_url(ident))
        # TODO: What happens if there are errors?
        form = forms.FormWrapper(manipulator, new_data, errors)
        raise Exception('Model data errors are not handled yet.')
    
    def delete(self, request, ident):
        """
        Deletes the resource identified by 'ident' and redirects to
        the list of resources. Usually called by a HTTP request to the 
        resource URI with method DELETE.
        """
        try:
            resource_object = self.queryset.get(**{self.ident_field : ident})
        except self.queryset.model.DoesNotExist:
            raise Http404
        resource_object.delete()
        return HttpResponseRedirect(self.base_url)
