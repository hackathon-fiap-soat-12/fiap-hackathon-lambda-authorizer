import json
import requests
import os
from jose import jwt, JWTError
from jose import jwk

USER_POOL_ID = os.getenv('USER_POOL_ID', 'us-east-1_lmpQVedyx')
REGION = os.getenv('AWS_REGION', 'us-east-1')
COGNITO_ISSUER = f'https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}'
JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"

cached_keys = None

def lambda_handler(event, context):
    token = extract_token(event.get('headers', {}))
    method_arn = event.get('methodArn')

    if not token:
        return generate_policy("Deny", method_arn)

    try:
        verify_token(token)
        return generate_policy("Allow", method_arn)
    except Exception as error:
        print(f"Erro ao verificar token: -> {error}")
        return generate_policy("Deny", method_arn)

def extract_token(headers):
    auth_header = headers.get('Authorization') or headers.get('authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.replace('Bearer ', '')
    return None

def verify_token(token):
    public_key = get_public_key(token)

    key = jwk.construct(public_key)

    jwt.decode(token, key, algorithms=['RS256'], issuer=COGNITO_ISSUER)

def get_public_key(token):
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get('kid')

    if not kid:
        raise JWTError('Token inválido: cabeçalho sem `kid`.')

    public_key = None
    for key, value in get_keys().items():
        if value.get('kid') == kid:
            public_key = value
            break

    if public_key is None:
        raise JWTError('Chave pública correspondente não encontrada')

    return public_key

def get_keys():
    global cached_keys
    if cached_keys is None:
        response = requests.get(JWKS_URL)
        response.raise_for_status()
        keys = response.json().get('keys', [])
        cached_keys = {key['kid']: key for key in keys}
    return cached_keys

def generate_policy(effect, resource):
    if not effect or not resource:
        raise ValueError("Efeito e recurso são obrigatórios para gerar uma política.")

    return {
        "principalId": "Grant_Access_To_API",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "execute-api:Invoke",
                "Effect": effect,
                "Resource": resource
            }]
        }
    }
