variable "build_in_docker" {
  description = "Build in docker for avoid problems with local environment"
  type        = bool
  default     = false
}

variable "certificate_expiration_notice_days" {
  description = "Days prior to the notification of the expired certificate"
  type        = string
  default     = "7"
}

variable "cloudwatch_logs_retention_in_days" {
  description = "Specifies the number of days you want to retain log events in the specified log group. Possible values are: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, and 3653."
  type        = number
  default     = 14
}

variable "function_name" {
  description = "Lambda function name"
  type        = string
  default     = "ssl-checker"
}

variable "hostnames" {
  description = "The list of DNS names that should be monitored. e.g.: [\"example.com\"]"
  type        = list(string)
}

variable "health_check_matcher" {
  description = "The response HTTP codes to use when checking for a healthy responses from a hostnames. e.g.: \"200,201,202-399\"."
  type        = string
  default     = "200-399"
}

# https://nabla-c0d3.github.io/sslyze/documentation/available-scan-commands.html
variable "scan_commands" {
  description = "List of scan commands types witch will run against hostnames. Any type supported by SSLyze."
  type        = list(string)
  default = [
    "certificate_info", "robot", "tls_compression", "tls_fallback_scsv", "heartbleed",
    "http_headers", "openssl_ccs_injection", "session_renegotiation", "tls_1_1_cipher_suites",
    "tls_1_2_cipher_suites", "tls_1_3_cipher_suites"
  ]
}

variable "schedule_expression" {
  description = "The scheduling expression. How often check hostnames. For example, `cron(0/5 * * * ? *)` or `rate(5 minutes)`"
  type        = string
  default     = "cron(0/5 * * * ? *)"
}

variable "slack_hook_url" {
  description = "Slack incoming webhook URL."
  type        = string
}

variable "tags" {
  description = "Tags to apply on created resources"
  type        = map(string)
  default     = {}
}
