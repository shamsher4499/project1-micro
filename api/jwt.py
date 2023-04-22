import jwt
from microApp.settings import JWT_SECRET_KEY

jwt_options = {
        'verify_signature': False,
        'verify_exp': True,
        'verify_nbf': False,
        'verify_iat': True,
        'verify_aud': False
        }

def authenticate(request):
    """
    The code is trying to authenticate a request.
    It is checking for an HTTP_AUTHORIZATION header in the request, and if it doesn't exist, returning None.
    If there is an HTTP_AUTHORIZATION header, then it splits the string on spaces into two parts: token and secret key.
    The token is used to decode a JWT (JSON Web Token) from the secret key using jwt-decode().
    Then data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'], options=jwt_options).
    Finally return data or return None depending on whether or not there was an error decoding the token with jwt-decode().
    The code is a function that takes in a request object and checks for an HTTP_AUTHORIZATION header.
    If there is no HTTP_AUTHORIZATION header, then the code returns None.
    Otherwise, it will return data from jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'], options=jwt_options).
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if auth_header is None:
        return None
    
    token = auth_header.split(' ')[1]
    try:
        data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'], options=jwt_options)
        return data
    except jwt.DecodeError:
        return None