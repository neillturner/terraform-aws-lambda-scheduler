# terraform-aws-lambda-scheduler
Stop and start EC2 instances according to schedule via lambda and terraform.

# Overview

The scheduler looks at the json on the schedule tag to see if it needs to stop or start and instance.
It works by setting a tag (default name schedule) to a json string giving the stop and start time hour for each day.

A schedule tag json looks like:
```json
{"mon": {"start": 7, "stop": 20},"tue": {"start": 7, "stop": 20},"wed": {"start": 7, "stop": 20},"thu": {"start": 7, "stop": 20}, "fri": {"start": 7, "stop": 20}}
```

The scheduler can be configured to add a default schedule tag to instances it finds without a schedule tag.
It ignores instances that are part of autoscaling groups assuming scheduling actions can be used to stop and start these instances.


## Requirements

This module requires Terraform version `0.10.x` or newer.

## Dependencies

This module depends on a correctly configured [AWS Provider](https://www.terraform.io/docs/providers/aws/index.html) in your Terraform codebase.

## Usage

```
module "lambda-scheduler" {
  source = "neillturner/lambda-scheduler/aws"
  version = "0.1.1"
  schedule_expression = "cron(5 * * * ? *)"
  tag = "schedule"
  schedule_tag_force = true
  default = "\{\"mon": {\"start\": 7, \"stop\": 20},\"tue\": {\"start\": 7, \"stop\": 20},\"wed\": {\"start\": 7, \"stop\": 20},\"thu\": {\"start\": 7, \"stop\": 20}, \"fri\": {\"start\": 7, \"stop\": 20}}"
  time = "local"
}
```
## variables

### schedule_expression
The aws cloudwatch event rule schedule expression that specifies when the scheduler runs.

Default = "cron(5 * * * ? *)"  i.e. 5 minuts past the hour. for debugging use "rate(5 minutes)" See [ScheduledEvents](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html)

### tag
The tag name used on the EC2 instance to contain the schedule json string for the instance. default is 'schedule'

### schedule_tag_force
Whether to force the EC2 instance to have the default schedule tag if no schedule tag exists for the instance.

Default is false. If set to true it with create a default schedule tag for each instance it finds.

### exclude
String containing comma separated list of instance ids to exclude from scheduling.

### default
The default schedule tag containing json schedule information to add to instance when schedule_tag_force set to true.

Default for default is:
```json
{"mon": {"start": 7, "stop": 20},"tue": {"start": 7, "stop": 20},"wed": {"start": 7, "stop": 20},"thu": {"start": 7, "stop": 20}, "fri": {"start": 7, "stop": 20}}
```

### time
Timezone to use for scheduler. Can be 'local' or 'gmt'.

Default is gmt. local time is for the AWS region.

### security_group_ids
list of the vpc security groups to run lambda scheduler in. Defaults to []. Usually this is sufficent.

### subnet_ids
list of subnet_ids that the scheduler runs in. Defaults to []. Usually this is sufficent.

