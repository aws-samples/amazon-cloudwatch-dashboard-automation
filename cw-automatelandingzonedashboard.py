import boto3
import json
import copy
import os
import logging

from datetime import datetime

def lambda_handler(context, event):
    # EVENT TAGS AND REGIONS
    pathprefix = '/use1/dev/' # <- Please add desired SSM Parameter Store Path in the format /$region/$environment/
    #Retrieve SSM Values
    ssm_connection = boto3.client('ssm')
    cross_account_policy_name = ssm_connection.get_parameter(Name=pathprefix+'cross-account-policy-name')['Parameter']['Value']
    ssm_key_response = ssm_connection.get_parameter(Name=pathprefix+'search-key')
    ssm_regions_response = ssm_connection.get_parameter(Name=pathprefix+'search-regions')
    ssm_values_response = ssm_connection.get_parameter(Name=pathprefix+'search-values')
    ssm_prefix_response = ssm_connection.get_parameter(Name=pathprefix+'dashboard-prefix')

    #Set Variables
    key = ssm_key_response['Parameter']['Value']
    regions = ssm_regions_response['Parameter']['Value'].split(',')
    tagvalues = ssm_values_response['Parameter']['Value'].split(',')
    dashboardprefix = ssm_prefix_response['Parameter']['Value']

    scafolding_json = {
        "type": "metric",
        "width": 6,
        "height": 6,
        "properties": {
            "view": "timeSeries",
            "stacked": False,
            "metrics": [],
            "region": "us-east-1",
            "period": 300,
            "title": ""
        }
    }

    # LOGGER
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info('## ENVIRONMENT VARIABLES')
    logger.info(os.environ)

    dashboards = []
    for value in tagvalues:
        unsorted_tagged_arn_list = []
        sorted_tagged_arn_list = []
        # DASHBOARDS & WIDGET TEMPLATES
        widget_json = {
            "widgets": []
        }
        for region in regions:
            unsorted_tagged_arn_list.append(iterate_regions(region,key,value,logger,cross_account_policy_name))
        sorted_tagged_arn_list = sort_list(unsorted_tagged_arn_list)
        create_widgets(sorted_tagged_arn_list,widget_json,scafolding_json,logger)
        dashboards.append(create_dashboard(json.dumps(widget_json),'{0}{1}'.format(dashboardprefix,value)))
    return dashboards

#LAMBDA HANDLER RETURN

def iterate_regions(region,key,value,logger,cross_account_policy_name):
    region_arn_list = []
    try: #Local Account Resources
        request = local_client(region)
        region_arn_list.append(get_tagged_resources(request,key,value))
    except Exception as e:
        logger.info('### EXCEPTION')
        logger.info(e)

    try: #Cross-Account Resources
        sts_connection = boto3.client('sts')
        account_id = sts_connection.get_caller_identity()
        trusted_resources = get_trusted_roles(account_id['Account'],cross_account_policy_name)
        for resource in trusted_resources['PolicyVersion']['Document']['Statement']:
            for trusted_item in resource['Resource']:
                role_arn = trusted_item
                account_id = trusted_item.split(':')[4]
                role_session_name = trusted_item.split(':')[5].split('/')[1]
                request = destination_client(role_arn,role_session_name,sts_connection,region)
                region_arn_list.append(get_tagged_resources(request,key,value))
    except Exception as e:
        logger.info('### EXCEPTION')
        logger.info(e)
    return region_arn_list

def get_tagged_resources(request,key,value):
    response = request.get_resources(TagFilters=[
        {
            'Key': key,
            'Values': [
                value,
            ]
        },
    ])

    account_arn_list = []
    for item in response['ResourceTagMappingList']:
        account_arn_list.append(item['ResourceARN'].split(':'))
    return account_arn_list

def local_client(region):
    request = boto3.client(
        'resourcegroupstaggingapi',
        region_name=region
    )
    return request

def destination_client(role_arn,role_session_name,sts_connection,region):
    destination_account_role = sts_connection.assume_role(
        RoleArn=role_arn,
        RoleSessionName=role_session_name
        )

    request = boto3.client(
        'resourcegroupstaggingapi',
        aws_access_key_id=destination_account_role['Credentials']['AccessKeyId'],
        aws_secret_access_key=destination_account_role['Credentials']['SecretAccessKey'],
        aws_session_token=destination_account_role['Credentials']['SessionToken'],
        region_name=region
    )
    return request


