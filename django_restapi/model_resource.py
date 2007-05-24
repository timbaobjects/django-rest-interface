from django import forms
from django.db.models.fields import AutoField, CharField, IntegerField, \
         PositiveIntegerField, SlugField, SmallIntegerField
from django.http import Http404, HttpResponseRedirect
from resource import Resource

class InvalidURLField(Exception):
    pass

class ModelResource(Resource):
    """
    Resource for Django models.
    """
    def __init__(self, queryset, permitted_methods, responder, expose_fields, 
                 base_url, ident_field='id'):
        self.queryset = queryset
        self.expose_fields = expose_fields
        self.responder = responder
        self.ident_field = ident_field
        self.base_url = base_url
        Resource.__init__(self, permitted_methods, responder.mimetype)
    
    def get_url_pattern(self):
        f = self.queryset.model._meta.get_field(self.ident_field).__class__
        if f in (AutoField, IntegerField, PositiveIntegerField, SmallIntegerField):
            ident_pattern = r'\d+'
        elif f == CharField:
            ident_pattern = r'\w+'
        elif f == SlugField:
            ident_pattern = r'[a-z0-9_-]+'
        else:
            raise InvalidURLField
        url_pattern = r'^%s(?:(?P<ident>%s)/?)?$' % (self.base_url, ident_pattern)
        return (url_pattern,  'django_restapi.resource.dispatch', {'resource' : self})
    
    def get_resource_url(self, ident):
        return '%s%s/' % (self.base_url, str(ident))
    
    def create(self, request):
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
        if ident:
            resource_object = self.queryset.get(**{self.ident_field : ident})
            return self.responder.element(resource_object)
        else:
            return self.responder.list(self.queryset)
    
    def update(self, request, ident):
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
        try:
            resource_object = self.queryset.get(**{self.ident_field : ident})
        except self.queryset.model.DoesNotExist:
            raise Http404
        resource_object.delete()
        return HttpResponseRedirect(self.base_url)
