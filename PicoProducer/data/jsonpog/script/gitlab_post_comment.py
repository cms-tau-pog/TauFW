#!/usr/bin/env python3
import os
import sys
from urllib import parse, request

iid = os.environ['CI_MERGE_REQUEST_IID']
project = os.environ['CI_MERGE_REQUEST_PROJECT_PATH'].replace("/", "%2F")

if 'GITLAB_API_TOKEN' in os.environ:
    token = os.environ['GITLAB_API_TOKEN'];
else:
    token=("".join(open("%s/private/gitlab-token" % os.environ['HOME']))).strip()

review_body = ""
for f in sys.argv[1:]:
    if os.path.isfile(f):
        review_body += "".join(open(f)) + "\n"

blob = parse.urlencode({'body': review_body.replace("\n", "\r\n").replace('"', '\"').encode('utf-8')})
blob = blob.encode('utf-8')
req = request.Request(f"https://gitlab.cern.ch/api/v4/projects/{project}/merge_requests/{iid}/notes", blob, headers={'PRIVATE-TOKEN': token})
req.get_method = lambda: 'POST'
response = request.urlopen(req)
data = response.read().decode('utf-8')
print(data)