def get_trusted_roles(account_id,cross_account_policy_name):
    request = boto3.client('iam')
    policy_arn = 'arn:aws:iam::' + account_id + ':policy/' + cross_account_policy_name
    policy_version = request.get_policy(PolicyArn=policy_arn)
    trusted_list = request.get_policy_version(PolicyArn=policy_arn,VersionId=policy_version['Policy']['DefaultVersionId'])
    return trusted_list

def create_dashboard(dashboard_body,dashboard_name):
    cloudwatch = boto3.client('cloudwatch')
    response = cloudwatch.put_dashboard(DashboardName=dashboard_name, DashboardBody=dashboard_body)
    return response

def create_widgets(sorted_tagged_arn_list,widget_json,scafolding_json,logger):
    #ARN KEY MAPPING
    arn_keys = ['arn','segment','service','region','account','resource','item']

    # EC2
    ec2_metric_dimensions = get_ec2_metric_dimensions(arn_keys,sorted_tagged_arn_list)
    widget_json['widgets'].append(create_widget('EC2 CPU Utilization', scafolding_json, 'AWS/EC2',
                                                'CPUUtilization', 'InstanceId',ec2_metric_dimensions))
    widget_json['widgets'].append(create_widget('EC2 Network In', scafolding_json, 'AWS/EC2',
                                                'NetworkIn', 'InstanceId', ec2_metric_dimensions))
    widget_json['widgets'].append(create_widget('EC2 Network Out', scafolding_json, 'AWS/EC2',
                                                'NetworkOut', 'InstanceId', ec2_metric_dimensions))
    widget_json['widgets'].append(create_widget('EC2 Status Check', scafolding_json, 'AWS/EC2',
                                                'StatusCheckFailed', 'InstanceId', ec2_metric_dimensions))
    # RDS
    rds_metric_dimensions = get_rds_metric_dimensions(arn_keys,sorted_tagged_arn_list)
    widget_json['widgets'].append(create_widget('RDS CPU Utilization', scafolding_json, 'AWS/RDS',
                                                'CPUUtilization', 'DBInstanceIdentifier', rds_metric_dimensions))
    widget_json['widgets'].append(create_widget('RDS DB Connections', scafolding_json, 'AWS/RDS',
                                                'DatabaseConnections', 'DBInstanceIdentifier', rds_metric_dimensions))
    widget_json['widgets'].append(create_widget('RDS Read IOPS', scafolding_json, 'AWS/RDS',
                                                'ReadIOPS', 'DBInstanceIdentifier', rds_metric_dimensions))
    widget_json['widgets'].append(create_widget('RDS FreeableMemory', scafolding_json, 'AWS/RDS',
                                                'FreeableMemory', 'DBInstanceIdentifier', rds_metric_dimensions))
    widget_json['widgets'].append(create_widget('RDS Write IOPS', scafolding_json,'AWS/RDS',
                                                'WriteIOPS', 'DBInstanceIdentifier', rds_metric_dimensions))

    # Lambda
    lambda_metric_dimensions = get_lambda_metric_dimensions(arn_keys,sorted_tagged_arn_list)
    widget_json['widgets'].append(create_widget('Lambda Throttles', scafolding_json,'AWS/Lambda',
                                                'Throttles', 'FunctionName', lambda_metric_dimensions))
    widget_json['widgets'].append(create_widget('Lambda Duration', scafolding_json, 'AWS/Lambda',
                                                'Duration', 'FunctionName', lambda_metric_dimensions))
    widget_json['widgets'].append(create_widget('Lambda Errors', scafolding_json, 'AWS/Lambda',
                                                'Errors', 'FunctionName', lambda_metric_dimensions))
    widget_json['widgets'].append(create_widget('Lambda Invocations', scafolding_json, 'AWS/Lambda',
                                                'Invocations', 'FunctionName', lambda_metric_dimensions))

    # Elasticache
    elasticache_metric_dimensions = get_elasticache_metric_dimensions(arn_keys,sorted_tagged_arn_list)
    widget_json['widgets'].append(create_widget('ElasticCache CPU Utilization', scafolding_json, 'AWS/ElastiCache',
                                                'CPUUtilization', 'CacheClusterId', elasticache_metric_dimensions))
    widget_json['widgets'].append(create_widget('ElasticCache Evictions', scafolding_json, 'AWS/ElastiCache', 'Evictions',
                                                'CacheClusterId', elasticache_metric_dimensions))
    widget_json['widgets'].append(create_widget('ElasticCache CurrConnections', scafolding_json, 'AWS/ElastiCache',
                                                'CurrConnections', 'CacheClusterId', elasticache_metric_dimensions))

    # Classic Load Balancer
    clb_metric_dimensions = get_clb_metric_dimensions(arn_keys,sorted_tagged_arn_list)
    widget_json['widgets'].append(create_widget('CLB Request Count', scafolding_json, 'AWS/ELB',
                                                'RequestCount', 'LoadBalancerName', clb_metric_dimensions))
    widget_json['widgets'].append(create_widget('CLB Healthy Host Count', scafolding_json, 'AWS/ELB',
                                                'HealthyHostCount', 'LoadBalancerName', clb_metric_dimensions))
    widget_json['widgets'].append(create_widget('CLB Unhealthy Host Count', scafolding_json, 'AWS/ELB',
                                                'UnHealthyHostCount', 'LoadBalancerName', clb_metric_dimensions))
    widget_json['widgets'].append(create_widget('CLB 5XX Count', scafolding_json, 'AWS/ELB',
                                                'HTTPCode_ELB_5XX', 'LoadBalancerName', clb_metric_dimensions))

    # Application Load Balancer
    alb_metric_dimensions = get_alb_metric_dimensions(arn_keys,sorted_tagged_arn_list)
    widget_json['widgets'].append(create_widget('ALB Consumed LCUs', scafolding_json, 'AWS/ApplicationELB',
                                                'ConsumedLCUs', 'LoadBalancer', alb_metric_dimensions))
    widget_json['widgets'].append(create_widget('ALB Request Count', scafolding_json, 'AWS/ApplicationELB',
                                                'RequestCount', 'LoadBalancer', alb_metric_dimensions))
    widget_json['widgets'].append(create_widget('ALB Target Response Time', scafolding_json, 'AWS/ApplicationELB',
                                                'TargetResponseTime', 'LoadBalancer', alb_metric_dimensions))
    widget_json['widgets'].append(create_widget('ALB Active Connection Count', scafolding_json, 'AWS/ApplicationELB',
                                                'ActiveConnectionCount', 'LoadBalancer', alb_metric_dimensions))
    widget_json['widgets'].append(create_widget('ALB 5XX Count', scafolding_json, 'AWS/ApplicationELB',
                                                'HTTPCode_ELB_5XX_Count', 'LoadBalancer', alb_metric_dimensions))


    # Network Load Balancer
    nlb_metric_dimensions = get_nlb_metric_dimensions(arn_keys,sorted_tagged_arn_list)

    widget_json['widgets'].append(create_widget('NLB Consumed LCUs', scafolding_json, 'AWS/NetworkELB',
                                                'ConsumedLCUs', 'LoadBalancer', nlb_metric_dimensions))
    widget_json['widgets'].append(create_widget('NLB Processed Bytes', scafolding_json, 'AWS/NetworkELB',
                                                'ProcessedBytes', 'LoadBalancer', nlb_metric_dimensions))
    widget_json['widgets'].append(create_widget('NLB Active Flow Count', scafolding_json, 'AWS/NetworkELB',
                                                'ActiveFlowCount', 'LoadBalancer', nlb_metric_dimensions))
    widget_json['widgets'].append(create_widget('NLB New Flow Count', scafolding_json, 'AWS/NetworkELB',
                                                'NewFlowCount', 'LoadBalancer', nlb_metric_dimensions))
    widget_json['widgets'].append(create_widget('NLB TCP Client Reset Count', scafolding_json, 'AWS/NetworkELB',
                                                'TCP_Client_Reset_Count', 'LoadBalancer', nlb_metric_dimensions))
    return True

