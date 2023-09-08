import os

AWS_URL = "http://169.254.169.254"
BUCKET_NAME = os.getenv("BUCKET_NAME")
IMAGE_FOLDER = "images"
SQS_URL = os.getenv("SQS_URL")
TOPIC_ARN = os.getenv("TOPIC_ARN")
