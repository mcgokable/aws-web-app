from fastapi import FastAPI, Depends
import boto3
from fastapi.middleware.cors import CORSMiddleware

# boto3.setup_default_session(profile_name="FullAccessEC2User")
app = FastAPI()

INSTANCE_ID = "i-0abf051a8e0682019"

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_ec2_client():
    return boto3.client("ec2")


@app.get("/")
async def instance_info(client=Depends(get_ec2_client)):
    instance_info = client.describe_instances(InstanceIds=[INSTANCE_ID])                           
    return {"AZ": instance_info["Reservations"][0]["Instances"][0]["Placement"]["AvailabilityZone"], "region": None}