#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#make asyncrhonous requests to AWS Rekognition

import base64
import datetime
import hashlib
import hmac
import simplejson as json
import requests
import aiohttp
import asyncio
from timeit import default_timer as timer



access_key ='access-key'
secret_key = 'secret-key'
host = 'rekognition.us-east-2.amazonaws.com'
endpoint = 'https://rekognition.us-east-2.amazonaws.com'

# Server region
region = 'us-east-2'
service = 'rekognition'
# Currently, all Rekognition actions require POST requests
method = 'POST'
#Targeted function
amz_target = 'RekognitionService.DetectLabels'
# Amazon content type - Rekognition expects 1.1 x-amz-json
content_type = 'application/x-amz-json-1.1'


async def makeReq(session, photo):
    
    print("Starting request for:", photo)

    # Create a date for headers and the credential string
    now = datetime.datetime.utcnow()
    amz_date = now.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = now.strftime('%Y%m%d') # Date w/o time, used in credential scope
    
    # Canonical request information
    canonical_uri = '/'
    canonical_querystring = ''
    canonical_headers = 'content-type:' + content_type + '\n' + 'host:' + host + '\n' + 'x-amz-date:' + amz_date + '\n' + 'x-amz-target:' + amz_target + '\n'
    
    # list of signed headers
    signed_headers = 'content-type;host;x-amz-date;x-amz-target'
    
    
    # here we build the dictionary for our request data
    # that we will convert to JSON
    
    p1 = open(photo, 'rb')
    
    request_dict = {
        
        "Image": {
            "Bytes": base64.b64encode(p1.read())
    }
    }
    
    
    # Convert our dict to a JSON string as it will be used as our payload
    request_parameters = json.dumps(request_dict)
    #print(request_parameters)
    
    # Generate a hash of our payload for verification by Rekognition
    payload_hash = hashlib.sha256(request_parameters.encode("utf8")).hexdigest()
    

    canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash
    
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = date_stamp + '/' + region + '/' + service + '/' + 'aws4_request'
    string_to_sign = algorithm + '\n' +  amz_date + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode("utf8")).hexdigest()
    
    signing_key = getSignatureKey(secret_key, date_stamp, region, service)
    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()
    
    authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature
    
    headers = { 'Content-Type': content_type,
        'X-Amz-Date': amz_date,
            'X-Amz-Target': amz_target,
                'Authorization': authorization_header}


    # Let's format the JSON string returned from the API for better output
    #formatted_text = json.dumps(json.loads(r.text), indent=4, sort_keys=True)

    #session.get('http://httpbin.org/delay/3') as resp:
    async with  session.post(endpoint, data=request_parameters, headers=headers) as resp:

        print("Finished request for:", photo)
        response = await resp.text()
        formatted_text = json.dumps(json.loads(response), indent=4, sort_keys=True)
        print(formatted_text)
        #return(resp)


def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def getSignatureKey(key, date_stamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning

async def fetch_all(session):

    photos =['frog.png','complex.png','perp.jpg', 'dog.png', 'panda.png','duck.png']
    
    tasks = []
    for photo in photos:
        task = asyncio.create_task(makeReq(session, photo))
        tasks.append(task)
    results = await asyncio.gather(*tasks)


async def main():
    async with aiohttp.ClientSession() as session:
        await fetch_all(session)


if __name__ == '__main__':

    start = timer()
    asyncio.run(main())
    end = timer()
    print("Elapsed Time: " + str(end - start))

