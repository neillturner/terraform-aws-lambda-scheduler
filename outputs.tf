output "scheduler_lambda_arn" {
  value = aws_lambda_function.scheduler_lambda.arn
}

output "scheduler_lambda_function_name" {
  value = aws_lambda_function.scheduler_lambda.function_name
}
