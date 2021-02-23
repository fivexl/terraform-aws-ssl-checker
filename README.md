[![FivexL](https://releases.fivexl.io/fivexlbannergit.jpg)](https://fivexl.io/)

# Configuration

Configuration is done via env variables

* `HOOK_URL` - Slack web hook URL where to send events. This is a mandatory parameter.
* `SSL_CHECK_HOST_LIST` - Comma separated list of domain names. This is a mandatory parameter.
* `CERTIFICATE_REMAINING_DAYS` -  How many days before the expiration date of the certificate to send reminders. Default - `'7'`
