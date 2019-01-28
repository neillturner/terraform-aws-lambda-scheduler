import boto3

import sys, os, json, logging, datetime, time


logger = logging.getLogger()
logger.setLevel(logging.INFO)

aws_region = None

create_schedule_tag_force = os.getenv('SCHEDULE_TAG_FORCE', 'False')
create_schedule_tag_force = create_schedule_tag_force.capitalize()
logger.info("create_schedule_tag_force is %s." % create_schedule_tag_force)

rds_schedule = os.getenv('RDS_SCHEDULE', 'True')
rds_schedule = rds_schedule.capitalize()
logger.info("rds_schedule is %s." % rds_schedule)

ec2_schedule = os.getenv('EC2_SCHEDULE', 'True')
ec2_schedule = ec2_schedule.capitalize()
logger.info("ec2_schedule is %s." % ec2_schedule)

def init():
    # Setup AWS connection
    aws_region     = os.getenv('AWS_REGION', 'us-east-1')

    global ec2
    logger.info("-----> Connecting to region \"%s\"", aws_region)
    ec2 = boto3.resource('ec2', region_name=aws_region)
    logger.info("-----> Connected to region \"%s\"", aws_region)

#
# Add default 'schedule' tag to instance.
# (Only if instance.id not excluded and create_schedule_tag_force variable is True.
#
def create_schedule_tag(instance):
    exclude_list = os.environ.get('EXCLUDE').split(',')

    autoscaling = False
    for tag in instance.tags:
        if 'aws:autoscaling:groupName' in tag['Key']:
           autoscaling = True

    if (create_schedule_tag_force == 'True') and (instance.id not in exclude_list) and (not autoscaling):
        try:
            schedule_tag =  os.getenv('TAG', 'schedule')
            tag_value =  os.getenv('DEFAULT', '{"mon": {"start": 7, "stop": 20},"tue": {"start": 7, "stop": 20},"wed": {"start": 7, "stop": 20},"thu": {"start": 7, "stop": 20}, "fri": {"start": 7, "stop": 20}}')
            logger.info("About to create %s tag on EC2 instance %s with value: %s" % (schedule_tag,instance.id,tag_value))
            tags = [{
                "Key" : schedule_tag,
                "Value" : tag_value
            }]
            instance.create_tags(Tags=tags)
        except Exception as e:
            logger.error("Error adding Tag to EC2 instance: %s" % e)
    else:
        if (autoscaling):
            logger.info("Ignoring EC2 instance %s. It is part of an auto scaling group" % instance.id)
        else:
            logger.info("No 'schedule' tag found on EC2 instance %s. Use create_schedule_tag_force option to create the tag automagically" % instance.id)

#
# Loop EC2 instances and check if a 'schedule' tag has been set. Next, evaluate value and start/stop instance if needed.
#
def check():
    # Get all reservations.
    instances = ec2.instances.filter(
    Filters=[{'Name': 'instance-state-name', 'Values': ['pending','running','stopping','stopped']}])

    # Get current day + hour (using gmt by default if time parameter not set to local)
    time_zone =  os.getenv('TIME', 'gmt')
    if time_zone == 'local':
        hh  = int(time.strftime("%H", time.localtime()))
        day = time.strftime("%a", time.localtime()).lower()
        logger.info("-----> Checking for EC2 instances to start or stop for 'local time' hour \"%s\"", hh)
    else:
        hh  = int(time.strftime("%H", time.gmtime()))
        day = time.strftime("%a", time.gmtime()).lower()
        logger.info("-----> Checking for EC2 instances to start or stop for 'gmt' hour \"%s\"", hh)

    started = []
    stopped = []

    schedule_tag = os.getenv('TAG', 'schedule')
    logger.info("-----> schedule tag is called \"%s\"", schedule_tag)
    if not instances:
        logger.error('Unable to find any EC2 Instances, please check configuration')

    for instance in instances:
        logger.info("Evaluating EC2 instance \"%s\"", instance.id)

        try:
            data = "{}"
            for tag in instance.tags:
                if schedule_tag in tag['Key']:
                    data = tag['Value']
                    break
            else:
                # 'schedule' tag not found, create if appropriate.
                create_schedule_tag(instance)

            schedule = json.loads(data)

            try:
                if hh == schedule[day]['start'] and not instance.state["Name"] == 'running':
                    logger.info("Starting EC2 instance \"%s\"." %(instance.id))
                    started.append(instance.id)
                    ec2.instances.filter(InstanceIds=[instance.id]).start()
            except:
                pass # catch exception if 'start' is not in schedule.

            try:
                if hh == schedule[day]['stop']:
                    logger.info("Stopping time matches")
                if hh == schedule[day]['stop'] and instance.state["Name"] == 'running':
                    logger.info("Stopping EC2 instance \"%s\"." %(instance.id))
                    stopped.append(instance.id)
                    ec2.instances.filter(InstanceIds=[instance.id]).stop()
            except:
                pass # catch exception if 'stop' is not in schedule.


        except ValueError as e:
            # invalid JSON
            logger.error('Invalid value for tag \"schedule\" on EC2 instance \"%s\", please check!' %(instance.id))

def rds_init():
    # Setup AWS connection
    aws_region     = os.getenv('AWS_REGION', 'us-east-1')

    logger.info("-----> Connecting rds to region \"%s\"", aws_region)
    global rds
    rds = boto3.client('rds', region_name=aws_region)
    logger.info("-----> Connected rds to region \"%s\"", aws_region)

