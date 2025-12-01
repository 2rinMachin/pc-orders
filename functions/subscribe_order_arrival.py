import os

import boto3

from common import to_json

TOPIC_ARN = os.environ["ORDER_ARRIVALS_TOPIC_ARN"]

sns = boto3.client("sns")


def handler(event, context):
    user = event["detail"]
    sns.subscribe(
        TopicArn=TOPIC_ARN,
        Protocol="email",
        Endpoint=user["email"],
        Attributes={
            "FilterPolicy": to_json(
                {
                    "tenant_id": [user["tenant_id"]],
                    "user_id": [user["user_id"]],
                }
            )
        },
    )
