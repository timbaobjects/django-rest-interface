from django.core import serializers
from django.http import HttpResponse
    
class SerializeResponder(object):
    def __init__(self, format, mimetype='text/plain'):
        self.format = format
        self.mimetype = mimetype
        
    def render(self, queryset):
        return serializers.serialize(self.format, queryset)
    
    def element(self, elem):
        # TODO: Include the resource urls of related resources?
        return HttpResponse(self.render([elem]), self.mimetype)
    
    def list(self, queryset):
        # TODO: Each element needs to include its resource url
        # TODO: Include the resource urls of related resources?
        # TODO: Pagination?
        return HttpResponse(self.render(queryset), self.mimetype)
    
class JSONResponder(SerializeResponder):
    def __init__(self):
        SerializeResponder.__init__(self, 'json', 'application/json')

class XMLResponder(SerializeResponder):
    def __init__(self):
        SerializeResponder.__init__(self, 'xml', 'application/xml')

#class TemplateResponder(object):
#    def __init__(self, template_dir, paginate_by, template_loader, extra_context, 
#                 allow_empty, context_processors, template_object_name, mimetype):
#        pass
#    def list(self, queryset):
#        pass
#    def element(self, queryset):
#        pass
#    def get_create_form(self):
#        pass
#    def get_update_form(self):
#        pass