import json
import boto3
import requests
import time
import os

def lambda_handler(event, context):
    # TODO implement
    
    print(event)
    
    ddb = boto3.resource("dynamodb")
    table = ddb.Table("UserProfile")
    
    response = table.put_item(
        Item={
            'emailId': event['request']['userAttributes']['email'],
            'name': event['request']['userAttributes']['name'],
            'username': event['userName'],
            'profile': event['request']['userAttributes']['profile'],
            'userType': event['request']['userAttributes']['custom:userType'],
            'referralsRemaining': 5,
            'resumeReviewRemaining': 5,
            'resumes': [],
            'company': event['request']['userAttributes']['custom:company'],
            'createdAt': str(int(time.time())),
        }
    )
    
    status_code = response['ResponseMetadata']['HTTPStatusCode']
    print(status_code)
    
    
    ######CHIME add user######
    
    region_name = os.environ['AWS_REGION']
    chime = boto3.client('chime', region_name=region_name)

    CHIME_APP_INSTANCE_ARN = os.environ['CHIME_APP_INSTANCE_ARN']

    username = event['request']['userAttributes']['email']
    userId = event['request']['userAttributes']['email']
    print(username)
    
    if userId == 'none':
        print("User hasn't logged in yet and hasn't been setup with profile")
        return event

    # Create a Chime App Instance User for the user
    chimeCreateAppInstanceUserParams = {
        'AppInstanceArn': CHIME_APP_INSTANCE_ARN,
        'AppInstanceUserId': userId,
        'Name': username
    }

    try:
        print("Creating app instance user for {0}".format(userId))
        response = chime.create_app_instance_user(**chimeCreateAppInstanceUserParams)
        print("Created app instance user")
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': e.stack
        }
        
    if event['request']['userAttributes']['custom:userType'] == "alumni":
        lambdaclient = boto3.client("lambda")
        lambdaclient.invoke(
                FunctionName = "arn:aws:lambda:us-east-1:491877765750:function:linkedin-scrape",
                InvocationType = "Event",
                Payload = json.dumps({
                    "request": {
                        "userAttributes": {
                            "profile": event['request']['userAttributes']['profile'],
                            "email": event['request']['userAttributes']['email'],
                            "company": event['request']['userAttributes']['custom:company']
                        }
                    }
                })
            )

    return event