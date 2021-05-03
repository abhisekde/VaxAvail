import boto3
import base64
import json
from botocore.exceptions import ClientError

def get_secret():
    secret_name = "cowin_app"
    region_name = "ap-south-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        print(e.__repr__())
        return {'bot_secret_key': ''}
    else:
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            
    return json.loads(secret)

TOKEN=get_secret()['bot_secret_key']
