from OpenSSL import SSL
import idna
import datetime
from dateutil.tz import tzutc
import httplib
from socket import socket
import json
import urllib2
from collections import namedtuple
import os


hook_url = os.environ.get('HOOK_URL')
dns_host_name_list = os.environ.get('SSL_CHECK_HOST_LIST').split(',')
port=443
HostInfo = namedtuple(field_names='cert hostname peername', typename='HostInfo')

def check_if_available(full_host_name):
    req = urllib2.Request(full_host_name)
    try:
        urllib2.urlopen(req)
    except urllib2.URLError as e:
        is_available = False
        print('Error, {} URL is not available, reason: {}'.format(dns_host_name, e.reason))
    else:
        is_available = True
    return is_available

def get_certificate(dns_host_name, port):
    hostname_idna = idna.encode(dns_host_name)
    sock = socket()
    
    sock.connect((dns_host_name, port))
    peername = sock.getpeername()
    ctx = SSL.Context(SSL.SSLv23_METHOD) # most compatible
    ctx.check_hostname = False
    ctx.verify_mode = SSL.VERIFY_NONE

    sock_ssl = SSL.Connection(ctx, sock)
    sock_ssl.set_connect_state()
    sock_ssl.set_tlsext_host_name(hostname_idna)
    sock_ssl.do_handshake()
    cert = sock_ssl.get_peer_certificate()
    crypto_cert = cert.to_cryptography()
    sock_ssl.close()
    sock.close()

    return HostInfo(cert=crypto_cert, peername=peername, hostname=dns_host_name)

def check_if_expire(dns_host_name, hook_url):
    date_expire=get_certificate(dns_host_name, port).cert.not_valid_after
    date_current = datetime.datetime.now()
    delta = date_expire - date_current
    # if certificate expires in less than 5 days, send slack alert
    if delta.days < 5:
        text_for_message = '{} SSL certificate expires in less than {} days'.format(dns_host_name, str(delta.days))
        message = {'text': text_for_message}
        post_slack_message(hook_url, message)
    else:
        print('{} certificate is valid for the next {} days'.format(dns_host_name, str(delta.days)))

def post_slack_message(hook_url, message):
    headers = {'Content-type': 'application/json'}
    connection = httplib.HTTPSConnection('hooks.slack.com')
    connection.request('POST',
                       hook_url.replace('https://hooks.slack.com', ''),
                       json.dumps(message),
                       headers)
    response = connection.getresponse()
    print(response.read().decode())

def main(json_input, context):
    for dns_host_name in dns_host_name_list:
        full_host_name = 'https://' + dns_host_name
        if check_if_available(full_host_name) is True:
            check_if_expire(dns_host_name,hook_url)
        else:
            message = {'text': 'https://{} URL is not available!'.format(dns_host_name)}
            post_slack_message(hook_url, message)

if __name__ == '__main__':
    main('','')