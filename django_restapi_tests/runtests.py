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

SHOW_ERRORS_IN_BROWSER = False

def show_in_browser(content):
    if SHOW_ERRORS_IN_BROWSER:
        f = open("/tmp/djangorest_error", "w")
        f.write(content)
        f.close()
        webbrowser.open_new("file:///tmp/djangorest_error")

def runtests():
    host = 'localhost'
    port = '8000'
    
    http = httplib2.Http()
    
    for format in ['xml', 'html']:
        
        # Get list of polls
        url = 'http://%s:%s/%s/polls/' % (host, port, format)
        headers, content = http.request(url, 'GET')
        assert headers['status'] == '200', show_in_browser(content)
        assert content.find('secret') == -1
        print 'Got list of polls.'

        # Get list of choices
        url = 'http://%s:%s/%s/choices/' % (host, port, format)
        headers, content = http.request(url, 'GET')
        assert headers['status'] == '200', show_in_browser(content)
        print 'Got first page of choices.'
        
        # Second page of choices must exist.
        headers, content = http.request('%s?page=2' % url, 'GET')
        assert headers['status'] == '200', show_in_browser(content)
        print 'Got second page of polls.'
                
        # Third page must not exist.
        headers, content = http.request('%s?page=3' % url, 'GET')
        assert headers['status'] == '404', show_in_browser(content)
        print 'Got 404 for third page of polls (ok).'
                
        # Try to create poll with insufficient data
        # (needs to fail)
        url = 'http://%s:%s/%s/polls/' % (host, port, format)
        params = urlencode({
            'question' : 'Does this not work?',
        })
        headers, content = http.request(url, 'POST', params)
        assert headers['status'] == '400', show_in_browser(content)
        print 'Creating poll with insufficient data failed (ok)'
        
        # Create poll
        params = urlencode({
            'question' : 'Does this work?',
            'password' : 'secret',
            'pub_date' : '2001-01-01'
        })
        headers, content = http.request(url, 'POST', params)
        assert headers['status'] == '201', show_in_browser(content)
        location = headers['location']
        poll_id = int(re.findall("\d+", location)[0])
        print 'Created poll:', poll_id
        print 'Redirect to:', location
        
        # Try to change poll with inappropriate data
        # (needs to fail)
        url = 'http://%s:%s/%s/polls/%d/' % (host, port, format, poll_id)
        params = urlencode({
            'question' : 'Yes, it works.',
            'password' : 'newsecret',
            'pub_date' : '2007-07-07-123'
        })
        headers, content = http.request(url, 'PUT', params)
        assert headers['status'] == '400', show_in_browser(content)
        print 'Changing poll with inappropriate data failed (ok)'
            
        # Change poll
        url = 'http://%s:%s/%s/polls/%d/' % (host, port, format, poll_id)
        params = urlencode({
            'question' : 'Yes, it works.',
            'password' : 'newsecret',
            'pub_date' : '2007-07-07'
        })
        headers, content = http.request(url, 'PUT', params)
        assert headers['status'] == '200', show_in_browser(content)
        print 'Updated poll:', poll_id
        print 'Redirect to:', headers['location']
        
        # Read poll
        headers, content = http.request(url, 'GET')
        assert headers['status'] == '200', show_in_browser(content)
        assert content.find('secret') == -1
        # print content
        
        # Delete poll
        headers, content = http.request(url, 'DELETE')
        assert headers['status'] == '200', show_in_browser(content)
        print 'Deleted poll:', poll_id
        
        # Read choice
        url = 'http://%s:%s/%s/choices/1/' % (host, port, format)
        headers, content = http.request(url, 'GET')
        assert headers['status'] == '200', show_in_browser(content)
        # print content
        
        # Try to delete choice (must fail)
        headers, content = http.request(url, 'DELETE')
        assert headers['status'] == '405', headers
        print 'No permission to delete choice 1 (ok).'
    
        print 'All %s tests succeeded.\n' % format
    
    # Test different URL patterns
    url = 'http://%s:%s/json/polls/' % (host, port)
    headers, content = http.request(url, 'GET')
    assert headers['status'] == '200', show_in_browser(content)
    assert content.find('secret') == -1
    print 'Got list of polls.'
    
    # Get poll
    url = 'http://%s:%s/json/polls/1/' % (host, port)
    headers, content = http.request(url, 'GET')
    assert headers['status'] == '200', show_in_browser(content)
    assert content.find('secret') == -1
    print 'Got first poll.'    

    # Get filtered list of choices
    url = 'http://%s:%s/json/polls/1/choices/' % (host, port)
    headers, content = http.request(url, 'GET')
    assert len(eval(content)) == 3, show_in_browser(content)
    assert headers['status'] == '200', show_in_browser(content)
    assert content.find('secret') == -1
    print 'Got list of choices for poll #1.'    

    # Get choice
    url = 'http://%s:%s/json/polls/1/choices/1/' % (host, port)
    headers, content = http.request(url, 'GET')
    assert headers['status'] == '200', show_in_browser(content)
    assert content.find('secret') == -1
    print 'Got first choice for poll #1.'    
    
    # Get choice (failure)
    url = 'http://%s:%s/json/polls/1/choices/12/' % (host, port)
    headers, content = http.request(url, 'GET')
    assert headers['status'] == '404', show_in_browser(content)
    assert content.find('secret') == -1
    print 'Attempt to get 12th choice for poll #1 failed (ok).'
    
    # Try to create poll with insufficient data
    # (needs to fail)
    url = 'http://%s:%s/json/polls/' % (host, port)
    params = urlencode({
        'question' : 'Does this not work?',
    })
    headers, content = http.request(url, 'POST', params)
    assert headers['status'] == '400', show_in_browser(content)
    print 'Creating choice with insufficient data failed (ok)'
    
    # Create choice
    url = 'http://%s:%s/json/polls/1/choices/' % (host, port)
    params = urlencode({
        'poll' : 1, # TODO: Should be taken from URL
        'choice' : 'New choice',
        'votes' : 0
    })
    headers, content = http.request(url, 'POST', params)
    assert headers['status'] == '201', show_in_browser(content)
    location = headers['location']
    poll_id = int(re.findall("\d+", location)[0])
    assert poll_id == 1, poll_id
    choice_id = int(re.findall("\d+", location)[1])
    print 'Created choice: ', choice_id

    # Try to update choice with insufficient data (needs to fail)
    url = 'http://%s:%s%s' % (host, port, location)
    params = urlencode({
        'poll' : 1, # TODO: Should be taken from URL
        'choice' : 'New choice',
        'votes' : 'Should be an integer'
    })
    headers, content = http.request(url, 'PUT', params)
    assert headers['status'] == '400', show_in_browser(content)
    print 'Changing choice with inappropriate data failed (ok)'
    
    # Update choice
    params = urlencode({
        'poll' : 1, # TODO: Should be taken from URL
        'choice' : 'New choice',
        'votes' : '712'
    })
    headers, content = http.request(url, 'PUT', params)
    assert content.find("712") != -1, show_in_browser(content)
    assert headers['status'] == '200', show_in_browser(content)
    print 'Updated choice #1.'
    
    # Delete choice
    headers, content = http.request(url, 'DELETE')
    assert headers['status'] == '200', show_in_browser(content)
    print 'Choice #1 deleted.'
        
    print 'Tests for different URL pattern succeeded.\n'


    # Authentication tests:
    
    url = 'http://%s:%s/basic/polls/' % (host, port)
    headers, content = http.request(url, 'GET')
    assert headers['status'] == '401', show_in_browser(content)
    print 'Basic authentication, no password'
    
    http2 = httplib2.Http()
    http2.add_credentials('rest', 'wrong_password')
    headers, content = http.request(url, 'GET')
    assert headers['status'] == '401', show_in_browser(content)
    print 'Basic authentication, wrong password'

    http2 = httplib2.Http()
    http2.add_credentials('rest', 'rest')
    headers, content = http2.request(url, 'GET')
    assert headers['status'] == '200', show_in_browser(content)
    print 'Basic authentication, right password'
    
    url = 'http://%s:%s/digest/polls/' % (host, port)
    headers, content = http.request(url, 'GET')
    assert headers['status'] == '401', show_in_browser(content)
    print 'Digest authentication, no password'
    
    http2 = httplib2.Http()
    http2.add_credentials('john', 'wrong_password')
    headers, content = http2.request(url, 'GET')
    assert headers['status'] == '401', show_in_browser(content)
    print 'Digest authentication, wrong password'
    
    http2 = httplib2.Http()
    http2.add_credentials('john', 'johnspass')
    headers, content = http2.request(url, 'GET')
    assert headers['status'] == '200', show_in_browser(content)
    print 'Digest authentication, right password'
        
    print 'Authentication tests succeeded.\n'

if __name__ == '__main__':
    runtests()
