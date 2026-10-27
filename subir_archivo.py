import json
import base64
import binascii
import mimetypes
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
    nombre = str(body.get('nombre_archivo', '')).strip()
    contenido_b64 = str(body.get('contenido_base64', '')).strip()

    if not bucket or not directorio or not nombre or not contenido_b64:
        return {'statusCode': 400,
                'mensaje': 'Campos requeridos: bucket, directorio, nombre_archivo, contenido_base64'}
    if '/' in nombre:
        return {'statusCode': 400, 'mensaje': '"nombre_archivo" no debe contener "/"'}

    try:
        contenido = base64.b64decode(contenido_b64, validate=True)
    except (binascii.Error, ValueError):
        return {'statusCode': 400, 'mensaje': '"contenido_base64" no es base64 valido'}

    prefijo = directorio + '/'

    try:
        s3.head_bucket(Bucket=bucket)
        existe = s3.list_objects_v2(Bucket=bucket, Prefix=prefijo, MaxKeys=1)
        if existe.get('KeyCount', 0) == 0:
            return {'statusCode': 404,
                    'mensaje': f'El directorio "{prefijo}" no existe en el bucket "{bucket}"'}

        clave = prefijo + nombre
        tipo = mimetypes.guess_type(nombre)[0] or 'application/octet-stream'
        s3.put_object(Bucket=bucket, Key=clave, Body=contenido, ContentType=tipo)

        return {
            'statusCode': 200,
            'bucket': bucket,
            'archivo': clave,
            'tamano_bytes': len(contenido),
            'content_type': tipo,
            'mensaje': 'Archivo subido correctamente'
        }
    except ClientError as e:
        codigo = e.response['Error']['Code']
        if codigo in ('404', 'NoSuchBucket'):
            return {'statusCode': 404, 'mensaje': f'El bucket "{bucket}" no existe'}
        return {'statusCode': 400, 'error': codigo, 'mensaje': e.response['Error']['Message']}