def create_widget(title, scaffolding_json, namespace, metric, metric_dimension_name, metric_dimensions):
    widget = copy.deepcopy(scaffolding_json)
    for metric_dimension in metric_dimensions:
        widget['properties']['metrics'].append([namespace, metric,
                                                metric_dimension_name, metric_dimension['id'] ,
                                                { "region": metric_dimension['region'], "accountId": metric_dimension['account']}])
    widget['properties']['title'] = title
    return widget


def get_ec2_metric_dimensions(arn_keys,sorted_tagged_arn_list):
    ec2_metric_dimensions = []
    for arn_item in sorted_tagged_arn_list:
        arn_item_value = dict(zip(arn_keys, arn_item))
        if arn_item_value['service'] == 'ec2':
            if arn_item_value['resource'].split('/')[0] == 'instance':
                resource = arn_item_value['resource'].split('/')[1]
                ec2_metric_dimensions.append(dict(
                    id=resource,
                    region=arn_item_value['region'],
                    account=arn_item_value['account']
                ))
    return ec2_metric_dimensions

def get_rds_metric_dimensions(arn_keys,sorted_tagged_arn_list):
    rds_metric_dimensions = []
    for arn_item in sorted_tagged_arn_list:
        arn_item_value = dict(zip(arn_keys, arn_item))
        if arn_item_value['service'] == 'rds':
            if arn_item_value['resource'] == 'db':
                resource = arn_item_value['item']
                rds_metric_dimensions.append(dict(
                    id=resource,
                    region=arn_item_value['region'],
                    account=arn_item_value['account']
                ))
    return rds_metric_dimensions

