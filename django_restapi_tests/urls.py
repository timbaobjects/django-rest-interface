from django.conf.urls.defaults import *
from django_restapi.model_resource import Collection
from django_restapi.responder import XMLResponder
from polls.models import Poll, Choice

# Poll API urls

poll_resource = Collection(
        queryset = Poll.objects.all(),
        permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
        expose_fields = ('id', 'question', 'pub_date'),
        responder = XMLResponder(),
        url = r'xml/polls/'
)

choice_resource = Collection(
        queryset = Choice.objects.all(),
        permitted_methods = ('GET',),
        expose_fields = ('id', 'poll_id', 'choice'),
        responder = XMLResponder(),
        url = r'xml/choices/'
)

urlpatterns = patterns('',
    poll_resource.get_url_pattern(),
    choice_resource.get_url_pattern(),
   ( r'^admin/', include('django.contrib.admin.urls')),
)

# TODO: How should other URL styles, e.g. json/polls/121/2/,
# be implemented (with '2' being the 2nd choice for the poll
# with id 121)?

# TODO: URL patterns for the Atom test