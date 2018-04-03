# Cloudwatch event rule
resource "aws_cloudwatch_event_rule" "check-scheduler-event" {
    name = "check-scheduler-event"
    description = "check-scheduler-event"
    schedule_expression = "${var.schedule_expression}"
    depends_on = ["aws_lambda_function.scheduler_lambda"]
}

# Cloudwatch event target
resource "aws_cloudwatch_event_target" "check-scheduler-event-lambda-target" {
    target_id = "check-scheduler-event-lambda-target"
    rule = "${aws_cloudwatch_event_rule.check-scheduler-event.name}"
    arn = "${aws_lambda_function.scheduler_lambda.arn}"
}

# IAM Role for Lambda function
resource "aws_iam_role" "scheduler_lambda" {
    name = "scheduler_lambda"
    assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

data "aws_iam_policy_document" "ec2-access-scheduler" {
    statement {
        actions = [
            "ec2:DescribeInstances",
            "ec2:StopInstances",
            "ec2:StartInstances",
            "ec2:CreateTags"
        ]
        resources = [
            "*",
        ]
    }
}

resource "aws_iam_policy" "ec2-access-scheduler" {
    name = "ec2-access-scheduler"
    path = "/"
    policy = "${data.aws_iam_policy_document.ec2-access-scheduler.json}"
}

resource "aws_iam_role_policy_attachment" "ec2-access-scheduler" {
    role       = "${aws_iam_role.scheduler_lambda.name}"
    policy_arn = "${aws_iam_policy.ec2-access-scheduler.arn}"
}

## create custom role

resource "aws_iam_policy" "scheduler_aws_lambda_basic_execution_role" {
  name        = "scheduler_aws_lambda_basic_execution_role"
  path        = "/"
  description = "AWSLambdaBasicExecutionRole"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "ec2:CreateNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DeleteNetworkInterface"
            ],
            "Resource": "*"
        }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "basic-exec-role" {
    role       = "${aws_iam_role.scheduler_lambda.name}"
    policy_arn = "${aws_iam_policy.scheduler_aws_lambda_basic_execution_role.arn}"
}

# AWS Lambda function
resource "aws_lambda_function" "scheduler_lambda" {
    filename = "${path.module}/package/aws-scheduler.zip"
    function_name = "aws-scheduler"
    role = "${aws_iam_role.scheduler_lambda.arn}"
    handler = "aws-scheduler.handler"
    runtime = "python2.7"
    timeout = 10
    source_code_hash = "${base64sha256(file("${path.module}/package/aws-scheduler.zip"))}"
    vpc_config = {
      security_group_ids = "${var.security_group_ids}"
      subnet_ids = "${var.subnet_ids}"
    }
    environment {
      variables = {
        TAG = "${var.tag}"
        SCHEDULE_TAG_FORCE = "${var.schedule_tag_force}"
        EXCLUDE = "${var.exclude}"
        DEFAULT = "${var.default}"
        TIME = "${var.time}"
      }
    }
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_scheduler" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = "${aws_lambda_function.scheduler_lambda.function_name}"
    principal = "events.amazonaws.com"
    source_arn = "${aws_cloudwatch_event_rule.check-scheduler-event.arn}"
}
