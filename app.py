import json
import uuid
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
import requests
from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from clients import get_connection, s3_client, sns_client, sqs_client, lambda_client
from constants import (
    AWS_URL,
    BUCKET_NAME,
    IMAGE_FOLDER,
    SQS_URL,
    TOPIC_ARN,
    LAMBDA_VALIDATION_NAME,
)
from logger import logger

app = FastAPI()


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def instance_info():
    response = requests.get(f"{AWS_URL}/latest/meta-data/placement/availability-zone")
    return {"AZ": response.text, "region": response.text[:-1]}


@app.get("/images/metadata")
def random_metadata(connection=Depends(get_connection)):
    with connection:
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM metadata ORDER BY random() LIMIT 1")
        result = cursor.fetchone()
    return result


@app.get("/images/{filename}")
def download_image(filename: str, client=Depends(s3_client)):
    image = client.get_object(Bucket=BUCKET_NAME, Key=f"{IMAGE_FOLDER}/{filename}")
    return StreamingResponse(
        content=image["Body"].iter_chunks(), media_type="image/png"
    )


@app.get("/images/metadata/{name}")
def get_image_metadata(name: str, connection=Depends(get_connection)):
    with connection:
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(f"SELECT * FROM metadata WHERE name='{name}'")
        result = cursor.fetchone()
    return result


@app.post("/images")
def upload_image(
    file: UploadFile = File(...),
    client=Depends(s3_client),
    sqs_client=Depends(sqs_client),
    connection=Depends(get_connection),
):
    try:
        filename = file.filename or uuid.uuid4().hex
        metadata = create_metadata(file.size, filename)
        with connection:
            cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute(
                "INSERT INTO metadata (name, extension, size) VALUES (%s, %s, %s)",
                tuple(metadata.values()),
            )
        client.upload_fileobj(file.file, BUCKET_NAME, f"{IMAGE_FOLDER}/{filename}")
        sqs_client.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(metadata))

    except Exception as e:
        return {"message": "There was an error uploading the file" + str(e.args)}
    finally:
        file.file.close()

    return {
        "message": f"Successfully uploaded {file.filename}",
        "metadata": metadata,
    }


@app.delete("/images/{name}")
def delete_image(
    filename: str,
    client=Depends(s3_client),
    connection=Depends(get_connection),
):
    client.delete_object(Bucket=BUCKET_NAME, Key=f"{IMAGE_FOLDER}/{filename}")
    try:
        with connection:
            name, extension = get_name_and_extension(filename)
            cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute(
                f"DELETE FROM metadata WHERE name='{name}' and extension='{extension}'"
            )
        return {"message": "Image deleted"}
    except Exception as e:
        logger.error("Error ocured: %s", e)
        return {"message": f"Error occured {e}"}


@app.get("/subscribe")
def subscribe(email: str, client=Depends(sns_client)):
    response = client.subscribe(
        TopicArn=TOPIC_ARN,
        Protocol="email",
        Endpoint=email,
        ReturnSubscriptionArn=True,
    )
    logger.info("Subscribtion response: %s", response)
    return {
        "message": "You are successfully subscribed.",
        "subscription_arn": response["SubscriptionArn"],
    }


@app.get("/validate")
def validate(client=Depends(lambda_client)):
    client.invoke(FunctionName=LAMBDA_VALIDATION_NAME, LogType="Tail")


def build_message(metadata: str) -> str:
    meta = json.loads(metadata)
    ip_address = requests.get(f"{AWS_URL}/latest/meta-data/public-ipv4")
    message = f"Image was uploaded.\nMetadata: {metadata}\nLink for downloading: http://{ip_address}/images/{meta['name']}{meta['extension']}"
    return message


@app.get("/unsubscribe")
def unsubscribe(subscription_arn: str, client=Depends(sns_client)):
    response = client.unsubscribe(
        SubscriptionArn=subscription_arn,
    )
    logger.info("Unsubscription response: %s", response)
    return {"message": "You are unsubscribed successfully."}


def get_name_and_extension(filename: str) -> tuple[str, str]:
    return Path(filename).stem, Path(filename).suffix


def create_metadata(size, filename: str) -> dict[str, Any]:
    name, extension = get_name_and_extension(filename)
    return {
        "name": name,
        "extension": extension,
        "size": size,
    }
