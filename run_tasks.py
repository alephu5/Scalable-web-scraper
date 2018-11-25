#! /usr/bin/python

"""Loads a list of the the Alexa top 1 million URLs and queues them up to be
concurrently crawl using the crawl_site function."""

from task_manager.tasks import crawl_site
import sys
import csv

try:
    n = int(sys.argv[1])
except:
    n = 1000000

if __name__ == '__main__':
    with open('top-1m.csv') as csvfile:
        urls = csv.reader(csvfile)
        for i in range(n):
            crawl_site.delay(urls.__next__()[1])
