import json
from aws_lambda_types.api_gw import APIGWPayloadV1RequestDict,APIGWPayloadV1RequestContextDict, APIGWPayloadV1ResponseDict


def handler(event: APIGWPayloadV1RequestDict, context: APIGWPayloadV1RequestContextDict) -> APIGWPayloadV1ResponseDict:
    return {
        "statusCode": 200,
        "headers": {},
        "multiValueHeaders": {},
        "body": json.dumps({ "message": "Hello, world!" }),
        "isBase64Encoded": False,
    }
