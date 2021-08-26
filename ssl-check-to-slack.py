#!/usr/bin/env python3
import os
import sys
import json
import logging
import http.client
from sslyze.errors import ServerHostnameCouldNotBeResolved, ConnectionToServerFailed
from sslyze import ServerNetworkLocationViaDirectConnection
from sslyze import ServerConnectivityTester
from sslyze import Scanner
from sslyze import ServerScanRequest
from sslyze import ScanCommand
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def read_env_variable_or_die(env_var_name):
    value = os.environ.get(env_var_name, '')
    if value == '':
        message = f'Env variable {env_var_name} is not defined or set to empty string. '
        message += 'Set it to non-empty string and try again'
        logger.error(message)
        raise EnvironmentError(message)
    return value


def get_response_status(hostname,endpoint):
    connection = http.client.HTTPSConnection(hostname)
    connection.request("GET", endpoint)
    response = connection.getresponse()
    return response.status


def split_matcher(matcher):
    result = []
    comma_list = matcher.split(',')
    for item in comma_list:
        dash_list = item.split('-')
        if len(dash_list) == 1:
            result.append(int(dash_list[0]))
        else:
            for element in list(range(int(dash_list[0]), int(dash_list[1]) + 1)):
                result.append(element)
    return set(result)


# Slack web hook example
# https://hooks.slack.com/services/XXXXXXX/XXXXXXX/XXXXXXXXXXXX
def post_slack_message(hook_url, message):
    logger.info(f'Posting the following message:\n{message}')
    headers = {'Content-type': 'application/json'}
    connection = http.client.HTTPSConnection('hooks.slack.com')
    connection.request('POST',
                       hook_url.replace('https://hooks.slack.com', ''),
                       message,
                       headers)
    response = connection.getresponse()
    print(response.read().decode())


def format_error_to_slack_message(error_message):
    message = {
        'attachments': [{
            'color': '#8963B9',
            'title': 'Ooopsy oopsy!',
            'text': f'Check logs! Failed with error: {error_message}'
        }]
    }
    return json.dumps(message)


def format_ssl_check_to_slack_message(hostname, message):
    message = {
        'attachments': [{
            'color': '#FF0000',
            'title': f'{hostname}',
            'text': f'{message}'
        }]
    }
    return json.dumps(message)


