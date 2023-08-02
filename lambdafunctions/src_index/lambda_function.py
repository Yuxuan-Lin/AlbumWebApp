import json
import boto3
import requests
from requests_aws4auth import AWS4Auth
import base64

region = 'us-east-1' # For example, us-west-1
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)


host = 'https://search-myalbumdomain-icnkz72tj52u2m6hy2jueia46i.us-east-1.es.amazonaws.com' # The OpenSearch domain endpoint with https:// and without a trailing slash
index = 'photos'
url = host + '/' + index + '/_doc'
headers = { "Content-Type": "application/json" }

rek = boto3.client('rekognition')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    if not event or len(event['Records']) == 0:
        return
    
    photo = event['Records'][0]['s3']['object']['key']
    bucket = event['Records'][0]['s3']['bucket']['name']
    created_time = event['Records'][0]['eventTime']
    
    # photo = '1690760238506Image3.jpg'
    # bucket = 'albumbucketkerwin2'
    # created_time = '2032-07-26T14:32:55.683Z'
    
    s3obj = s3.get_object(Bucket=bucket, Key=photo)

    if 'x-amz-meta-customlabels' in s3obj['ResponseMetadata']['HTTPHeaders']:
        customlabels = s3obj['ResponseMetadata']['HTTPHeaders']['x-amz-meta-customlabels'].split(',')
    else:
        customlabels = []

    base64_image_binary = s3obj['Body'].read() #this contains data:image/jpeg;base64,
    base64_image_string_only_data = base64_image_binary.decode('utf-8').split(',')[1]
    image_bytes = bytes(base64.b64decode(base64_image_string_only_data))

    # client = boto3.client('rekognition')
    rekognitionImageObj = {'Bytes': image_bytes}
    rek_response = rek.detect_labels(Image=rekognitionImageObj)
    
    
    if rek_response['ResponseMetadata']['HTTPStatusCode'] != 200 or len(rek_response['Labels']) == 0:
        return
    
    labels = []
    for item in rek_response['Labels']:
        if item['Confidence'] > 90.0:
            labels.append(item['Name'])
            
    print(labels)
    
    # Build target json for opensearch
    index_json = {
        'objectKey': photo,
        'bucket': bucket,
        'createdTimestamp': created_time,
        'labels': labels
    }
    
    # print(index_json)
    
    opensearch_res = requests.post(url, auth=awsauth, json=index_json, headers=headers)
    
    res_json = opensearch_res.json()
    
    print(res_json)
    
    if res_json['result'] == 'created': 
        return {
            'statusCode': 200,
            'body': json.dumps("The photo was uploaded successfully")
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps("Something wrong during photo upload, please try again")
        }