# terraform-aws-lambda-scheduler
Stop and start EC2 and RDS instances according to schedule via lambda and terraform.

# Overview

The scheduler looks at the schedule tag to see if it needs to stop or start and instance.
It works by setting a tag (default name schedule) to a string giving the stop and start time hour for each day.

A schedule tag for an EC2 instance is json and looks like:
```json
{"mon": {"start": 7, "stop": 20},"tue": {"start": 7, "stop": 20},"wed": {"start": 7, "stop": 20},"thu": {"start": 7, "stop": 20}, "fri": {"start": 7, "stop": 20}}
```

On a RDS instance the schedule tag is a string of keyword parameters separated by a space.
```
"mon_start=7 mon_stop=20 tue_start=7 tue_stop=20 wed_start=7 wed_stop=20 thu_start=7 thu_stop=20 fri_start=7 fri_stop=20"
```
NOTE: This is because of restrictions in the characters the tags on RDS instance support.

The scheduler can be configured to add a default schedule tag to EC2 and RDS instances it finds without a schedule tag.
It ignores instances that are part of autoscaling groups assuming scheduling actions can be used to stop and start these instances.


## Requirements

This module requires Terraform version `0.10.x` or newer.

## Dependencies

This module depends on a correctly configured [AWS Provider](https://www.terraform.io/docs/providers/aws/index.html) in your Terraform codebase.

## Usage

```
module "lambda-scheduler" {
  source = "neillturner/lambda-scheduler/aws"
  version = "0.x.0"
  schedule_expression = "cron(5 * * * ? *)"
  tag = "schedule"
  schedule_tag_force = "true"
  ec2_schedule = "true"
  rds_schedule = "true"
  default = "{\"mon\": {\"start\": 7, \"stop\": 20},\"tue\": {\"start\": 7, \"stop\": 20},\"wed\": {\"start\": 7, \"stop\": 20},\"thu\": {\"start\": 7, \"stop\": 20}, \"fri\": {\"start\": 7, \"stop\": 20}}"
  time = "Europe/London"
}
```
## variables

### schedule_expression
The aws cloudwatch event rule schedule expression that specifies when the scheduler runs.

Default = "cron(5 * * * ? *)"  i.e. 5 minuts past the hour. for debugging use "rate(5 minutes)" See [ScheduledEvents](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html)

### tag
The tag name used on the EC2 and RDS instance to contain the schedule string for the instance. default is 'schedule'

### schedule_tag_force
Whether to force the EC2 and RDS instance to have the default schedule tag if no schedule tag exists for the instance.

Default is false. If set to true it with create a default schedule tag for each instance it finds.

### exclude
String containing comma separated list of ECS2 and RDS instance ids to exclude from scheduling.

### default
The default schedule tag containing json schedule information to add to EC2 or RDS instance when schedule_tag_force set to true.

NOTE: On a RDS instance the tag is converted to a string of keyword parameters separated by a space.  i.e.
```
"mon_start=7 mon_stop=20"
```
because of restrictions in the characters the tags on RDS instance support.

Default for default is:
```json
{"mon": {"start": 7, "stop": 20},"tue": {"start": 7, "stop": 20},"wed": {"start": 7, "stop": 20},"thu": {"start": 7, "stop": 20}, "fri": {"start": 7, "stop": 20}}
```

### time
Timezone to use for scheduler. Can be 'local', 'gmt' or an Olson timezone from https://gist.github.com/ykessler/3349954. default is 'gmt'. local time is for the AWS region.

### ec2_schedule
Whether to do scheduling for EC2 instances. default = "true".

### rds_schedule
Whether to do scheduling for RDS instances. default = "true".

### security_group_ids
list of the vpc security groups to run lambda scheduler in. Defaults to []. Usually this does not need to be specified.

### subnet_ids
list of subnet_ids that the scheduler runs in. Defaults to []. Usually this does not need to be specified.

### resource_name_prefix
The prefix to apply to resource names. E.g. setting this to `cluster1-` will create the Lambda as `cluster1-aws-scheduler` rather than `aws-schedule`. default = "".