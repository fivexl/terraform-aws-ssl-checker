resource "aws_cloudwatch_event_rule" "rule" {
  name                = var.function_name
  description         = "Scheduler for ${var.function_name}"
  schedule_expression = var.schedule_expression
  tags                = var.tags
}

module "lambda" {
  source        = "terraform-aws-modules/lambda/aws"
  version       = "1.39.0"
  function_name = var.function_name
  description   = "Lambda to monitor app https endpoint availability and SSL certificate validity."
  handler       = "ssl-check-to-slack.main"
  source_path = [
    {
      path             = "${path.module}/ssl-check-to-slack.py",
      pip_requirements = "${path.module}/requirements.txt",
    }
  ]
  runtime                           = "python3.8"
  timeout                           = length(var.hostnames) * 10 + 20 #10s per domain + 20s
  publish                           = true
  cloudwatch_logs_retention_in_days = var.cloudwatch_logs_retention_in_days
  attach_policy                     = true
  policy                            = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  allowed_triggers = {
    AllowExecutionFromCloudWatch = {
      principal  = "events.amazonaws.com"
      source_arn = aws_cloudwatch_event_rule.rule.arn
    }
  }
  environment_variables = {
    HOOK_URL                           = var.slack_hook_url
    HOSTNAMES                          = join(",", var.hostnames)
    CERTIFICATE_EXPIRATION_NOTICE_DAYS = var.certificate_expiration_notice_days
    SCAN_COMMANDS                      = join(",", var.scan_commands)
  }
  tags = var.tags
}

resource "aws_cloudwatch_event_target" "target" {
  rule      = aws_cloudwatch_event_rule.rule.name
  target_id = var.function_name
  arn       = module.lambda.this_lambda_function_arn
}
