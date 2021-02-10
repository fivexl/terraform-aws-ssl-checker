variable "function_name" {
    description = "Lambda function name"
    default     = "fivexl-ssl-checker"
    type        = string
}

variable "host_dns_name" {
    description = "The host DNS name that should be monitored, for example mywebsite.com"
    type        = string
}

variable "slack_hook_url" {
    description = "Specifies where to send Slack messages"
    type        = string
}

variable "tags" {
    description = "Tags to attach to resources"
    default     = {}
    type        = map(string)
}
