import boto3
from time import sleep,perf_counter_ns

clients = {}

clients["sns"] = boto3.client(
                      "sns",
                      aws_access_key_id="X",
                      aws_secret_access_key="X",
                      region_name="us-east-1"
                      )
clients["rekognition"] = boto3.client(
                      "rekognition",
                      aws_access_key_id="X",
                      aws_secret_access_key="X",
                      region_name="us-east-2"
                      )


topic = clients["sns"].create_topic(Name="AlertEmail")
topic_arn = topic['TopicArn']


def send_Alert_Email(message = "Security Alert: Intruder detected!"):
    clients["sns"].publish(TargetArn=topic_arn, Message=message)



def AWS_detect_labels(image, cloud_thresh):
    
    IMGclient = clients["rekognition"]

    start_time = perf_counter_ns()
    response = IMGclient.detect_labels(Image={'Bytes': image.read()})
    elapsed_ns = perf_counter_ns() - start_time
    print("Cloud Inference Response (ns): ", format(elapsed_ns, '.3e'))

    for label in response['Labels']:

        if label['Name'] == 'Human' or label['Name'] == 'Person':
            if label['Confidence'] >= cloud_thresh:
                print("Cloud ALERT!!")
                send_Alert_Email(message='A {} was detected with {}% confidence.'.format(label['Name'],label['Confidence']))
                break

    return elapsed_ns


'''
    def sendText(message = "Security Alert: Intruder detected!"):
    # Send your sms message.
    response =  Textclient.publish(
    PhoneNumber="123456789",
    Message=message
    )
    print(response)
'''
