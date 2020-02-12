import json
import os
import requests
import socket
import threading


def download_file(name, url):
    res = requests.head(url)
    if not res:
        return None

    filetype = res.headers['content-type'].split('/')[-1]
    filename = '{}.{}'.format(name, filetype)
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), filename)

    if os.path.isfile(path):
        return filename

    res = requests.get(url, stream=True)
    if not res.ok:
        return None

    with open(path, 'wb') as f:
        for chunk in res:
            f.write(chunk)

    return filename

def prefix_tmp(key):
    return 'tmp_{}'.format(key)

def ib_notify(path, data=''):
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.sendto('{}:{}'.format(path, data).encode(), ('127.0.0.1', 4444))

def ib_update_selection(selection_id):
    ib_notify('selector/selection', selection_id + 1)

def ib_update_selector(entries, messages=[]):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 4444))
    s.recv(1000)
    s.send('selector\n'.encode())
    s.recv(1000)
    try:
        s.send(json.dumps({'entries': entries, 'messages': messages}, ensure_ascii=False).encode('utf8'))
        s.send('\n'.encode())
    except:
        return False
    finally:
        s.close()

    return True
