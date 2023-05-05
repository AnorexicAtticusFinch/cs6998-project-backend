from function_calls import *
import json

dynamodb = boto3.resource("dynamodb")
USER_PROFILE_TABLE = "UserProfile"
USER_PROFILE_TABLE_ID = "emailId"
USER_PROFILE_TABLE_RESUMES = "resumes"

def main(event, context):
    print("lambda_add_resume_to_user:", event)

    userId = event["userId"]
    resumeId = event["resumeId"]

    try:
        table = dynamodb.Table(USER_PROFILE_TABLE)
        table.update_item(
            TableName = USER_PROFILE_TABLE,
            Key = {
                USER_PROFILE_TABLE_ID: userId,
            },
            UpdateExpression = f"SET {USER_PROFILE_TABLE_RESUMES} = list_append(if_not_exists({USER_PROFILE_TABLE_RESUMES}, :empty_list), :i)",
            ExpressionAttributeValues = {
                ":empty_list": [],
                ':i': [resumeId],
            },
        )
    except Exception as e:
        print("lambda_add_resume_to_user: ERROR:", str(e))
        return {
                "error": str(e)
            }

    return {}
