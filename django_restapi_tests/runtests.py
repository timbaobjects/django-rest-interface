#!/usr/bin/env python
"""
Tests django_restapi by requesting various GET/POST/PUT/DELETE
operations and ensures that the server returns the appropriate HTTP
status headers and redirects.
Assumes that a web server (presumably the Django test server that can by run
by runserver.py) runs at localhost:8000.
Needs httplib2 from http://bitworking.org/projects/httplib2/
"""
import httplib2
from urllib import urlencode
import webbrowser
import re

def runtests():
    host = 'localhost'
    port = '8000'
    
    http = httplib2.Http()
    
    # Create poll
    url = 'http://%s:%s/xml/polls/' % (host, port)
    params = urlencode({
        'question' : 'Does this work',
        'pub_date_date' : '2001-01-01',
        'pub_date_time' : '12:05:01'
    })
    headers, content = http.request(url, 'POST', params)
    assert headers['status'] == '302', content
    location = headers['location']
    print location
    poll_id = int(re.findall("\d+", location)[0])
    print 'Created poll:', poll_id
    print 'Redirect to:', location
    
    # Change poll
    url = 'http://%s:%s/xml/polls/%d/' % (host, port, poll_id)
    params = urlencode({
        'question' : 'Yes, it works.',
        'pub_date_date' : '2007-07-07',
        'pub_date_time' : '12:05:01'
    })
    headers, content = http.request(url, 'POST', params) # TODO: PUT
    assert headers['status'] == '302', content
    print 'Updated poll:', poll_id
    print 'Redirect to:', headers['location']
    
    # Read poll
    headers, content = http.request(url, 'GET')
    assert headers['status'] == '200', content
    print content
    
    # Delete poll
    headers, content = http.request(url, 'DELETE')
    assert headers['status'] == '302', content
    print 'Deleted poll:', poll_id
    print 'Redirect to:', headers['location']
    
    # Read choice
    url = 'http://%s:%s/xml/choices/1/' % (host, port)
    headers, content = http.request(url, 'GET')
    assert headers['status'] == '200', content
    print content
    
    # Try to delete choice (must fail)
    headers, content = http.request(url, 'DELETE')
    assert headers['status'] == '405', headers
    print 'No permission to delete choice 1 (ok).'

    print 'All tests succeeded.'

if __name__ == '__main__':
    runtests()
