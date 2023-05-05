import boto3
from botocore.exceptions import ClientError
import pymysql as sql
import time
import json

STATUS_PENDING = "pending"
STATUS_REJECTED = "rejected"
STATUS_ACCEPTED = "accepted"
STATUS_COMPLETED = "completed"

statusChanges = {
    STATUS_PENDING: [STATUS_ACCEPTED, STATUS_REJECTED],
    STATUS_REJECTED: [],
    STATUS_ACCEPTED: [STATUS_COMPLETED],
    STATUS_COMPLETED: [],
}

db = sql.connect(
    host = "database-2.caqq79ctnwek.us-east-1.rds.amazonaws.com",
    user = "admin",
    password = "adminpwd",
    database = "columbiaconnect",
)

dynamodb = boto3.resource("dynamodb")
MAX_REF_COUNT = 5
MAX_RES_COUNT = 5
USER_PROFILE_TABLE = "UserProfile"
USER_PROFILE_TABLE_ID = "emailId"
USER_PROFILE_TABLE_REF_COUNT = "referralsRemaining"
USER_PROFILE_TABLE_RES_COUNT = "resumeReviewRemaining"

def parse_cursor_fetchall_referral_requests(records):
    ret = []

    if records is None:
        return ret

    for record in records:
        ret.append({
            "sid": record[0],
            "aid": record[1],
            "timestamp": record[2],
            "status": record[3],
        })
    
    return ret

def parse_cursor_fetchall_chat_check(records):
    ret = []

    if records is None:
        return ret

    for record in records:
        ret.append({
            "sid": record[0],
            "aid": record[1],
            "counter": record[2],
        })
    
    return ret

def read_ref_requests(id):
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM referral_requests WHERE sid = '{id}' OR aid = '{id}' ORDER BY timestamp DESC")
    ret = cursor.fetchall()

    ret = parse_cursor_fetchall_referral_requests(ret)

    db.commit()
    return ret

def increment_profile_table_ref(id):
    try:
        table = dynamodb.Table(USER_PROFILE_TABLE)
        table.update_item(
            Key = {
                USER_PROFILE_TABLE_ID: id,
            },
            UpdateExpression = f"SET {USER_PROFILE_TABLE_REF_COUNT} = {USER_PROFILE_TABLE_REF_COUNT} + :val",
            ConditionExpression = f"{USER_PROFILE_TABLE_REF_COUNT} < :max",
            ExpressionAttributeValues = {
                ":val": 1,
                ":max": MAX_REF_COUNT,
            },
        )

        return None
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return "Invalid request (Referral count is already maximum)"
        else:
            return str(e)

def decrement_profile_table_ref(id):
    try:
        table = dynamodb.Table(USER_PROFILE_TABLE)
        table.update_item(
            TableName = USER_PROFILE_TABLE,
            Key = {
                USER_PROFILE_TABLE_ID: id,
            },
            UpdateExpression = f"SET {USER_PROFILE_TABLE_REF_COUNT} = {USER_PROFILE_TABLE_REF_COUNT} - :val",
            ConditionExpression = f"{USER_PROFILE_TABLE_REF_COUNT} > :zero",
            ExpressionAttributeValues = {
                ":val": 1,
                ":zero": 0,
            },
        )

        return None
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return "Referral limit reached"
        else:
            return str(e)

