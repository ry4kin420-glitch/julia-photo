import json
from dataclasses import dataclass

import boto3


@dataclass
class S3Config:
    endpoint: str
    key: str
    secret: str
    bucket: str


def build_s3_client(config: S3Config):
    return boto3.client(
        "s3",
        endpoint_url=config.endpoint,
        aws_access_key_id=config.key,
        aws_secret_access_key=config.secret,
    )


def store_json(client, bucket: str, key: str, payload: dict) -> None:
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
    )
