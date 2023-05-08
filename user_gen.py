import requests
import csv
from random import randrange
import time

URL = "https://n4dcx9l98a.execute-api.us-east-1.amazonaws.com/v1/create-users"

company_list = ["Google", "Microsoft", "Apple", "Salesforce", "Amazon", "Snap", "Bloomberg", "Facebook", "Meta", "Netflix", "Jane Street", "Citadel", "Akuna Capital", "Slack", "Reddit", "PlayStation", "Autodesk", "A10 Networks", "Adobe", "Samsung", "Palantir", "Databricks", "Twitter"]

hash = set()

with open("profile.csv", "r") as file:
    reader = csv.reader(file, delimiter = "\t")
    for iter, line in enumerate(reader):
        line = line[:2]

        name = line[0].rstrip()
        link = line[1]
        company = randrange(len(company_list))

        if link == "" or name == "":
            continue

        if link in hash:
            continue
        hash.add(link)

        data = {
            "version":"1",
            "region":"us-east-1",
            "userPoolId":"us-east-1_4XHPSeDOO",
            "userName":"965677cb-5d9e-4018-b5be-2f55a4983a8d",
            "callerContext":{
                "awsSdkVersion":"aws-sdk-unknown-unknown",
                "clientId":"23jsf7ag8c7miq9f8v9j6lghrn"
            },
            "triggerSource":"PostConfirmation_ConfirmSignUp",
            "request":{
                "userAttributes":{
                    "sub":"965677cb-5d9e-4018-b5be-2f55a4983a8d",
                    "custom:userType":"alumni",
                    "email_verified":"true",
                    "cognito:user_status":"CONFIRMED",
                    "cognito:email_alias":f"dummy_1_{iter}@columbia.edu",
                    "profile":link,
                    "name":name,
                    "email":f"dummy_1_{iter}@columbia.edu",
                    "custom:company":company_list[company]
                }
            },
            "response":{
                
            }
        }

        resp = requests.post(URL, json = data)
        time.sleep(1)
        if iter % 50 == 0:
            print(iter, name, link, resp.status_code)
