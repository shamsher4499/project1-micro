from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except InvalidToken:
            # Custom error message for invalid token
            error_message = {'code': 401, 'detail':'Token expired'}
            raise AuthenticationFailed(**error_message)