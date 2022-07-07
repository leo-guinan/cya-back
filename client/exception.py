from rest_framework.exceptions import APIException


class UnknownClient(APIException):
    status_code = 404
    default_detail = 'Client Not Found'
    default_code = 'client_not_found'


class UnknownClientAccount(APIException):
    status_code = 404
    default_detail = 'Client Account Not Found'
    default_code = 'client_account_not_found'
