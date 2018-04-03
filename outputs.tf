output "scheduler_lambda_arn" {
  value = "${aws_lambda_function.scheduler_lambda.arn}"
}