import requests
import datetime
import boto3
import json

from botocore.exceptions import ClientError

#-- Get WaterCooler secret:
watercooler_slack_secret_name = "WatercoolerSlackPresenceApp"
region_name                   = "us-east-1"

session         = boto3.session.Session()
secret_manager  = session.client(
    service_name = 'secretsmanager',
    region_name  = region_name,
)

watercooler_slack_secret_dict = json.loads(secret_manager.get_secret_value(SecretId=watercooler_slack_secret_name)['SecretString'])
watercooler_app_id            = watercooler_slack_secret_dict['client_id'    ]
watercooler_app_secret        = watercooler_slack_secret_dict['client_secret']

def get_client_token(code):

    data = {
        "client_id"     : watercooler_app_id,
        "client_secret" : watercooler_app_secret,
        "code"          : code,
    }

    response = requests.post(
        "https://slack.com/api/oauth.v2.access",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    response_data = response.json()

    if response_data['ok'] != True:
        print(f"Error: {response_data['error']}")
        print(response_data)
        raise

    return response_data


def lambda_handler(event, context):

    # print('AAAAAAAAAAAAAAAAAAAAAAAAAAAA')
    # print(event)
    # print('BBBBBBBBBBBBBBBBBBBBBBBBBBBB')
    # print(context)
    # print('CCCCCCCCCCCCCCCCCCCCCCCCCCCC')

    app_name = event['queryStringParameters']['app_name']
    code     = event['queryStringParameters']['code']
    response = get_client_token(code)

    team_name          = response['team']['name']
    client_secret_dict = {
        'user_id'   : response['authed_user']['id'],
        'scope'     : response['authed_user']['scope'],
        'token'     : response['authed_user']['access_token'],
        'team_id'   : response['team']['id'],
        'team_name' : team_name,
        'app_name'  : app_name,
    }

    new_secret_kwargs = {
        'Name'         : f'{team_name}_{app_name}',
        'Description'  : 'Slack token',
        'SecretString' : json.dumps(client_secret_dict),
        'Tags'         : [{
            'Key'  : 'Platform',
            'Value': 'Slack'
        }],
    }

    try:
        secret_manager.create_secret(**new_secret_kwargs)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceExistsException':
            print('Warning! secret already exists.\nAdding date to secret name')
            new_secret_kwargs['Name'] = team_name + f'{datetime.datetime.now()}'.replace(':','_').replace(' ','_')
            secret_manager.create_secret(**new_secret_kwargs)
        else:
            print('Unknown error')
            raise e

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Thank you for installing the Watercooler Slack presence app!",
            # "location": ip.text.replace("\n", "")
        }),
    }

    # return {
    #     "statusCode" : 302,
    #     "headers"    : {"Location":"https://wcooler.io"},
    #     "body"       : ""
    # }
