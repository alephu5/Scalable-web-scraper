#! /usr/bin/python

"""This is a simple crawling task that extracts all internal links from a page.
It is designed to be run concurrently with celery workers, that allows this
to be easily scaled up and distributed."""

from task_manager.celery import app
import time
import requests
from pymongo import MongoClient
from task_manager.parse_robots import RobotParser
from bs4 import BeautifulSoup

agent = 'SomeBotty'
headers = {'User-Agent': agent}

# This decorator allows this task to be run concurrently in
# celery workers.
@app.task(bind=True, default_retry_delay=10)
def crawl_site(self, url):
    # The mongo hostname is set within the docker-compose.yml
    client = MongoClient('mongo', 27017)
    db = client.crawler
    pages = db.pages

    # Set up the preliminary record.
    url = url.strip('/')
    doc = {'url': url,
           'crawl_time': time.time(),
           'crawl_date': time.asctime(),
           'links': []}
    try:
        # Sometimes a connection fails because the url does not have
        # http or https prepended.
        print('Crawling: ' + url)
        r = requests.get(url, headers=headers)
        doc['status'] = r.status_code
        doc['connected'] = True
    except requests.exceptions.MissingSchema:
        crawl_site('http://' + url)
        return None
    except Exception:
        doc['connected'] = False

    pages.insert_one(doc)

    # Scans for links in page and saves them into the database. This
    # was originally done using arrays but memory became a bottleneck.
    link_scan(url, pages)


def link_scan(url, pages, delay=1):
    # This class helps to ensure we abide by the rules in the robots.txt
    rp = RobotParser(url, agent)
    # Use a session because multiple connections to the domain will be made.
    s = requests.session()

    r = s.get(url, headers=headers)
    html = BeautifulSoup(r.text, 'html.parser')

    for a in set(html.find_all('a')):
        link = a.get('href')
        if not link:
            # Link is empty
            pass
        elif '#' in link:
            pass
        elif 'http://' in link or 'https://' in link:
            # External link: Could put in a task list but
            # for now do nothing.
            pass
        elif rp.can_fetch(link):
            link = link.strip('/')
            link = url + '/' + link
            print('Found: ' +  link)

            # For politeness there is a 1s default delay
            time.sleep(delay)

            # Use same format for these URLs as root
            doc = {'url': link,
                   'crawl_time': time.time(),
                   'crawl_date': time.asctime()}
            try:
                r = s.get(link, headers=headers)
                doc['status'] = r.status_code,
                doc['connected'] = True
            except Exception:
                # Don't check for http(s) as this should already
                # be present from the root URL.
                print('Connection failed: ' + url)
                doc['connected'] = False

            pages.update({'url': url}, {'$push': {'links': doc}})
