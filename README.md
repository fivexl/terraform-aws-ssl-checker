[![FivexL](https://releases.fivexl.io/fivexlbannergit.jpg)](https://fivexl.io/)

# Configuration

Configuration is done via env variables

* `HOOK_URL` - Slack web hook URL where to send events. This is a mandatory parameter.
* `HOSTNAMES` - Comma separated string with domain names. This is a mandatory parameter.
* `CERTIFICATE_EXPIRATION_NOTICE_DAYS` -  How many days before the expiration date of the certificate to send reminders. Default - `'7'`
* `SCAN_COMMANDS` - Comma separated string with scan commands types witch will run against hostnames. Any type supported by SSLyze. 