#!/usr/bin/env python3

import json
import os
import re
import sys
import time

import requests


if len(sys.argv) < 2 or sys.argv[1] in ('help', '-h', '--help'):
    print('Usage: %s <CONTENT_FILE>' % sys.argv[0])
    sys.exit(1)

content_file = sys.argv[1]
try:
    cache_file = sys.argv[2]
except IndexError:
    cache_file = 'autolink.json'

word_list = {}

if os.path.isfile(cache_file):
    with open(cache_file) as f:
        word_list = json.load(f)

# Take content of third column, ignore rest of row
r = re.compile(r'^\s*\|[^\|]*\|[^\|]*\|\s*([^\|]+)\s*\|.*$')

words = set()

# Parse single words from column contents
with open(content_file) as f:
    for line in f:
        m = r.search(line)
        if not m:
            continue
        content = m.group(1)
        # Ignore empty fields
        if not content.strip():
            continue
        # Take all words, i.e.
        # 'Acetazolamid (alternativ: Azetazolamid)' becomes
        # ['Acetazolamid', 'alternativ', 'Azetazolamid']
        words.update(re.findall(r'[-\w]{3,}', content))

# Add missing words to word list
for word in words:
    if word in word_list:
        continue
    word_list[word] = {}

# Lookup each word on DocCheck and Wikipedia
for word, links in word_list.items():
    should_sleep = False

    if 'dc' not in links:
        url = 'https://flexikon.doccheck.com/de/%s' % word
        r = requests.head(url)
        if r.status_code != 200:
            word_list[word]['dc'] = '-'
        else:
            word_list[word]['dc'] = url

        should_sleep = True

    if 'wp' not in links:
        url = 'https://de.wikipedia.org/wiki/%s' % word
        r = requests.head(url)
        if r.status_code != 200:
            word_list[word]['wp'] = '-'
        else:
            word_list[word]['wp'] = url

        should_sleep = True

    # Don't send too many requests at once
    if should_sleep:
        time.sleep(2)

# Write out cache file
with open(cache_file, 'w') as f:
    json.dump(word_list, f, indent=2, sort_keys=True)
