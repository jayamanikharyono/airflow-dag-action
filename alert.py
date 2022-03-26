"""
Created on Mon Oct 25 16:49:07 2021

@author: jayaharyonomanik
"""

import os
import json
import logging
import argparse
from github import Github


def comment_pr(repo_token, filename):
    file = open(filename)
    message = file.read()
    g = Github(repo_token)
    repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
    event_payload = open(os.getenv('GITHUB_EVENT_PATH')).read()
    json_payload =  json.loads(event_payload)
    logging.info(json_payload)
    pr = repo.get_pull(json_payload['number'])
    pr.create_issue_comment(message)
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--log_filename', action = 'store', type = str, required = True)
    parser.add_argument('--repo_token', action = 'store', type=str, required = True)
    args = parser.parse_args()
    try:
        comment_pr(args.repo_token, args.log_filename)
    except Exception as e:
        print(e.args)
        logging.info("PR comment not supported on current event")