#
# Add default 'schedule' tag to instance.
# (Only if instance.id not excluded and create_schedule_tag_force variable is True.
#
def rds_create_schedule_tag(instance):
    exclude_list = os.environ.get('EXCLUDE').split(',')

    if (create_schedule_tag_force == 'True') and (instance['DBInstanceIdentifier'] not in exclude_list):
        try:
            schedule_tag =  os.getenv('TAG', 'schedule')
            tag_default =  os.getenv('DEFAULT', '{"mon": {"start": 7, "stop": 20},"tue": {"start": 7, "stop": 20},"wed": {"start": 7, "stop": 20},"thu": {"start": 7, "stop": 20}, "fri": {"start": 7, "stop": 20}}')
            logger.info("json tag_value: %s" % tag_default)
            tag = json.loads(tag_default)
            tag_dict = flattenjson(tag, "_")
            tag_value= dict_to_string(tag_dict)
            logger.info("About to create %s tag on RDS instance %s with value: %s" % (schedule_tag,instance['DBInstanceIdentifier'],tag_value))
            tags = [{
                "Key" : schedule_tag,
                "Value" : tag_value
            }]
            rds.add_tags_to_resource(ResourceName=instance['DBInstanceArn'],Tags=tags)
        except Exception as e:
            logger.error("Error adding Tag to RDS instance: %s" % e)
    else:
        logger.info("No 'schedule' tag found on RDS instance %s. Use create_schedule_tag_force option to create the tag automagically" % instance['DBInstanceIdentifier'])

def flattenjson( b, delim ):
    val = {}
    for i in b.keys():
        if isinstance( b[i], dict ):
            get = flattenjson( b[i], delim )
            for j in get.keys():
                val[ i + delim + j ] = get[j]
        else:
            val[i] = b[i]

    return val

def dict_to_string( d ):
    val = ""
    for k, v in d.items():
         if len(val) == 0 :
             val=k+"="+str(v)
         else:
             val=val+" "+k+"="+str(v)

    return val


#
# Loop RDS instances and check if a 'schedule' tag has been set. Next, evaluate value and start/stop instance if needed.
#
def rds_check():
    # Get all reservations.
    instances = rds.describe_db_instances()

    # Get current day + hour (using gmt by default if time parameter not set to local)
    time_zone =  os.getenv('TIME', 'gmt')
    if time_zone == 'local':
        hh  = time.strftime("%H", time.localtime())
        day = time.strftime("%a", time.localtime()).lower()
        logger.info("-----> Checking for RDS instances to start or stop for 'local time' hour \"%s\"", hh)
    else:
        hh  = time.strftime("%H", time.gmtime())
        day = time.strftime("%a", time.gmtime()).lower()
        logger.info("-----> Checking for RDS instances to start or stop for 'gmt' hour \"%s\"", hh)

    started = []
    stopped = []

    schedule_tag = os.getenv('TAG', 'schedule')
    logger.info("-----> schedule tag is called \"%s\"", schedule_tag)
    if not instances:
        logger.error('Unable to find any RDS Instances, please check configuration')

    for instance in instances['DBInstances']:
        #instance = json.loads(db_instance)
        logger.info("Evaluating RDS instance \"%s\"." %(instance['DBInstanceIdentifier']))
        response = rds.list_tags_for_resource(ResourceName=instance['DBInstanceArn'])
        taglist = response['TagList']

        try:
            data = ""
            for tag in taglist:
                if schedule_tag in tag['Key']:
                    data = tag['Value']
                    break
            else:
                rds_create_schedule_tag(instance)

            if data == "":
                schedule = []
            else:
                schedule = dict(x.split('=') for x in data.split(' '))

            try:
                if hh == schedule[day+'_'+'start'] and not instance['DBInstanceStatus'] == 'available':
                    logger.info("Starting RDS instance \"%s\"." %(instance['DBInstanceIdentifier']))
                    started.append(instance['DBInstanceIdentifier'])
                    rds.start_db_instance(DBInstanceIdentifier=instance['DBInstanceIdentifier'])
            except:
                pass # catch exception if 'start' is not in schedule.

            try:
                if hh == schedule[day+'_'+'stop']:
                    logger.info("Stopping time matches")
                if hh == schedule[day+'_'+'stop'] and instance['DBInstanceStatus'] == 'available':
                    logger.info("Stopping RDS instance \"%s\"." %(instance['DBInstanceIdentifier']))
                    stopped.append(instance['DBInstanceIdentifier'])
                    rds.stop_db_instance(DBInstanceIdentifier=instance['DBInstanceIdentifier'])
            except:
                pass # catch exception if 'stop' is not in schedule.


        except ValueError as e:
            # invalid JSON
            logger.error('Invalid value for tag \"schedule\" on RDS instance \"%s\", please check!' %(instance['DBInstanceIdentifier']))

# Main function. Entrypoint for Lambda
def handler(event, context):

    if (ec2_schedule == 'True'):
        init()
        check()

    if (rds_schedule == 'True'):
        rds_init()
        rds_check()

# Manual invocation of the script (only used for testing)
if __name__ == "__main__":
    # Test data
    test = {}
    handler(test, None)
