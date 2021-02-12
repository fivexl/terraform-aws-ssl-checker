data "aws_iam_policy" "lambda_basic_execution" {
  arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role" "role" {
  name               = "${var.function_name}-lambda-execution-role"
  path               = "/"
  assume_role_policy = data.aws_iam_policy_document.sts.json
}

resource "aws_iam_role_policy_attachment" "lambda_attach" {
  role       = aws_iam_role.role.name
  policy_arn = data.aws_iam_policy.lambda_basic_execution.arn
}

data "aws_iam_policy_document" "sts" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

module lambda {
  source = "github.com/terraform-aws-modules/terraform-aws-lambda?ref=v1.22.0"

  function_name                     = "${var.function_name}"
  description                       = "Lambda to monitor app https endpoint availability and SSL certificate validity."
  handler                           = "main.main"
  runtime                           = "python2.7"
  memory_size                       = "128"
  timeout                           = "20"
  cloudwatch_logs_retention_in_days = "5"
  lambda_role                       = aws_iam_role.role.arn

  create_package         = false
  local_existing_package = "lambda.zip"

  environment_variables = {
    HOOK_URL = var.slack_hook_url
    SSL_CHECK_HOST = var.host_dns_name
  }

  tags = var.tags
}

data "archive_file" "package" {
  type        = "zip"
  output_path = "lambda.zip"
  source_dir  = "${path.module}/src/"
}

resource "aws_cloudwatch_event_rule" "rule" {
  name                = var.function_name
  description         = "Fires every 5 min"
  schedule_expression = "cron(0/5 * * * ? *)"
}

resource "aws_cloudwatch_event_target" "target" {
  rule      = aws_cloudwatch_event_rule.rule.name
  target_id = "trigger_ssl_checker"
  arn       = module.lambda.this_lambda_function_arn
}

resource "aws_cloudwatch_log_group" "log-group" {
  name              = var.function_name
  retention_in_days = 7
}

resource "aws_lambda_permission" "permission" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda.this_lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.rule.arn
}