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
    print(f"token: {str(token)}")
    print(f"method_arn: {str(method_arn)}")

    if not token:
        return generate_policy("Deny", method_arn)

    try:
        decoded_token = verify_token(token)
        print(f"decoded_token: {str(decoded_token)}")

        user_id = decoded_token.get("sub")
        email = decoded_token.get("email")

        print(f"user_id: {str(user_id)}")
        print(f"email: {str(email)}")

        if not user_id or not email:
            raise JWTError("Claims 'sub' ou 'email' não encontrados no token")

        policy = generate_policy("Allow", method_arn)
        policy["context"] = {
            "user_id": user_id,
            "email": email
        }

        return policy
    except Exception as error:
        print(f"Erro ao verificar token: {str(error)}")
        return generate_policy("Deny", method_arn)

def extract_token(headers):
    auth_header = headers.get('Authorization') or headers.get('authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    return None

def verify_token(token):
    public_key = get_public_key(token)
    print(f"public_key: {str(public_key)}")

    key = jwk.construct(public_key)
    print(f"key: {str(key)}")

    return jwt.decode(
        token,
        key,
        algorithms=['RS256'],
        issuer=COGNITO_ISSUER,
        options={"verify_aud": False}
    )

def get_public_key(token):
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get('kid')
    if not kid:
        raise JWTError("Token inválido: sem 'kid' no header")

    for key in get_keys().values():
        if key.get('kid') == kid:
            return key
    raise JWTError("Chave pública não encontrada para o 'kid' fornecido")

def get_keys():
    global cached_keys
    if cached_keys is None:
        response = requests.get(JWKS_URL)
        response.raise_for_status()
        cached_keys = {key['kid']: key for key in response.json().get('keys', [])}
    return cached_keys

def generate_policy(effect, resource):
    return {
        "principalId": "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "execute-api:Invoke",
                "Effect": effect,
                "Resource": resource
            }]
        }
    }