def add_to_chat_table(sid, aid):
    try:
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM chat_check WHERE sid = '{sid}' AND aid = '{aid}'")
        req = cursor.fetchall()

        req = parse_cursor_fetchall_chat_check(req)

        if len(req) == 0:
            cursor = db.cursor()
            cursor.execute(f"INSERT INTO chat_check VALUES ('{sid}', '{aid}', 1)")
            db.commit()

            lambdaclient = boto3.client("lambda")
            response = lambdaclient.invoke(
                    FunctionName = "arn:aws:lambda:us-east-1:491877765750:function:createChimeChannel",
                    InvocationType = "RequestResponse",
                    Payload = json.dumps({
                        "appInstanceArn": "arn:aws:chime:us-east-1:491877765750:app-instance/44f08432-a18d-4e00-aff8-e13948f62d5b",
                        "name": f"{sid} <> {aid}",
                        "sid": sid,
                        "aid": aid,
                    })
            )

            response = json.load(response["Payload"])
            if response["status"] == "error":
                return "Failed to allow chat access"
        else:
            req = req[0]
            oldCounter = req["counter"]

            cursor = db.cursor()
            cursor.execute(f"UPDATE chat_check SET counter = {oldCounter+1} WHERE sid = '{sid}' AND aid = '{aid}'")
            db.commit()
        
        db.commit()
        return None
    except Exception as e:
        db.commit()
        return str(e)

def remove_from_chat_table(sid, aid):
    try:
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM chat_check WHERE sid = '{sid}' AND aid = '{aid}'")
        req = cursor.fetchall()

        req = parse_cursor_fetchall_chat_check(req)

        if len(req) == 0:
            db.commit()
            return "Invalid request (Chat did not exist in the first place)"
        else:
            req = req[0]
            oldCounter = req["counter"]

            if oldCounter == 0:
                db.commit()
                return "Invalid request (Chat did not exist in the first place, counter was 0)"

            cursor = db.cursor()
            cursor.execute(f"UPDATE chat_check SET counter = {oldCounter-1} WHERE sid = '{sid}' AND aid = '{aid}'")
            db.commit()

            if oldCounter == 1:
                pass
        
        db.commit()
        return None
    except Exception as e:
        db.commit()
        return str(e)

def update_ref_request(sid, aid, timestamp, newStatus):
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM referral_requests WHERE sid = '{sid}' AND aid = '{aid}' AND timestamp = {timestamp}")
    req = cursor.fetchall()

    req = parse_cursor_fetchall_referral_requests(req)
    if len(req) == 0:
        return "Could not find request"
    
    req = req[0]
    oldStatus = req["status"]

    if newStatus not in statusChanges[oldStatus]:
        db.commit()
        return "Invalid status change"
    
    cursor = db.cursor()
    cursor.execute(f"UPDATE referral_requests SET status = '{newStatus}' WHERE sid = '{sid}' AND aid = '{aid}' AND timestamp = {timestamp}")
    db.commit()

    if newStatus == STATUS_REJECTED or newStatus == STATUS_COMPLETED:
        ret = increment_profile_table_ref(sid)
        if ret is not None:
            db.commit()
            return ret
        ret = increment_profile_table_ref(aid)
        if ret is not None:
            db.commit()
            return ret

    if newStatus == STATUS_COMPLETED:
        ret = remove_from_chat_table(sid, aid)
        if ret is not None:
            db.commit()
            return ret

    if newStatus == STATUS_ACCEPTED:
        ret = add_to_chat_table(sid, aid)
        if ret is not None:
            db.commit()
            return ret

    db.commit()
    return None

def create_referral_request(sid, aid):
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM referral_requests WHERE sid = '{sid}' AND aid = '{aid}' AND status = '{STATUS_PENDING}'")
    req = cursor.fetchall()
    req = parse_cursor_fetchall_referral_requests(req)
    if len(req) > 0:
        db.commit()
        return "These 2 users already have a pending referral request"

    ret = decrement_profile_table_ref(sid)
    if ret is not None:
        db.commit()
        return ret
    ret = decrement_profile_table_ref(aid)
    if ret is not None:
        db.commit()
        return ret

    cursor = db.cursor()
    cursor.execute(f"INSERT INTO referral_requests VALUES ('{sid}', '{aid}', {int(time.time())}, '{STATUS_PENDING}')")
    db.commit()

    db.commit()
    return None

#----------------------------------------------------------------------------------------------------------------------

def parse_cursor_fetchall_resume_requests(records):
    ret = []

    if records is None:
        return ret

    for record in records:
        ret.append({
            "sid": record[0],
            "aid": record[1],
            "rid": record[2],
            "timestamp": record[3],
            "status": record[4],
        })
    
    return ret

