#! /usr/bin/python3

"""The robots parser included in urllib assumes a UTF-8 encoding of the robots
file and fails to read google.com/robots.txt, so I decided to write this one
using the Requests library to obtain the file and regular expressions to parse
it. Despite not being a part of the robots.txt standard a lot of websites use *
as a wildcard and this has not yet been implemented in this module."""

import requests
import re

agent = 'SomeBotty'
headers = {'User-Agent': agent}


class RobotParser:
    ua = '*'
    rules = {'*': {'allow': [], 'disallow': []}}
    sitemaps = []
    bots = ''

    def __init__(self, url, agent='*'):
        # Strip sub-domains off the end of URL
        root = re.match(r'https?://[\w\.-]+', url)[0]
        try:
            robots = requests.get(root + '/robots.txt', headers=headers).text
        except requests.exceptions.ConnectionError:
            # If the robots file cannot be loaded leave the class properties
            # with their initial values. This means that there are no
            # restrictions
            return
        robots = robots.lower().split('\n')
        ua = ''
        for word in robots:
            # If the word starts with '#' it is a comment so should be ignored.
            if word and word[0] != '#':
                if 'user-agent' in word:
                    # Extract the user-agent value, strip whitespace and create
                    # a record in the rules dictionary.
                    ua = re.search(r'(?<=user-agent:).*', word)[0].strip()
                    self.rules[ua] = {'allow': [], 'disallow': []}
                elif 'disallow' in word:
                    # Search for 'disallow' first because 'allow' appears in
                    # both sorts of string.
                    rule = re.search(r'(?<=disallow:).*', word)[0].strip()
                    self.rules[ua]['disallow'].append(root + rule)
                elif 'allow' in word:
                    rule = re.search(r'(?<=allow:).*', word)[0].strip()
                    self.rules[ua]['allow'].append(root + rule)
                elif 'sitemap' in word:
                    # Load sitemaps into a class property.
                    site = re.search(r'(?<=sitemap:).*', word)[0].strip()
                    self.sitemaps.append(site)

        # If user-agent is referenced in the robots file use those rules,
        # otherwise use the '*' ruleset.
        if agent in self.rules:
            self.ua = agent
        else:
            self.ua = '*'

    def can_fetch(self, url):
        return url not in self.rules[self.ua]['disallow']
