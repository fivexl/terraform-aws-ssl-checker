#!/usr/bin/env bash

set -ex

export SCAN_COMMANDS="certificate_info,robot,tls_compression,tls_fallback_scsv,heartbleed,http_headers,openssl_ccs_injection,session_renegotiation,tls_1_1_cipher_suites,tls_1_2_cipher_suites,tls_1_3_cipher_suites"
export CERTIFICATE_EXPIRATION_NOTICE_DAYS=7
export HEALTH_CHECK_MATCHER=200-399
export HOOK_URLS="https://hooks.slack.com/services/XXXXXXX/XXXXXXX/XXXXXXXXXXXX"
export DEBUG=true
export HOSTNAMES="google.com,g00gle.com,fivexl.io"

python3 ssl-check-to-slack.py