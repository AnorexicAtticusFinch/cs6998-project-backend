import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth 
import operator
import random

REGION = 'us-east-1'
HOST = 'search-linkedin-keywords-phrcf56t7zdvmqnt6d7nlea3oq.us-east-1.es.amazonaws.com'
INDEX = 'keywords'

dynamodb = boto3.resource("dynamodb")
USER_PROFILE_TABLE = "UserProfile"
USER_PROFILE_TABLE_ID = "emailId"

def lambda_handler(event, context):
    # TODO implement
    opensearch = OpenSearch(hosts=[{
                'host': HOST,
                'port': 443
            }],
            http_auth=get_awsauth(REGION, 'es'),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection)
    
    flow = "None"
    
    if "company" in event:
        flow = "alumni"
    else:
        flow = "student"
        
    print(flow)
    
    search_string = event["keywords"]
    search_list = search_string.split(",")
    results_dict = dict()
    
    if flow == "student":
        query = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"keywords": {"query": keyword, "fuzziness": "AUTO"}}} for keyword in search_list
                    ]
                }
            },
            "size": 6,
        }
        
        response = opensearch.search(index=INDEX, body=query)
        response = response['hits']['hits']
        
        for response_dict in response:
            print(response_dict)
            results_dict[response_dict["_id"]] = response_dict['_score']

    else:
        query = {
          "query": {
            "bool": {
              "must": [
                { "match": { "company": event["company"] } }
              ],
             "should": [
                {"match": {"keywords": {"query": keyword, "fuzziness": "AUTO"}}} for keyword in search_list
            ]
            }
          },
          "size": 6
        }
        response = opensearch.search(index=INDEX, body=query)
        response = response['hits']['hits']
        
        for response_dict in response:
            print(response_dict)
            results_dict[response_dict["_id"]] = response_dict['_score']
            
    results_dict = dict(sorted(results_dict.items(), key=operator.itemgetter(1),reverse=True))
    print(results_dict)
    
    profiles = []
    for email_id in results_dict.keys():
        profiles.append(fetch_from_dynamo(email_id))
        
    return {
        'statusCode': 200,
        'body': profiles
    }
    
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

def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)