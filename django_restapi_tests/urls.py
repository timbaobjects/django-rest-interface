from django.conf.urls.defaults import *
from django_restapi.model_resource import Collection, Entry
from django_restapi.responder import *
from polls.models import Poll, Choice

urlpatterns = patterns('',
   ( r'^admin/', include('django.contrib.admin.urls')),
)

# Really simple XML example.
#
# URLs are generated automatically:
# The API is available at /api/poll/, /api/poll/[poll_id]/,
# /api/choice/ and /api/choice/[choice_id]/

simple_poll_resource = Collection(
    queryset = Poll.objects.all(), 
    responder = XMLResponder()
)
simple_choice_resource = Collection(
    queryset = Choice.objects.all(),
    responder = XMLResponder()
)

urlpatterns += simple_poll_resource.get_url_pattern()
urlpatterns += simple_choice_resource.get_url_pattern()


# XML Test API URLs
#
# URLs are generated semi-automatically (base_url given):
# The API is available at /xml/polls/, /xml/polls/[poll_id]/,
# /xml/choices/ and /xml/choices/[choice_id]/

xml_poll_resource = Collection(
    queryset = Poll.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    expose_fields = ('id', 'question', 'pub_date'),
    responder = XMLResponder(paginate_by = 10),
    base_url = r'xml/polls/'
)

xml_choice_resource = Collection(
    queryset = Choice.objects.all(),
    permitted_methods = ('GET',),
    expose_fields = ('id', 'poll_id', 'choice'),
    responder = XMLResponder(paginate_by = 5),
    base_url = r'xml/choices/'
)

urlpatterns += xml_poll_resource.get_url_pattern()
urlpatterns += xml_choice_resource.get_url_pattern()


# Template Test API URLs
#
# URLs are generated semi-automatically (base_url given):
# The API is available at /html/polls/, /html/polls/[poll_id]/,
# /html/choices/ and /html/choices/[choice_id]/

template_poll_resource = Collection(
    queryset = Poll.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    expose_fields = ('id', 'question', 'pub_date'),
    responder = TemplateResponder(
        template_dir = 'polls',
        template_object_name = 'poll',
        paginate_by = 10
    ),
    base_url = r'html/polls/'
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
    base_url = r'html/choices/'
)

urlpatterns += template_poll_resource.get_url_pattern()
urlpatterns += template_choice_resource.get_url_pattern()


# JSON Test API URLs
#
# Polls are available at /json/polls/ and 
# /json/polls/[poll_id]/.
#
# Different (manual) URL structure for choices:
# /json/polls/[poll_id]/choices/[number of choice]/
# Example: /json/polls/121/choices/2/ identifies the second 
# choice for the poll with ID 121.

json_poll_resource = Collection(
    queryset = Poll.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    expose_fields = ('id', 'question', 'pub_date'),
    responder = JSONResponder(paginate_by=10),
    base_url = r'json/polls/'
)

class ChoiceCollection(Collection):
    
    def read(self, request, url_parts={}):
        filtered_set = self.queryset._clone()
        filtered_set = filtered_set.filter(poll__id=int(url_parts['poll_id']))
        return self.responder.list(request, filtered_set)
    
    def get_entry(self, url_parts):
        poll_id = url_parts.get('poll_id')
        choice_num = url_parts.get('choice_num')
        if poll_id and choice_num:
            poll = Poll.objects.get(id=poll_id)
            choice = poll.get_choice_from_num(choice_num)
            return ChoiceEntry(self, choice)
        return None

class ChoiceEntry(Entry):
    def get_url(self):
        choice_num = self.model.get_num()
        return 'json/polls/%d/choices/%s/' % (self.model.id, choice_num)

json_choice_resource = ChoiceCollection(
    queryset = Choice.objects.all(),
    permitted_methods = ('GET',),
    expose_fields = ('id', 'poll_id', 'choice'),
    responder = JSONResponder(paginate_by=5),
    base_url = r'json/polls/(?P<poll_id>\d+)/choices/?',
    entry_url = r'json/polls/(?P<poll_id>\d+)/choices/(?P<choice_num>\d+)/?'
)

urlpatterns += json_poll_resource.get_url_pattern()
urlpatterns += json_choice_resource.get_url_pattern()