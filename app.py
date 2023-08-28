import os
import shutil
import uuid
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# boto3.setup_default_session(profile_name="FullAccessEC2User")
app = FastAPI()

AWS_URL = "http://169.254.169.254"

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
MEDIA_FOLDER_PATH = "./media"


@app.get("/")
async def instance_info():
    response = requests.get(f"{AWS_URL}/latest/meta-data/placement/availability-zone")
    return {"AZ": response.text, "region": response.text[:-1]}


@app.get("/images/{name}")
def downloaded_image(name: str):
    return FileResponse(f"{MEDIA_FOLDER_PATH}/{name}")


@app.get("/images/metadata")
def random_metadata(name: str):
    ...


@app.get("/images/metadata/{name}")
def get_image_metadata(name: str):
    ...


@app.post("/images")
def upload_image(file: UploadFile = File(...)):
    try:
        filename = file.filename or uuid.uuid4().hex
        with open(f"./media/{filename}", "wb") as f:
            shutil.copyfileobj(file.file, f)
        metadata = create_metadata(filename)
        
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()
    
    return {"message": f"Successfully uploaded {file.filename}", "metadata": metadata}


@app.delete("/images/{name}")
def delete_image(name: str):
    if os.path.isfile(f"{MEDIA_FOLDER_PATH}/{name}"):
        os.remove(f"{MEDIA_FOLDER_PATH}/{name}")
        return {"message": "File successfully deleted"}
    else:
        return {"message": "NO such file"}


def create_metadata(filename: str) -> dict[str, Any]:
    stat = os.stat(f"{MEDIA_FOLDER_PATH}/{filename}")
    return {
        "size": stat.st_size,
        "updated_at": stat.st_mtime,
        "extension": Path(filename).suffix,
        "name": Path(filename).stem,
    }
