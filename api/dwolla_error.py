from dwollav2.error import *
from api.status_code import *

# dwolla_exception = (
# AccessDeniedError,
# InvalidCredentialsError,
# NotFoundError,
# BadRequestError,
# InvalidGrantError,
# RequestTimeoutError,
# ExpiredAccessTokenError,
# InvalidRequestError,
# ServerError,
# ForbiddenError,
# InvalidResourceStateError,
# TemporarilyUnavailableError,
# InvalidAccessTokenError,
# InvalidScopeError,
# UnauthorizedClientError,
# InvalidAccountStatusError,
# UnsupportedGrantTypeError,
# InvalidApplicationStatusError,
# InvalidVersionError,
# UnsupportedResponseTypeError,
# InvalidClientError,
# MethodNotAllowedError,
# ValidationError,
# TooManyRequestsError,
# ConflictError
# )
def dwolla_error_code1(dwolla_instance):
    print('000000000000000000')
    try:
        return {
            'status':True,
            'message': 'Success',
            'data': dwolla_instance
        }
    except ValidationError as e:
        print(e, '---------------')
        return {
            'status':False,
            'message': e.body['_embedded']['errors'][0]['message'],
            'status_code': e.status
        } 
    finally:
        return {
            'status':False,
            'message': 'Something went wrong',
            'status_code': HTTP_400_BAD_REQUEST
        } 

