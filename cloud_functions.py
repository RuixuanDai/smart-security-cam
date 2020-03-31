
import boto3

client = boto3.client( service_name = 'iot-data',
                        aws_access_key_id='AKIAVQY6WPNC3FVUXSMZ',
                        aws_secret_access_key='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',
                        region_name='us-east-2'
                        )



def sendAlert(message ='Alert!'):
    print("Sending Message:", message)
    
    JSONPayload = '{"state":{"desired":{"message":' + '\"' + str(message) + '\"' + '}}}'

    response = client.update_thing_shadow(
                                          thingName='alertUpdate',
                                          payload=JSONPayload
                                          )
    # print(response)





