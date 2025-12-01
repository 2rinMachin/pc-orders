from datetime import datetime, timezone

import boto3
from pydantic import BaseModel

from common import PROJECT_NAME, STAGE, parse_body, resource_name, response, to_json
from schemas import AuthorizedUser, Order, OrderHistoryEntry, OrderStatus, UserRole

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


ROLE_REQUIREMENTS = {
    OrderStatus.cooking: UserRole.cook,
    OrderStatus.wait_for_dispatcher: UserRole.cook,
    OrderStatus.dispatching: UserRole.dispatcher,
    OrderStatus.wait_for_deliverer: UserRole.dispatcher,
    OrderStatus.delivering: UserRole.driver,
    OrderStatus.complete: UserRole.driver,
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

    orders = dynamodb.Table(resource_name("orders"))

    resp = orders.get_item(Key={"tenant_id": tenant_id, "order_id": order_id})
    item: dict | None = resp.get("Item")

    if item == None:
        return response(404, {"message": "Order not found."})

    user = AuthorizedUser(**event["requestContext"]["authorizer"])
    order = Order(**item)

    required_status = STATUS_REQUIREMENTS.get(data.status)
    required_role = ROLE_REQUIREMENTS.get(data.status)

    # TODO: uncomment when ready
    # if required_role != None and required_role != user.role:
    #     return response(403, {"message": "Forbidden."})

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

    if data.status == OrderStatus.cooking:
        orders.update_item(
            Key={"tenant_id": tenant_id, "order_id": order_id},
            UpdateExpression="SET cook = :cook, cook_id = :cook_id",
            ExpressionAttributeValues={
                ":cook": user.model_dump(),
                ":cook_id": user.user_id,
            },
        )
    elif data.status == OrderStatus.dispatching:
        orders.update_item(
            Key={"tenant_id": tenant_id, "order_id": order_id},
            UpdateExpression="SET dispatcher = :dispatcher, dispatcher_id = :dispatcher_id",
            ExpressionAttributeValues={
                ":dispatcher": user.model_dump(),
                ":dispatcher_id": user.user_id,
            },
        )
    elif data.status == OrderStatus.delivering:
        orders.update_item(
            Key={"tenant_id": tenant_id, "order_id": order_id},
            UpdateExpression="SET driver = :driver, driver_id = :driver_id",
            ExpressionAttributeValues={
                ":driver": user.model_dump(),
                ":driver_id": user.user_id,
            },
        )

    update_resp = orders.update_item(
        Key={"tenant_id": tenant_id, "order_id": order_id},
        UpdateExpression="""
        SET #s = :status,
            history = list_append(:entry, if_not_exists(history, :empty))
        """,
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":status": data.status,
            ":entry": [
                OrderHistoryEntry(
                    user=user,
                    status=data.status,
                    date=datetime.now(timezone.utc).isoformat(),
                ).model_dump()
            ],
            ":empty": [],
        },
        ReturnValues="ALL_NEW",
    )

    new_order = update_resp["Attributes"]

    event_bridge.put_events(
        Entries=[
            {
                "Source": f"{PROJECT_NAME}-{STAGE}.orders",
                "DetailType": "order.status_updated",
                "Detail": to_json(new_order),
            }
        ]
    )

    return response(200, new_order)
