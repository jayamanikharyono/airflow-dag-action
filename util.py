# -*- coding: utf-8 -*-

import os
import json
import argparse
from github import Github

def comment_pr(repo_token, filename):
    file = open(filename)
    comment = file.read()
    g = Github(repo_token)
    repo = g.get_repo(os.environ['GITHUB_REPOSITORY'])
    event_payload = open(os.environ['GITHUB_EVENT_PATH']).read()
    json_payload =  json.loads(event_payload)
    pr = repo.get_pull(json_payload['number'])
    pr.create_issue_comment(message)
    return True


parser = argparse.ArgumentParser(allow_abbrev=False)
parser.add_argument('--filename', action = 'store', type = str, required = True)
parser.add_argument('--repo_token', action = 'store', type=str, required = True)

args = parser.parse_args()
comment_pr(args.repo_token, args.filename)
