import json
import boto3
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):

    def default(self, obj):

        if isinstance(obj, Decimal):

            return float(obj)

        return super().default(obj)


dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url="http://host.docker.internal:4566",
    region_name="us-east-1"
)

table = dynamodb.Table("NotasFiscais")


def lambda_handler(event, context):

    try:

        response = table.scan()

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(
                response["Items"],
                cls=DecimalEncoder,
                ensure_ascii=False
            )
        }

    except Exception as e:

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "erro": str(e)
                }
            )
        }