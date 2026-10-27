import json
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')


def obtener_body(event):
    # Integración lambda (no proxy): body llega como dict.
    # Integración proxy o prueba directa: puede llegar como string o sin "body".
    body = event.get('body', event) if isinstance(event, dict) else {}
    if isinstance(body, str):
        body = json.loads(body) if body else {}
    return body or {}


def lambda_handler(event, context):
    body = obtener_body(event)
    nombre = str(body.get('bucket', '')).strip()

    if not nombre:
        return {'statusCode': 400, 'mensaje': 'Falta el campo "bucket"'}

    try:
        region = s3.meta.region_name
        if region == 'us-east-1':
            s3.create_bucket(Bucket=nombre)
        else:
            s3.create_bucket(
                Bucket=nombre,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        return {
            'statusCode': 200,
            'bucket': nombre,
            'region': region,
            'mensaje': 'Bucket creado correctamente'
        }
    except ClientError as e:
        error = e.response['Error']
        codigo = error['Code']
        return {
            'statusCode': 409 if codigo in ('BucketAlreadyExists', 'BucketAlreadyOwnedByYou') else 400,
            'error': codigo,
            'mensaje': error['Message']
        }
