import boto3
from boto3.dynamodb.conditions import Key

from common import response, table_name

dynamodb = boto3.resource("dynamodb")


def handler(event, context):
    tenant_id = event["pathParameters"]["tenant_id"]

    orders = dynamodb.Table(table_name("orders"))

    resp = orders.query(KeyConditionExpression=Key("tenant_id").eq(tenant_id))
    orders = resp["Items"]

    return response(200, orders)
