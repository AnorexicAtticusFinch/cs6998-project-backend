from function_calls import *

def main(event, context):

    print("lambda_update_resume_request_status:", event)

    userId = event["userId"]
    alumniId = event["alumniId"]
    resumeId = event["resumeId"]
    timestamp = event["timestamp"]
    newStatus = event["newStatus"]

    try:
        ret = update_res_request(userId, alumniId, resumeId, timestamp, newStatus)
        if ret is not None:
            print("lambda_update_resume_request_status: ERROR:", ret)
            return {
                "error": ret
            }
    except Exception as e:
        print("lambda_update_resume_request_status: ERROR:", str(e))
        return {
                "error": str(e)
            }

    return {}
