from django.conf.urls.defaults import *
from django_restapi.model_resource import Collection
from django_restapi.responder import XMLResponder, TemplateResponder
from polls.models import Poll, Choice

# XML Poll API urls

xml_poll_resource = Collection(
    queryset = Poll.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    expose_fields = ('id', 'question', 'pub_date'),
    responder = XMLResponder(paginate_by = 10),
    url = r'xml/polls/'
)

xml_choice_resource = Collection(
    queryset = Choice.objects.all(),
    permitted_methods = ('GET',),
    expose_fields = ('id', 'poll_id', 'choice'),
    responder = XMLResponder(paginate_by = 5),
    url = r'xml/choices/'
)

# Template API urls

template_poll_resource = Collection(
    queryset = Poll.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    expose_fields = ('id', 'question', 'pub_date'),
    responder = TemplateResponder(
        template_dir = 'polls',
        template_object_name = 'poll',
        paginate_by = 10
    ),
    url = r'html/polls/'
)

template_choice_resource = Collection(
    queryset = Choice.objects.all(),
    permitted_methods = ('GET',),
    expose_fields = ('id', 'poll_id', 'choice'),
    responder = TemplateResponder(
        template_dir = 'polls',
        template_object_name = 'choice',
        paginate_by = 5
    ),
    url = r'html/choices/'
)

urlpatterns = patterns('',
    xml_poll_resource.get_url_pattern(),
    xml_choice_resource.get_url_pattern(),
    template_poll_resource.get_url_pattern(),
    template_choice_resource.get_url_pattern(),
   ( r'^admin/', include('django.contrib.admin.urls')),
)

# TODO: How should other URL styles, e.g. json/polls/121/2/,
# be implemented (with '2' being the 2nd choice for the poll
# with id 121)?

# TODO: URL patterns for the Atom test