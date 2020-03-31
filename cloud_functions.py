
import boto3

client = boto3.client( service_name = 'iot-data',
                        aws_access_key_id='xxxxx',
                        aws_secret_access_key='xxxxx',
                        region_name='us-east-2'
                        )



def sendAlert(message ='Alert!'):
    print("Sending Message:", message)
    
    JSONPayload = '{"state":{"desired":{"message":' + '\"' + str(message) + '\"' + '}}}'

    response = client.update_thing_shadow(
                                          thingName='alertUpdate',
                                          payload=JSONPayload
                                          )
    print(response)





