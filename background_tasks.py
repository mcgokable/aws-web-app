import json
from time import sleep

import requests

from clients import sns_client, sqs_client
from constants import AWS_URL, SQS_URL, TOPIC_ARN
from logger import logger


def get_ip_address() -> str:
    return requests.get(f"{AWS_URL}/latest/meta-data/public-ipv4").text


def build_message(metadata: str) -> str:
    meta = json.loads(metadata)
    message = f"Image was uploaded.\nMetadata: {metadata}\nLink for downloading: http://{get_ip_address()}/images/{meta['name']}{meta['extension']}"
    return message


def polling_queue(timeout: int):
    while True:
        try:
            logger.info("Start polling queue...")
            sqs = sqs_client()
            messages = sqs.receive_message(
                QueueUrl=SQS_URL,
                AttributeNames=["All"],
                MaxNumberOfMessages=10,
                WaitTimeSeconds=5,
            )
            if messages := messages.get("Messages"):
                sns = sns_client()
                for message in messages:
                    sns.publish(
                        TopicArn=TOPIC_ARN,
                        Message=build_message(message["Body"]),
                        Subject="New image was uploaded",
                    )
                    sqs.delete_message(
                        QueueUrl=SQS_URL, ReceiptHandle=message["ReceiptHandle"]
                    )
            sleep(timeout)
        except Exception as e:
            logger.error(f"Exception occured {str(e)}")
