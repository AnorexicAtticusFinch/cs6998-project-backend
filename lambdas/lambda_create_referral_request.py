from function_calls import *

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
    except Exception as e:
        print("lambda_get_referral_requests: ERROR:", str(e))
        return {
                "error": str(e)
            }

    return {}
