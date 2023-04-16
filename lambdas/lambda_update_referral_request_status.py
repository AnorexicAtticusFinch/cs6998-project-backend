from function_calls import *

def main(event, context):

    print("lambda_update_referral_request_status:", event)

    userId = event["userId"]
    alumniId = event["alumniId"]
    timestamp = event["timestamp"]
    newStatus = event["newStatus"]

    try:
        ret = update_ref_request(userId, alumniId, timestamp, newStatus)
        if ret is not None:
            print("lambda_update_referral_request_status: ERROR:", ret)
            return {
                "error": ret
            }
    except Exception as e:
        print("lambda_update_referral_request_status: ERROR:", str(e))
        return {
                "error": str(e)
            }

    return {}
