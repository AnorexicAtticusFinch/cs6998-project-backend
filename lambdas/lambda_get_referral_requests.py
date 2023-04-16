from function_calls import *
import json

def main(event, context):

    print("lambda_get_referral_requests:", event)
    
    user_id = event["queryStringParameters"]["userId"]

    try:
        tmp = read_ref_requests(user_id)

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
        "body": json.dumps(ret)
    }