def read_res_requests(id):
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM resume_requests WHERE sid = '{id}' OR aid = '{id}' ORDER BY timestamp DESC")
    ret = cursor.fetchall()

    ret = parse_cursor_fetchall_resume_requests(ret)

    db.commit()
    return ret

def increment_profile_table_res(id):
    try:
        table = dynamodb.Table(USER_PROFILE_TABLE)
        table.update_item(
            Key = {
                USER_PROFILE_TABLE_ID: id,
            },
            UpdateExpression = f"SET {USER_PROFILE_TABLE_RES_COUNT} = {USER_PROFILE_TABLE_RES_COUNT} + :val",
            ConditionExpression = f"{USER_PROFILE_TABLE_RES_COUNT} < :max",
            ExpressionAttributeValues = {
                ":val": 1,
                ":max": MAX_RES_COUNT,
            },
        )

        return None
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return "Invalid request (Resume count is already maximum)"
        else:
            return str(e)

def decrement_profile_table_res(id):
    try:
        table = dynamodb.Table(USER_PROFILE_TABLE)
        table.update_item(
            TableName = USER_PROFILE_TABLE,
            Key = {
                USER_PROFILE_TABLE_ID: id,
            },
            UpdateExpression = f"SET {USER_PROFILE_TABLE_RES_COUNT} = {USER_PROFILE_TABLE_RES_COUNT} - :val",
            ConditionExpression = f"{USER_PROFILE_TABLE_RES_COUNT} > :zero",
            ExpressionAttributeValues = {
                ":val": 1,
                ":zero": 0,
            },
        )

        return None
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return "Resume limit reached"
        else:
            return str(e)

def update_res_request(sid, aid, rid, timestamp, newStatus):
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM resume_requests WHERE sid = '{sid}' AND aid = '{aid}' AND rid = '{rid}' AND timestamp = {timestamp}")
    req = cursor.fetchall()

    req = parse_cursor_fetchall_resume_requests(req)
    if len(req) == 0:
        return "Could not find request"
    
    req = req[0]
    oldStatus = req["status"]

    if newStatus not in statusChanges[oldStatus]:
        db.commit()
        return "Invalid status change"
    
    cursor = db.cursor()
    cursor.execute(f"UPDATE resume_requests SET status = '{newStatus}' WHERE sid = '{sid}' AND aid = '{aid}' AND rid = '{rid}' AND timestamp = {timestamp}")
    db.commit()

    if newStatus == STATUS_REJECTED or newStatus == STATUS_COMPLETED:
        ret = increment_profile_table_res(sid)
        if ret is not None:
            db.commit()
            return ret
        ret = increment_profile_table_res(aid)
        if ret is not None:
            db.commit()
            return ret

    if newStatus == STATUS_COMPLETED:
        ret = remove_from_chat_table(sid, aid)
        if ret is not None:
            db.commit()
            return ret

    if newStatus == STATUS_ACCEPTED:
        ret = add_to_chat_table(sid, aid)
        if ret is not None:
            db.commit()
            return ret

    db.commit()
    return None

def create_resume_request(sid, aid, rid):
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM resume_requests WHERE sid = '{sid}' AND aid = '{aid}' AND rid = '{rid}' AND status = '{STATUS_PENDING}'")
    req = cursor.fetchall()
    req = parse_cursor_fetchall_resume_requests(req)
    if len(req) > 0:
        db.commit()
        return "These 2 users already have a pending resume request"

    ret = decrement_profile_table_res(sid)
    if ret is not None:
        db.commit()
        return ret
    ret = decrement_profile_table_res(aid)
    if ret is not None:
        db.commit()
        return ret

    cursor = db.cursor()
    cursor.execute(f"INSERT INTO resume_requests VALUES ('{sid}', '{aid}', '{rid}', {int(time.time())}, '{STATUS_PENDING}')")
    db.commit()

    db.commit()
    return None
