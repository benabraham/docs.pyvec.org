import os
import re
from datetime import date
from pathlib import Path
from textwrap import indent

import requests
from jinja2 import Template


REACTIONS_API_MEDIA_TYPE = 'application/vnd.github.squirrel-girl-preview'
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
URL = 'https://api.github.com/repos/pyvec/money/issues'


res = requests.get(URL, headers={'Accept': REACTIONS_API_MEDIA_TYPE,
                                 'Authorization': f'token {GITHUB_TOKEN}'},
                   params={'per_page': 100, 'state': 'closed'})
res.raise_for_status()


def to_date(iso_datetime_string):
    iso_date_string, _ = iso_datetime_string.split('T')
    return date.fromisoformat(iso_date_string)


def remove_comments(html):
    return re.sub(r'<!--[^<]+-->', '', html).strip()


grants = []
for issue in res.json():
    url = issue['reactions']['url']
    res = requests.get(url, headers={'Accept': REACTIONS_API_MEDIA_TYPE,
                                     'Authorization': f'token {GITHUB_TOKEN}'})
    res.raise_for_status()
    reactions = res.json()

    body = remove_comments(issue['body'])
    labels = [label['name'] for label in issue['labels']]
    grants.append({
        'title': issue['title'],
        'description': body,
        'description_indented': indent(body, '    '),
        'url': issue['html_url'],
        'user': {
            'username': issue['user']['login'],
            'url': issue['user']['html_url'],
        },
        'is_approved': 'approved' in labels,
        'created_at': to_date(issue['created_at']),
        'closed_at': to_date(issue['closed_at']),
        'votes': [{
            'username': reaction['user']['login'],
            'url': reaction['user']['html_url'],
            'content': reaction['content'],
        } for reaction in reactions],
    })


tpl_path = Path(__file__).parent.parent / 'operations' / 'grants.rst.template'
tpl = Template(tpl_path.read_text())
print(tpl.render(grants=grants))
