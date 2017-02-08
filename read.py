import re
import time
import socket
import os
import sys

import requests

hostname = socket.gethostname().replace('.', '-').lower()

xmr_api_host = os.environ.get('XMR_API_HOST', 'localhost')
xmr_api_port = os.environ.get('XMR_API_PORT', 8000)
push_interval = float(os.environ.get('PUSH_INTERVAL', 10))
graphite_host = os.environ.get('GRAPHITE_HOST')
graphite_port = int(os.environ.get('GRAPHITE_PORT'))

def collect_metric(name, value, timestamp):
    sock = socket.socket()
    try:
        sock.connect( (graphite_host, graphite_port) )
    except Exception as e:
        sys.stderr.write("Cannot push stats to {}:{}\n".format(graphite_host, graphite_port))
        sock.close()
        return
    payload = "xmr.hashsec.%s.%s %s %d\n" % (hostname, name, value, timestamp)
    sys.stdout.write(payload)
    sock.send(payload)
    sock.close()

def now():
    return int(time.time())

while True:
    try:
        r = requests.get("http://{}:{}/h".format(xmr_api_host, xmr_api_port))
    except Exception as e:
        sys.stderr.write("{}\n".format(e))
        time.sleep(push_interval)
        continue
    data = r.text
    m = re.search(r'^Totals:\s+(?P<v2dot5s>[^\s]+)\s+(?P<v60s>[^\s]+)\s+(?P<v15m>[^\s]+)', data, re.MULTILINE)
    try:
        v2dot5s, v60s, v15m = m.groups()
    except AttributeError:
        sys.stderr.write("Unable to fetch stats in http://{}:{}\n".format(xmr_api_host, xmr_api_port))
        time.sleep(push_interval)
        continue
    if v2dot5s > 0:
        collect_metric("last2dot5s", v2dot5s, now())
    if v60s > 0:
        collect_metric("last60s", v60s, now())
    if v15m > 0:
        collect_metric("last15m", v15m, now())
    time.sleep(push_interval)

