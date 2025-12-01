import boto3

from common import resource_name, response
from schemas import FullOrder

sfn = boto3.client("stepfunctions")
dynamodb = boto3.resource("dynamodb")

orders = dynamodb.Table(resource_name("orders"))


def handler(event, context):
    tenant_id = event["pathParameters"]["tenant_id"]
    order_id = event["pathParameters"]["order_id"]

    resp = orders.get_item(Key={"tenant_id": tenant_id, "order_id": order_id})
    item: dict | None = resp.get("Item")

    if item == None:
        return response(404, {"message": "Order not found."})

    order = FullOrder(**item)

    if order.execution_arn != None:
        order.execution_history = sfn.get_execution_history(
            executionArn=order.execution_arn
        )

    return response(200, order)
