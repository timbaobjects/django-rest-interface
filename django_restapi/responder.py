"""
Data format classes ("responders") that can be plugged 
into model_resource.ModelResource and determine how
the objects of a ModelResource instance are rendered
(e.g. serialized to XML, rendered by Django's generic
views, ...).
"""
from django.core import serializers
from django.http import HttpResponse
    
class SerializeResponder(object):
    """
    Class for all data formats that are possible
    with Django's serializer framework.
    """
    def __init__(self, format, mimetype=None):
        """
        format:
            may be every format that works with Django's serializer
            framework. By default: xml, python, json, (yaml).
        mimetype:
            if the default None is not changed, any HttpResponse calls 
            use settings.DEFAULT_CONTENT_TYPE and
            settings.DEFAULT_CHARSET
        """
        self.format = format
        self.mimetype = mimetype
        
    def render(self, queryset):
        """
        Serializes a queryset to the format specified in
        self.format.
        """
        return serializers.serialize(self.format, queryset)
    
    def element(self, elem):
        """
        Renders single model objects to HttpResponse.
        """
        # TODO: Include the resource urls of related resources?
        return HttpResponse(self.render([elem]), self.mimetype)
    
    def list(self, queryset):
        """
        Renders a list of model objects to HttpResponse.
        """
        # TODO: Each element needs to include its resource url
        # TODO: Include the resource urls of related resources?
        # TODO: Pagination?
        return HttpResponse(self.render(queryset), self.mimetype)
    
class JSONResponder(SerializeResponder):
    """
    JSON data format class.
    """
    def __init__(self):
        SerializeResponder.__init__(self, 'json', 'application/json')

class XMLResponder(SerializeResponder):
    """
    XML data format class.
    """
    def __init__(self):
        SerializeResponder.__init__(self, 'xml', 'application/xml')

#class TemplateResponder(object):
#    def __init__(self, template_dir, paginate_by, template_loader,
#                 extra_context, allow_empty, context_processors,
#                 template_object_name, mimetype):
#        pass
#    def list(self, queryset):
#        pass
#    def element(self, queryset):
#        pass
#    def get_create_form(self):
#        pass
#    def get_update_form(self):
#        pass