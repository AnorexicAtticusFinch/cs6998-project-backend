from function_calls import *
import json

dynamodb = boto3.resource("dynamodb")
USER_PROFILE_TABLE = "UserProfile"
USER_PROFILE_TABLE_ID = "emailId"

def fetch_from_dynamo(id):
    table = dynamodb.Table(USER_PROFILE_TABLE)
    response = table.get_item(
        Key = {
                USER_PROFILE_TABLE_ID: id,
            },
    )

    if "Item" in response:
        response["Item"]["referralsRemaining"] = int(response["Item"]["referralsRemaining"])
        response["Item"]["resumeReviewRemaining"] = int(response["Item"]["resumeReviewRemaining"])
        return response["Item"]
    else:
        return None

def main(event, context):

    print("lambda_get_referral_requests:", event)
    
    user_id = event["queryStringParameters"]["userId"]

    try:
        tmp = read_ref_requests(user_id)

        for row in tmp:
            row["aid_profile"] = fetch_from_dynamo(row["aid"])
            row["sid_profile"] = fetch_from_dynamo(row["sid"])

        ret = {
            "requests": tmp
        }
    except Exception as e:
        print("lambda_get_referral_requests: ERROR:", str(e))

        ret = {
            "error": str(e)
        }    
    
    print("lambda_get_referral_requests:", ret)
    
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        },
        "body": json.dumps(ret)
    }
