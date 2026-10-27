import json
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')


def obtener_body(event):
    body = event.get('body', event) if isinstance(event, dict) else {}
    if isinstance(body, str):
        body = json.loads(body) if body else {}
    return body or {}


def lambda_handler(event, context):
    body = obtener_body(event)
    bucket = str(body.get('bucket', '')).strip()
    directorio = str(body.get('directorio', '')).strip().strip('/')

    if not bucket or not directorio:
        return {'statusCode': 400, 'mensaje': 'Faltan los campos "bucket" y/o "directorio"'}

    clave = directorio + '/'

    try:
        s3.head_bucket(Bucket=bucket)          # el bucket debe existir
        s3.put_object(Bucket=bucket, Key=clave)  # objeto vacío = "carpeta"
        return {
            'statusCode': 200,
            'bucket': bucket,
            'directorio': clave,
            'mensaje': 'Directorio creado correctamente'
        }
    except ClientError as e:
        codigo = e.response['Error']['Code']
        if codigo in ('404', 'NoSuchBucket'):
            return {'statusCode': 404, 'mensaje': f'El bucket "{bucket}" no existe'}
        if codigo in ('403', 'AccessDenied'):
            return {'statusCode': 403, 'mensaje': f'Sin acceso al bucket "{bucket}"'}
        return {'statusCode': 400, 'error': codigo, 'mensaje': e.response['Error']['Message']}
