import boto3

client = boto3.client(
                      "sns",
                      aws_access_key_id="xxxx",
                      aws_secret_access_key="xxxx",
                      region_name="us-east-1"
                      )



topic = client.create_topic(Name="AlertEmail")
topic_arn = topic['TopicArn']


def send_Alert_Email(message = "Security Alert: Intruder detected!"):
    response = client.publish(
                          TargetArn=topic_arn,
                          Message=message
                          )



def AWS_detect_labels(image):
    
    IMGclient=boto3.client('rekognition')
    
    
    response =  IMGclient.detect_labels(Image={'Bytes': image.read()})

    alertSent = False
    for label in response['Labels']:
        if alertSent:
            break
        if (label['Name'] == 'Human' or label['Name'] == 'Person') and label ['Confidence'] > 60:
            alertSent = True
            sendAlertEmail(message='A {} was detected with {}% confidence.'.format(label['Name'],label['Confidence']))





'''
    client = boto3.client( service_name = 'iot-data',
    aws_access_key_id='xxxxx',
    aws_secret_access_key='xxxxx',
    region_name='us-east-2'
    )
    
    
    
    def sendAlert(message ='Alert!'):
    print("Sending Message:", message)
    
    JSONPayload = '{"state":{"desired":{"message":' + '\"' + str(message) + '\"' + ', "should_report": null, "Default": null }}}'
    
    response = client.update_thing_shadow(
    thingName='alertUpdate',
    payload=JSONPayload
    )
    print(response)
    '''


'''
    def sendText(message = "Security Alert: Intruder detected!"):
    # Send your sms message.
    response =  Textclient.publish(
    PhoneNumber="123456789",
    Message=message
    )
    print(response)
'''
