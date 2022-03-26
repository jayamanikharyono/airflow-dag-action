# -*- coding: utf-8 -*-
"""
Created on Mon Oct 25 16:49:07 2021

@author: jayaharyonomanik
"""

import os
import json
import argparse
from github import Github
from unidecode import unidecode


def comment_pr(repo_token, filename):
    file = open(filename)
    message = file.read()

    g = Github(repo_token)
    repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
    event_payload = open(os.getenv('GITHUB_EVENT_PATH')).read()
    json_payload =  json.loads(event_payload)
    if json_payload.get('number') is not None:
        pr = repo.get_pull(json_payload.get('number'))
        pr.create_issue_comment("```" + unidecode(message).replace("�", "") + "```")
    else:
        print("PR comment not supported on current event")
        print(message)
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--log_filename', action = 'store', type = str, required = True)
    parser.add_argument('--repo_token', action = 'store', type=str, required = True)
    args = parser.parse_args()
    comment_pr(args.repo_token, args.log_filename)
