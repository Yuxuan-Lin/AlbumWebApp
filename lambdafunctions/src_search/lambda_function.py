import json
import boto3
import uuid
import requests
from requests_aws4auth import AWS4Auth
import base64

region = 'us-east-1' # For example, us-west-1
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)


host = 'https://search-myalbumdomain-icnkz72tj52u2m6hy2jueia46i.us-east-1.es.amazonaws.com' # The OpenSearch domain endpoint with https:// and without a trailing slash
index = 'photos'
url = host + '/' + index + '/_search'
headers = { "Content-Type": "application/json" }

lex = boto3.client('lexv2-runtime')

s3 = boto3.resource('s3')


def lambda_handler(event, context):
    # TODO implement
    # return {
    #     'statusCode': 200,
    #     'body': json.dumps(event['queryStringParameters']['q'])
    # }
    # Get query text from event
    query_text = event['queryStringParameters']['q']
    # query_text = 'Show me photos with dogs and apples in them'
    
    # Call lex with query text
    lex_response = lex.recognize_text(
            botId='EROCIKJPBZ',
            botAliasId='TSTALIASID',
            localeId='en_US',
            sessionId=str(uuid.uuid4()),
            text=query_text
        )
    
    if lex_response['ResponseMetadata']['HTTPStatusCode'] != 200:
        print("Lex returned error response")
        return {
            'statusCode': 200,
            'body': json.dumps(lex_response)
        }
    
    # Get search labels from lex response
    search_labels = lex_response['sessionState']['intent']['slots']['Labels']['value']['interpretedValue'].split()
    
    print(search_labels)
    
    # Note that certain fields are boosted (^).
    query = {
              "size": 10,
              "query": {
                "fuzzy": {
                  "labels": {
                    "value": "",
                    "fuzziness": 2
                  }
                }
              }
            }


    # Make the signed HTTP request
    imgs = []
    matched_obj = {}
    
    for search_label in search_labels:
        query["query"]["fuzzy"]["labels"]["value"] = search_label
        os_res = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))
    
        print(os_res.text)
        print(type(os_res.text))
        
        text_obj = json.loads(os_res.text)
        
        if len(text_obj['hits']['hits']) == 0:
            continue
        
        search_results = text_obj['hits']['hits']
        
        for sr in search_results:
            obj_key = sr['_source']['objectKey']
            if obj_key in matched_obj:
                continue
            else:
                matched_obj[obj_key] = 0
            s3_bucket = s3.Bucket(sr['_source']['bucket'])
            s3_obj = s3_bucket.Object(key=sr['_source']['objectKey'])
            s3_res = s3_obj.get()
            s3_img = s3_res[u'Body'].read()
            if not s3_img.startswith(b'data'):
                my_obj = [base64.b64encode(s3_img)]
            else:
                my_obj = [s3_img]
            my_json = str(my_obj[0])
            my_json = my_json.replace("b'", "")
            encoded_img = my_json.replace("'", "")
            imgs.append(encoded_img)
            
    if len(imgs) == 0:
        return {
            "statusCode": 500,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body':json.dumps({
                "message": "Could not find any photo matching the search indices"
            })
        }
    
    lambda_response = {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body':json.dumps({
            'message': 'Found {} photos matching the search indices'.format(len(imgs)),
            'encoded_image': imgs
        })
    }
    
    print(lambda_response)
    
    return lambda_response
