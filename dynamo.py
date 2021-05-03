import boto3
from botocore.exceptions import ClientError
from pprint import pprint
from boto3.dynamodb.conditions import Key, Attr
from meta import status
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
alert_requests = dynamodb.Table('alert_requests')
alert_pincodes = dynamodb.Table('alarm_pincodes')
processed_request = dynamodb.Table('processed_request')
# chat_data = {'request_id':'1799512726411044', 'user': '1799512726', 'name': 'Abhisek', 'pincode': '411044', 'age': '18-44'}

def set_processed(chat_data):
    alert_requests.update_item(
    Key={
        'request_id': chat_data['request_id'],
        'pincode': chat_data['pincode']
    },
    UpdateExpression='SET sent_status = :new_stat, alert_time = :time',
    ExpressionAttributeValues={
        ':new_stat': status.DONE, 
        ':time': str(datetime.now())
    }
)

def add_request(chat_data):
    try:
        response1 = alert_requests.put_item(
        Item=chat_data
        )
        response2 = alert_pincodes.put_item(
        Item={'pincode': chat_data['pincode']}
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    finally:
        return 200 if response1['ResponseMetadata']['HTTPStatusCode'] == 200 and response2['ResponseMetadata']['HTTPStatusCode'] == 200 else 400

def get_request_key(filter_obj):
    try:
        response = alert_requests.get_item(Key=filter_obj)
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']

def get_request_pincode(pincode):
    try:
        response = alert_requests.scan(
            FilterExpression=Attr('pincode').eq(pincode) & Attr('sent_status').ne(status.DONE)
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Items']

def get_all_request():
    try:
        response = alert_requests.scan()
        items = response['Items']    
        while 'LastEvaluatedKey' in response:
            response = alert_requests.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return items

def get_all_pincodes():
    try:
        response = alert_pincodes.scan()
        items = response['Items']    
        while 'LastEvaluatedKey' in response:
            response = alert_requests.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return items
