import json
import requests
import pandas as pd
import csv
import requests
from linkedin_api import Linkedin
from transformers import TokenClassificationPipeline, AutoModelForTokenClassification, AutoTokenizer
from transformers.pipelines import AggregationStrategy
import numpy as np
import re

host = 'https://search-linkedin-keywords-phrcf56t7zdvmqnt6d7nlea3oq.us-east-1.es.amazonaws.com'
index = 'keywords'
url = host + '/' + index + '/' + '_doc/'
headers = { "Content-Type": "application/json", "Authorization": "Basic Z2lmZmluOkNjYmRAMjAyMw==" }

class KeyphraseExtractionPipeline(TokenClassificationPipeline):
    def __init__(self, model, *args, **kwargs):
        super().__init__(
            model=AutoModelForTokenClassification.from_pretrained(model),
            tokenizer=AutoTokenizer.from_pretrained(model),
            *args,
            **kwargs
        )

    def postprocess(self, model_outputs):
        results = super().postprocess(
            model_outputs=model_outputs,
            aggregation_strategy=AggregationStrategy.SIMPLE,
        )
        return np.unique([result.get("word").strip() for result in results])

def concatenate_values(dictionary):
    values = []

    if "summary" in dictionary:
        values.append(str(dictionary['summary']).replace('\n', '.'))

    if "industryName" in dictionary:
        values.append(str(dictionary['industryName']))

    if 'headline' in dictionary:
        values.append(str(dictionary['headline']))
    
    if 'experience' in dictionary:
        list_of_exp = dictionary['experience']
        for exp in list_of_exp:
            if 'companyName' in exp:
                values.append(str(exp['companyName']))
            if 'description' in exp:
                values.append(str(exp['description']).replace('\n', '.'))
            if 'company' in exp:
                if 'industries' in exp['company']:
                    list_of_industries = exp['company']['industries']
                    for ind in list_of_industries:
                        values.append(str(ind))
            if 'title' in exp:
                values.append(str(exp['title']))

    if 'projects' in dictionary:
        list_of_projs = dictionary['projects']
        for proj in list_of_projs:
            if 'description' in proj:
                values.append(str(proj['description']).replace('\n', '.'))
    
    return values

def populate_keywords(email_id, linkedin_id, company):
    # Authenticate using any Linkedin account credentials
    api = Linkedin('*********', '********')

    # GET a profile
    profile = api.get_profile(linkedin_id)

    #Import model
    model_name = "ml6team/keyphrase-extraction-kbir-inspec"
    extractor = KeyphraseExtractionPipeline(model=model_name)

    text = concatenate_values(profile)
    keyphrases = []

    for line in text:
        txt = re.sub(r'[^\w\s\[\]\(\)\-\.\,]', '', line)
        txt = re.sub(r'\s+', ' ', txt)
        txt = re.sub(r'\.{2,}', '.', txt)
        keyphrase = extractor(txt)
        for phrase in keyphrase:
            keyphrases.append(phrase)

    if 'experience' in profile:
        list_of_exp = profile['experience']
        for exp in list_of_exp:
            if 'title' in exp:
                keyphrases.append(str(exp['title']))

    unique_keyphrases = list(set(keyphrases))

    json_obj = {
        "emailId": email_id,
        "company": company,
        "keywords": unique_keyphrases
    }
    
    # Convert the JSON object to a string
    json_str = json.loads(json.dumps(json_obj))

    r = requests.put(url + email_id, json=json_str, headers=headers)
    if r.status_code != 201:
        print(email_id, " failed")


def get_id_from_link(linkedin_link):
    entries = linkedin_link.split('/')
    link_length = len(linkedin_link)
    if linkedin_link[link_length-1] == '/':
        return entries[-2]
    else:
        return entries[-1]

def main():

    profile_df = pd.read_csv('profile_mac.csv')
    print(profile_df.head())

    for index,row in profile_df.iterrows():
        email_id = "dummy_1_"+str(index)+"@columbia.edu"
        linkedin_url = row['LID']
        if type(linkedin_url) != type(" "):
            print("Skipped")
            continue
        
        linkedin_id = get_id_from_link(linkedin_url)

        response = requests.get('https://n4dcx9l98a.execute-api.us-east-1.amazonaws.com/v1/user-profile?userId='+email_id)

        if 'requests' not in response.json():
            print("Empty request body")
            continue

        company = response.json()['requests']['company']

        populate_keywords(email_id, linkedin_id, company)

        print("Added ",index)

        
if __name__ == '__main__':
    main()
    
