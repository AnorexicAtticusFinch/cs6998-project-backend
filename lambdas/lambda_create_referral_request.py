from function_calls import *
import boto3

def send_email(id):
    try:
        ses = boto3.client("ses")
        ses.send_email(
            Destination = {
                "ToAddresses": [
                    id,
                ],
            },
            Message = {
                "Body": {
                    "Text": {
                        "Charset": "UTF-8",
                        "Data": "Hello fren, you have a referral request!",
                    }
                },
                "Subject": {
                    "Charset": "UTF-8",
                    "Data": "Hello fren, you have a referral request!",
                },
            },
            Source = "b.ajay@columbia.edu",
        )
    except Exception as e:
        print("lambda_create_referral_request: Could not send email:", str(e))

def main(event, context):

    print("lambda_create_referral_request:", event)

    userId = event["userId"]
    alumniId = event["reviewers"]

    if len(alumniId) != 1:
        return {
            "error": "too many reviewers requested, please try again with just 1"
        }
    alumniId = alumniId[0]

    try:
        ret = create_referral_request(userId, alumniId)
        if ret is not None:
            print("lambda_create_referral_request: ERROR:", ret)
            return {
                "error": ret
            }
        
        send_email(alumniId)
    except Exception as e:
        print("lambda_get_referral_requests: ERROR:", str(e))
        return {
                "error": str(e)
            }

    return {}
