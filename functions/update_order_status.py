import boto3
from pydantic import BaseModel

from common import PROJECT_NAME, parse_body, response, table_name, to_json
from schemas import Order, OrderStatus

dynamodb = boto3.resource("dynamodb")
event_bridge = boto3.client("events")

STATUS_REQUIREMENTS = {
    OrderStatus.cooking: OrderStatus.wait_for_cook,
    OrderStatus.wait_for_dispatcher: OrderStatus.cooking,
    OrderStatus.dispatching: OrderStatus.wait_for_dispatcher,
    OrderStatus.wait_for_deliverer: OrderStatus.dispatching,
    OrderStatus.delivering: OrderStatus.wait_for_deliverer,
    OrderStatus.complete: OrderStatus.delivering,
}


class UpdateOrderStatusRequest(BaseModel):
    status: OrderStatus


def handler(event, context):
    tenant_id = event["pathParameters"]["tenant_id"]
    order_id = event["pathParameters"]["order_id"]

    data, err = parse_body(UpdateOrderStatusRequest, event)
    if err != None:
        return err

    assert data != None

    orders = dynamodb.Table(table_name("orders"))

    resp = orders.get_item(Key={"tenant_id": tenant_id, "order_id": order_id})
    item: dict | None = resp.get("Item")

    if item == None:
        return response(404, {"message": "Order not found."})

    order = Order(**item)

    required_status = STATUS_REQUIREMENTS.get(data.status)

    if required_status == None:
        return response(
            409, {"message": f"An order status cannot be updated to '{data.status}'."}
        )

    if order.status != required_status:
        return response(
            409,
            {
                "message": f"Order must be in '{required_status}' status, but is on '{order.status}'."
            },
        )

    update_resp = orders.update_item(
        Key={"tenant_id": tenant_id, "order_id": order_id},
        UpdateExpression="SET #s = :new_status",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":new_status": data.status},
        ReturnValues="ALL_NEW",
    )

    new_order = update_resp["Attributes"]

    event_bridge.put_events(
        Entries=[
            {
                "Source": f"{PROJECT_NAME}.orders",
                "DetailType": "order.status_updated",
                "Detail": to_json(new_order),
            }
        ]
    )

    return response(200, new_order)