def get_lambda_metric_dimensions(arn_keys,sorted_tagged_arn_list):
    lambda_metric_dimensions = []
    for arn_item in sorted_tagged_arn_list:
        arn_item_value = dict(zip(arn_keys, arn_item))
        if arn_item_value['service'] == 'lambda':
            if arn_item_value['resource'] == 'function':
                resource = arn_item_value['item']
                lambda_metric_dimensions.append(dict(
                    id=resource,
                    region=arn_item_value['region'],
                    account=arn_item_value['account']
                ))
    return lambda_metric_dimensions

def get_elasticache_metric_dimensions(arn_keys,sorted_tagged_arn_list):
    elasticache_metric_dimensions = []
    for arn_item in sorted_tagged_arn_list:
        arn_item_value = dict(zip(arn_keys, arn_item))
        if arn_item_value['service'] == 'elasticache':
            if arn_item_value['resource'] == 'cluster':
                resource = arn_item_value['item']
                elasticache_metric_dimensions.append(dict(
                    id=resource,
                    region=arn_item_value['region'],
                    account=arn_item_value['account']
                ))
    return elasticache_metric_dimensions

def get_clb_metric_dimensions(arn_keys,sorted_tagged_arn_list):
    clb_metric_dimensions = []
    for arn_item in sorted_tagged_arn_list:
        arn_item_value = dict(zip(arn_keys, arn_item))
        if arn_item_value['service'] == 'elasticloadbalancing':
            if arn_item_value['resource'].split('/')[0] == 'loadbalancer':
                if arn_item_value['resource'].split('/')[1] != 'app' and arn_item_value['resource'].split('/')[1] != 'net':
                    resource = arn_item_value['resource'].split('/')[1]
                    clb_metric_dimensions.append(dict(
                        id=resource,
                        region=arn_item_value['region'],
                        account=arn_item_value['account']
                    ))
    return clb_metric_dimensions

def get_alb_metric_dimensions(arn_keys,sorted_tagged_arn_list):
    alb_metric_dimensions = []
    for arn_item in sorted_tagged_arn_list:
        arn_item_value = dict(zip(arn_keys, arn_item))
        if arn_item_value['service'] == 'elasticloadbalancing':
            if arn_item_value['resource'].split('/')[0] == 'loadbalancer':
                if arn_item_value['resource'].split('/')[1] == 'app':
                    resource = arn_item_value['resource'].split('/')[1] + '/' + arn_item_value['resource'].split('/')[2] + '/' + arn_item_value['resource'].split('/')[3]
                    alb_metric_dimensions.append(dict(
                        id=resource,
                        region=arn_item_value['region'],
                        account=arn_item_value['account']
                    ))
    return alb_metric_dimensions

def get_nlb_metric_dimensions(arn_keys,sorted_tagged_arn_list):
    nlb_metric_dimensions = []
    for arn_item in sorted_tagged_arn_list:
        arn_item_value = dict(zip(arn_keys, arn_item))
        if arn_item_value['service'] == 'elasticloadbalancing':
            if arn_item_value['resource'].split('/')[0] == 'loadbalancer':
                if arn_item_value['resource'].split('/')[1] == 'net':
                    resource = arn_item_value['resource'].split('/')[1] + '/' + arn_item_value['resource'].split('/')[2] + '/' + arn_item_value['resource'].split('/')[3]
                    nlb_metric_dimensions.append(dict(
                        id=resource,
                        region=arn_item_value['region'],
                        account=arn_item_value['account']
                    ))
    return nlb_metric_dimensions


def sort_list(unsorted_tagged_arn_list):
    temp_list = []
    for arn_item_per_region in unsorted_tagged_arn_list:
        for arn_item_per_account in arn_item_per_region:
            for arn_item in arn_item_per_account:
                if arn_item:
                    temp_list.append(arn_item)
    return temp_list
