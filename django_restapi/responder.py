"""
Data format classes ("responders") that can be plugged 
into model_resource.ModelResource and determine how
the objects of a ModelResource instance are rendered
(e.g. serialized to XML, rendered by Django's generic
views, ...).
"""
from django.core import serializers
from django.http import HttpResponse
from django.newforms.util import ErrorDict
from django.template import loader
from django.views.generic import list_detail
from django.views.generic.simple import direct_to_template
from django.db.models.query import QuerySet
from django.core.paginator import ObjectPaginator, InvalidPage

class SerializeResponder(object):
    """
    Class for all data formats that are possible
    with Django's serializer framework.
    """
    def __init__(self, format, mimetype=None, paginate_by=None, allow_empty=False):
        """
        format:
            may be every format that works with Django's serializer
            framework. By default: xml, python, json, (yaml).
        mimetype:
            if the default None is not changed, any HttpResponse calls 
            use settings.DEFAULT_CONTENT_TYPE and
            settings.DEFAULT_CHARSET
        paginate_by:
            Number of elements per page. Default: All elements.
        """
        self.format = format
        self.mimetype = mimetype
        self.paginate_by = paginate_by
        self.allow_empty = allow_empty
        
    def render(self, object_list):
        """
        Serializes a queryset to the format specified in
        self.format.
        """
        return serializers.serialize(self.format, object_list)
    
    def element(self, request, elem):
        """
        Renders single model objects to HttpResponse.
        """
        # TODO: Include the resource urls of related resources?
        return HttpResponse(self.render([elem]), self.mimetype)
    
    def error(self, request, status_code, error_dict=ErrorDict()):
        """
        Handles errors in a RESTful way.
        - appropriate status code
        - appropriate mimetype
        - human-readable error message
        """
        response = HttpResponse(mimetype = self.mimetype)
        response.write('Error %s' % status_code)
        if error_dict:
            response.write('\n\nErrors:\n')
            response.write(error_dict.as_text())
        response.status_code = status_code
        return response
    
    def list(self, request, queryset, page=None):
        """
        Renders a list of model objects to HttpResponse.
        """
        if self.paginate_by:
            paginator = ObjectPaginator(queryset, self.paginate_by)
            if not page:
                page = request.GET.get('page', 1)
            try:
                page = int(page)
                object_list = paginator.get_page(page - 1)
            except (InvalidPage, ValueError):
                if page == 1 and self.allow_empty:
                    object_list = []
                else:
                    return self.error(request, 404)
            # TODO: Each page needs to include a link to the
            # next page
        else:
            object_list = list(queryset)
        # TODO: Each element needs to include its resource url
        # TODO: Include the resource urls of related resources?
        return HttpResponse(self.render(object_list), self.mimetype)
    
class JSONResponder(SerializeResponder):
    """
    JSON data format class.
    """
    def __init__(self, paginate_by=None, allow_empty=False):
        SerializeResponder.__init__(self, 'json', 'application/json',
                    paginate_by=paginate_by, allow_empty=allow_empty)

    # def error(self, status_code, error_dict={}):
        # TODO: Return JSON error message

class XMLResponder(SerializeResponder):
    """
    XML data format class.
    """
    def __init__(self, paginate_by=None, allow_empty=False):
        SerializeResponder.__init__(self, 'xml', 'application/xml',
                    paginate_by=paginate_by, allow_empty=allow_empty)

    # def error(self, status_code, error_dict={}):
        # TODO: Return XML error message, e.g.
        # http://www.oreillynet.com/onlamp/blog/2003/12/restful_error_handling.html

class TemplateResponder(object):
    """
    Data format class that uses Django's generic views.
    """
    def __init__(self, template_dir, paginate_by=None, template_loader=loader,
                 extra_context=None, allow_empty=False, context_processors=None,
                 template_object_name='object', mimetype=None):
        self.template_dir = template_dir
        self.paginate_by = paginate_by
        self.template_loader = template_loader
        self.extra_context = extra_context
        self.allow_empty = allow_empty
        self.context_processors = context_processors
        self.template_object_name = template_object_name
        self.mimetype = mimetype
    
    def list(self, request, queryset, page=None):
        template_name = '%s/%s_list.html' % (self.template_dir, queryset.model._meta.module_name)
        return list_detail.object_list(request,
            queryset = queryset,
            paginate_by = self.paginate_by,
            template_name = template_name,
            template_loader = self.template_loader,
            extra_context = self.extra_context,
            allow_empty = self.allow_empty,
            context_processors = self.context_processors,
            template_object_name = self.template_object_name,
            mimetype = self.mimetype
        )
        
    def element(self, request, elem):
        template_name = '%s/%s_detail.html' % (self.template_dir, elem._meta.module_name)
        # Construct QuerySet from single model object:
        q = QuerySet(elem.__class__)
        q._result_cache = [elem]
        return list_detail.object_detail(request,
            queryset = q,
            object_id = elem.id,
            template_name = template_name,
            template_loader = self.template_loader,
            extra_context = self.extra_context,
            context_processors = self.context_processors,
            template_object_name = self.template_object_name,
            mimetype = self.mimetype
        )
    
    def error(self, request, status_code, error_dict=ErrorDict()):
        response = direct_to_template(request, 
            template = '%s/%s.html' % (self.template_dir, str(status_code)),
            extra_context = { 'errors' : error_dict },
            mimetype = self.mimetype)
        response.status_code = status_code
        return response
    
    #def get_create_form(self):
    #    pass
    
    #def get_update_form(self):
    #    pass