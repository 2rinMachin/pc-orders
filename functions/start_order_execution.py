import os

import boto3

from common import resource_name
from schemas import Order

SFN_ARN = os.environ["AWS_SFN_ARN"]

sfn = boto3.client("stepfunctions")
dynamodb = boto3.resource("dynamodb")
orders = dynamodb.Table(resource_name("orders"))


def handler(event, context):
    order = Order(**event["detail"])

    execution = sfn.start_execution(
        stateMachineArn=SFN_ARN,
        input=order.model_dump_json(),
    )

    orders.update_item(
        Key={"tenant_id": order.tenant_id, "order_id": order.order_id},
        UpdateExpression="SET execution_arn = :arn",
        ExpressionAttributeValues={":arn": execution["executionArn"]},
    )
