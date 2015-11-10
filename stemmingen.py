#!/usr/bin/env python

import os
import sys
import re
import datetime
from pprint import pprint
import json

from BeautifulSoup import BeautifulSoup
import requests

def clean(text):
    return re.sub(r'\s+', u' ', text)

def get_text(node):
    if node is not None:
        try:
            return clean(u''.join(node.findAll(text=True)))
        except AttributeError as e:
            return clean(node)


def get_votes(vote_node):
    votes = []

    table = vote_node.find('table', 'statistics')

    if table is None:
        return []


    for row in table.findAll('tr'):
        cells = row.findAll('td')
        if len(cells) <= 0:
            continue

        try:
            vote_aye = cells[2].img['width']
        except (IndexError, AttributeError, TypeError) as e:
            vote_aye = 0
        try:
            vote_no = cells[3].img['width']
        except (IndexError, AttributeError, TypeError) as e:
            vote_no = 0

        vote = {
            'name': get_text(cells[0]),
            'total': get_text(cells[1]),
            'aye': vote_aye,
            'no': vote_no,
            'details': get_text(cells[4])
        }
        votes.append(vote)

    return votes

def get_vote_page(partial_url):
    url = 'http://www.tweedekamer.nl/kamerstukken/%s' % (partial_url,)
    resp = requests.get(url)
    if resp.status_code != 200:
        return

    soup = BeautifulSoup(resp.content)

    votes = []
    for vote in soup.find('ul', 'search-result-list').findAll('li'):
        props = vote.find('div', 'search-result-properties')
        try:
            submitter_party = vote.find('p', 'submitter').findAll('a')[-1]
        except IndexError as e:
            submitter_party = None
        result = get_text(vote.find('p', 'result'))
        if result is not None:
            result = result.replace(u'Besluit: ', '').replace(u'.', '')

        try:
            vote_type = vote.find('p', 'vote-type').span
        except Exception as e:
            vote_type = None

        try:
            summary = vote.find('table', 'statistics')['summary']
        except Exception as e:
            summary = None

        vote_obj = {
            'id': get_text(props.p),
            'date': get_text(props.find('p', 'date')),
            'title': get_text(vote.h3),
            'category': get_text(vote.find('p', 'search-result-category')),
            'submitter': {
                'name': get_text(vote.find('p', 'submitter').a),
                'party': get_text(submitter_party)
            },
            'result': result,
            'vote-type': get_text(vote_type),
            'votes': get_votes(vote),
            'summary': get_text(summary)
        }
        votes.append(vote_obj)
    return votes

def get_overview_page(url):
    resp = requests.get(url)
    if resp.status_code != 200:
        return

    soup = BeautifulSoup(resp.content)

    next_url_obj = soup.find('a', 'right')
    if next_url_obj is not None:
        next_url = 'http://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen' + next_url_obj['href']
    else:
        next_url = None

    all_urls = []
    for link in soup.findAll('h3'):
        try:
            all_urls += get_vote_page(link.a['href'])
        except Exception as e:
            pass
    return next_url, all_urls


def main():
    today = datetime.datetime.now()
    today_str = today.strftime("%d%%2F%m%%2F%Y")
    # start = today - datetime.timedelta(days=30)
    # start_str = start.strftime("%d%%2F%m%%2F%Y")
    start_str = "01%2F01%2F2015"
    date_str = 'fromdate=%s&todate=%s' % (start_str, today_str,)
    url = 'http://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen?qry=%2A&fld_tk_categorie=Kamerstukken&fld_tk_subcategorie=Stemmingsuitslagen&srt=date%3Adesc%3Adate%2Cprl_volgorde%3Aasc%3Anum&clusterName=Stemmingsuitslagen&Type=Kamerstukken&' + date_str + '&dpp=15&sta=1'
    all_votes = []
    while url is not None:
        print >>sys.stderr, url
        url, votes = get_overview_page(url)
        all_votes += votes
    print json.dumps(all_votes)
    return 0

if __name__ == '__main__':
    sys.exit(main())
