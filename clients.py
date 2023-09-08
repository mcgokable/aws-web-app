import os

import boto3
import psycopg2

from logger import logger


def s3_client():
    return boto3.client("s3")


def sqs_client():
    return boto3.client("sqs", region_name="us-east-1")


def sns_client():
    return boto3.client("sns", region_name="us-east-1")


def get_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
        logger.info("Connetcion is ready")
    except Exception as e:
        logger.error("Exception occured: %s" % e)
        raise
    return conn
