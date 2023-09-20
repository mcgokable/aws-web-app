import json
import logging

import boto3
import urllib3

logger = logging.getLogger(__name__)

SQS_URL = "https://sqs.us-east-1.amazonaws.com/420414205977/-PythonWebApp-UploadNotificationQueue"
TOPIC_ARN = "arn:aws:sns:us-east-1:420414205977:PythonWebApp-UploadNotificationTopic"
AWS_URL = "http://169.254.169.254"


def sqs_client():
    return boto3.client("sqs", region_name="us-east-1")


def sns_client():
    return boto3.client("sns", region_name="us-east-1")


def get_ip_address() -> str:
    # http = urllib3.PoolManager()
    # url = f"{AWS_URL}/latest/meta-data/public-ipv4"
    # return http.request("GET", url).data.decode("utf-8")
    return "fake_ip"


def build_message(message: str, metadata: str) -> str:
    meta = json.loads(metadata)
    message = (
        message
        + f"\n - Metadata: {metadata}. Link for downloading: http://{get_ip_address()}/images/{meta['name']}{meta['extension']}"
    )
    return message


def polling_queue():
    try:
        logger.info("Start polling queue...")
        sqs = sqs_client()
        messages = sqs.receive_message(
            QueueUrl=SQS_URL,
            AttributeNames=["All"],
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,
        )
        if messages := messages.get("Messages"):
            sns = sns_client()
            result = "New message(s) was uploaded."
            messages_for_delete = []
            for ind, message in enumerate(messages, 1):
                result = build_message(result, message["Body"])
                messages_for_delete.append(
                    {"Id": str(ind), "ReceiptHandle": message["ReceiptHandle"]}
                )
            print(f"Message for publish: {result}")
            sns.publish(
                TopicArn=TOPIC_ARN,
                Message=result,
                Subject="New image was uploaded",
            )
            print(f"Messages for deleting: {messages_for_delete}")
            sqs.delete_message_batch(QueueUrl=SQS_URL, Entries=messages_for_delete)
            return "successful"
    except Exception as e:
        logger.error(f"Exception occured {str(e)}")
        return "failed"


def lambda_handler(event, context):
    print("Hello from Lambda )")
    result = polling_queue()
    return {"statusCode": 200, "body": result}
