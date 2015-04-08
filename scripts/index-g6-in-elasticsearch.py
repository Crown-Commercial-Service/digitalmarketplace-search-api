#!/usr/bin/python
'''Process G6 JSON files into elasticsearch

This version reads G6 JSON from disk or DM API.

Usage:
    process-g6-into-elastic-search.py <es_endpoint> <dir_or_endpoint> [<token>]

Arguments:
    es_endpoint      Full ES index URL
    dir_or_endpoint  Directory path to import or an API URL if token is given
    token            Digital Marketplace API token

'''

import os
import sys
import json
import urllib2


def post_to_es(es_endpoint, json_data):
    handler = urllib2.HTTPHandler()
    opener = urllib2.build_opener(handler)

    if not es_endpoint.endswith('/'):
        es_endpoint += '/'
    request = urllib2.Request(es_endpoint + str(json_data['id']),
                              data=json.dumps(json_data))
    request.add_header("Content-Type", 'application/json')

    print request.get_full_url()
    # print request.get_data()

    try:
        connection = opener.open(request)
    except urllib2.HTTPError, e:
        connection = e
        print connection

    # check. Substitute with appropriate HTTP code.
    if connection.code == 200:
        data = connection.read()
        print str(connection.code) + " " + data
    else:
        print "connection.code = " + str(connection.code)


def request_services(endpoint, token):
    handler = urllib2.HTTPBasicAuthHandler()
    opener = urllib2.build_opener(handler)

    page_url = endpoint
    while page_url:
        print "requesting {}".format(page_url)

        request = urllib2.Request(page_url)
        request.add_header("Authorization", "Bearer {}".format(token))
        response = opener.open(request).read()

        data = json.loads(response)
        for service in data["services"]:
            yield service

        page_url = filter(lambda l: l['rel'] == 'next', data['links'])
        if page_url:
            page_url = page_url[0]['href']


def process_json_files_in_directory(dirname):
    for filename in os.listdir(dirname):
        with open(os.path.join(dirname, filename)) as f:
            data = json.loads(f.read())
            print "doing " + filename
            yield data


def main():
    if len(sys.argv) == 4:
        es_endpoint, endpoint, token = sys.argv[1:]
        for data in request_services(endpoint, token):
            post_to_es(es_endpoint, data)
    elif len(sys.argv) == 3:
        es_endpoint, listing_dir = sys.argv[1:]
        for data in process_json_files_in_directory(listing_dir):
            post_to_es(es_endpoint, data)
    else:
        print __doc__

if __name__ == '__main__':
    main()
