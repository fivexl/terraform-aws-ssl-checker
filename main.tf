resource "aws_cloudwatch_event_rule" "rule" {
  name                = var.function_name
  description         = "Fires every 5 min"
  schedule_expression = "cron(0/5 * * * ? *)"
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
  timeout                           = length(var.host_dns_name) * 10 + 20 #10s per domain + 20s
  publish                           = true
  cloudwatch_logs_retention_in_days = 14
  attach_policy                     = true
  policy                            = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  allowed_triggers = {
    AllowExecutionFromCloudWatch = {
      principal  = "events.amazonaws.com"
      source_arn = aws_cloudwatch_event_rule.rule.arn
    }
  }
  environment_variables = {
    HOOK_URL            = var.slack_hook_url
    SSL_CHECK_HOST_LIST = var.host_dns_name
  }
  tags = var.tags
}

resource "aws_cloudwatch_event_target" "target" {
  rule      = aws_cloudwatch_event_rule.rule.name
  target_id = "trigger_ssl_checker"
  arn       = module.lambda.this_lambda_function_arn
}