def main(event, context):
    if os.environ.get('DEBUG', False):
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                            format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logger.info('Reading configuration...')
    slack_web_hook_url = read_env_variable_or_die('HOOK_URL')
    hostnames = read_env_variable_or_die('HOSTNAMES').split(',')
    health_check_matcher = split_matcher(str(os.environ.get('HEALTH_CHECK_MATCHER', '200-399,201')))
    certificate_expiration_notice_days = int(os.environ.get('CERTIFICATE_EXPIRATION_NOTICE_DAYS', '7'))
    # https://nabla-c0d3.github.io/sslyze/documentation/available-scan-commands.html
    scan_commands = set(os.environ.get('SCAN_COMMANDS',
                                       'certificate_info,robot,tls_compression,tls_fallback_scsv,heartbleed,'
                                       'http_headers ,openssl_ccs_injection,session_renegotiation,'
                                       'tls_1_1_cipher_suites,tls_1_2_cipher_suites,tls_1_3_cipher_suites'
                                       ).replace(' ', '').split(',')).union({'certificate_info'})
    logger.info('Configuration is OK')
    logger.info(f'Going to check: {hostnames}')
    servers_to_scan = []
    # First validate that we can connect to the servers we want to scan
    for hostname in hostnames:
        # DNS check. Try to resolve hostname.
        try:
            # for urlparse to correctly parse the address it needs a scheme in fron of the domain name
            # otherwise it might get confused
            hostname_with_scheme = hostname
            if not hostname_with_scheme.startswith('https://'):
                hostname_with_scheme = f'https://{hostname}'
                logger.debug(f'prepend scheme to {hostname} so it is {hostname_with_scheme}')
            hostname_parsed = urlparse(hostname_with_scheme)
            logger.debug(f'hostname pasrsing result: {hostname_parsed}')
            path = "/" if hostname_parsed.path == "" else hostname_parsed.path
            host = hostname_parsed.netloc
            logger.debug(f'parsed {hostname} to host {host} and path {path}')
            logger.debug(f'DNS: {host} - Testing...')
            server_location = ServerNetworkLocationViaDirectConnection.with_ip_address_lookup(host, 443)
            logger.debug(f'DNS: {host} - OK')
            # Connection check. Try to connect to hostname.
            try:
                logger.debug(f'Connect: {hostname} - Testing...')
                server_info = ServerConnectivityTester().perform(server_location)
                response_status = get_response_status(host, path)
                if response_status not in health_check_matcher:
                    raise ConnectionToServerFailed(server_info.server_location, server_info.network_configuration,
                                                   error_message=f'HTTP Error. Status code: {response_status}')
                servers_to_scan.append(server_info)
                logger.debug(f'Connect: {hostname} - OK')
            except ConnectionToServerFailed as e:
                logger.error(f'Connect: {hostname} - ERROR: {e.error_message}')
                message = f'URL is not available! Connect error: {e.error_message}'
                post_slack_message(slack_web_hook_url,
                                   format_ssl_check_to_slack_message(f'https://{hostname}', message))
            except Exception as e:
                logger.error(f'Connect: {hostname} - ERROR: {e}')
                post_slack_message(slack_web_hook_url, format_error_to_slack_message(str(e)))
        except ServerHostnameCouldNotBeResolved as e:
            logger.error(f'DNS: {hostname} - ERROR: {e}')
            message = f'URL is not available! DNS error: {e}'
            post_slack_message(slack_web_hook_url, format_ssl_check_to_slack_message(f'https://{hostname}', message))
        except Exception as e:
            logger.error(f'DNS: {hostname} - ERROR: {e}')
            post_slack_message(slack_web_hook_url, format_error_to_slack_message(str(e)))

    scanner = Scanner()

    # Then queue some scan commands for each server
    for server_info in servers_to_scan:
        server_scan_req = ServerScanRequest(
            server_info=server_info, scan_commands=scan_commands,
        )
        scanner.queue_scan(server_scan_req)

    # Then retrieve the result of the scan commands for each server
    for server_scan_result in scanner.get_results():
        server_scan_result_hostname = server_scan_result.server_info.server_location.hostname
        logger.info(f'Results for {server_scan_result_hostname}:')
        # Scan commands that were run with no errors
        try:
            certificate_info_result = server_scan_result.scan_commands_results[ScanCommand.CERTIFICATE_INFO]
            logger.info(f'Certificate info for {server_scan_result_hostname}:')
            subject_matches_hostname = []
            chain_has_valid_order = []
            for cert_deployment in certificate_info_result.certificate_deployments:
                subject_matches_hostname.append(cert_deployment.leaf_certificate_subject_matches_hostname)
                chain_has_valid_order.append(cert_deployment.received_chain_has_valid_order)
                # print(f'Leaf certificate: \n{cert_deployment.received_certificate_chain_as_pem[0]}')
                not_valid_before = cert_deployment.received_certificate_chain[0].not_valid_before
                not_valid_after = cert_deployment.received_certificate_chain[0].not_valid_after
                date_current = datetime.now()
                if date_current < not_valid_before:
                    logger.error(f'TLS: {server_scan_result_hostname} - ERROR: Not valid before: {not_valid_before}. '
                                 f'Now is: {date_current}')
                    message = f'SSL certificate not valid before: {not_valid_before}. Now is: {date_current}'
                    post_slack_message(slack_web_hook_url,
                                       format_ssl_check_to_slack_message(f'https://{server_scan_result_hostname}',
                                                                         message))
                delta = not_valid_after - date_current
                if delta.days <= certificate_expiration_notice_days:
                    logger.error(f'TLS: {server_scan_result_hostname} - ERROR: Expires in less than {delta.days} days')
                    message = f'SSL certificate expires in less than: {delta.days} days.'
                    post_slack_message(slack_web_hook_url,
                                       format_ssl_check_to_slack_message(f'https://{server_scan_result_hostname}',
                                                                         message))
                else:
                    logger.info(f'TLS: {server_scan_result_hostname} - OK: Valid for next {delta.days} days')
            if not any(subject_matches_hostname):
                logger.error(f'TLS: {server_scan_result_hostname} - ERROR: No subject matches')
                message = 'SSL certificate no subject matches.'
                post_slack_message(slack_web_hook_url,
                                   format_ssl_check_to_slack_message(f'https://{server_scan_result_hostname}', message))
            if not all(chain_has_valid_order):
                logger.error(f'TLS: {server_scan_result_hostname} - ERROR: Chain has no valid order')
                message = 'SSL certificate chain has no valid order.'
                post_slack_message(slack_web_hook_url,
                                   format_ssl_check_to_slack_message(f'https://{server_scan_result_hostname}', message))
        except KeyError:
            pass
        # Scan commands that were run with errors
        for scan_command, error in server_scan_result.scan_commands_errors.items():
            logger.error(f'{scan_command}: {server_scan_result_hostname} - ERROR: {error.exception_trace}')
            message = f'{scan_command} failed with error: {error.exception_trace}'
            post_slack_message(slack_web_hook_url,
                               format_ssl_check_to_slack_message(f'https://{server_scan_result_hostname}', message))


if __name__ == '__main__':
    main("", "")
