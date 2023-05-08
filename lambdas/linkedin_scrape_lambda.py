import json
import requests
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3

REGION = 'us-east-1'
HOST = 'search-linkedin-keywords-phrcf56t7zdvmqnt6d7nlea3oq.us-east-1.es.amazonaws.com'
INDEX = 'keywords'


def get_id_from_link(linkedin_link):
    entries = linkedin_link.split('/')
    link_length = len(linkedin_link)
    if linkedin_link[link_length-1] == '/':
        return entries[-2]
    else:
        return entries[-1]

def lambda_handler(event, context):
    
    #Get from event
    linkedin_link = event['request']['userAttributes']['profile']
    emailId = event['request']['userAttributes']['email']
    
    #linkedin_link = 'https://www.linkedin.com/in/giffin-suresh/'
    linkedin_id = get_id_from_link(linkedin_link)
    print(linkedin_id)
    
    ngrok_url = "https://4216-2607-fb90-ac94-f781-ec0e-ff90-7d65-699.ngrok-free.app/"
    url = ngrok_url + linkedin_id
    
    response = requests.get(url)
    data = response.json()
    print(data)
    
    if response.status_code != 200:
        print('Error:', response.status_code)
        
    keywords_list = data['keywords']

    
    #Opensearch insert
    client = OpenSearch(hosts=[{
                'host': HOST,
                'port': 443
            }],
            http_auth=get_awsauth(REGION, 'es'),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection)
    
    # Define the JSON object to be put into OpenSearch
    company = event['request']['userAttributes']['company']

    json_obj = {
        "emailId": emailId,
        "company": company,
        "keywords": keywords_list
    }
    
    # Convert the JSON object to a string
    json_str = json.dumps(json_obj)
    
    # Put the JSON object into OpenSearch
    client.index(index=INDEX, id=emailId, body=json_str)
    res = client.get(index=INDEX, id=emailId)
    print(res)'

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully added Keywords')
    }

'''
def lambda_handler(event, context):
    client = OpenSearch(hosts=[{
                'host': HOST,
                'port': 443
            }],
            http_auth=get_awsauth(REGION, 'es'),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection)
            
    # Delete all documents in the OpenSearch index
    client.delete_by_query(index=INDEX, body={'query': {'match_all': {}}})
    
    return {
        'statusCode': 200,
        'body': 'All documents deleted from OpenSearch index.'
    }
'''
    
def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)
