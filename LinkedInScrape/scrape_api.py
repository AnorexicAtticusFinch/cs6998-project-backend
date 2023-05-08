import json
from linkedin_api import Linkedin
from transformers import TokenClassificationPipeline, AutoModelForTokenClassification, AutoTokenizer
from transformers.pipelines import AggregationStrategy
import numpy as np
import re
import requests
from flask import Flask

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

app = Flask(__name__)

@app.route('/<string:profile_id>', methods=['GET'])
def get_profile(profile_id):
    
    #Import model
    model_name = "ml6team/keyphrase-extraction-kbir-inspec"
    extractor = KeyphraseExtractionPipeline(model=model_name)

    api = Linkedin('colcon1@proton.me', '******')
    profile = api.get_profile(profile_id)

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
    print(unique_keyphrases)

    company = "Unknown"
    if 'experience' in profile:
        list_of_exp = profile['experience']
        if len(list_of_exp) != 0 and 'companyName' in list_of_exp[0]:
            company = str(list_of_exp[0]['companyName'])

    return {"company":company, "keywords":unique_keyphrases}

if __name__ == '__main__':
    app.run()
