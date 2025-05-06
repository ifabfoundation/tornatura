from typing import Type
from fastapi import HTTPException, logger, status
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from keycloak import KeycloakOpenID
from core import config
from core.permissions import BasePermission



class SecurityChecker(HTTPBearer):
    permissions_classes = ()

    def __init__(self, *permission_classes: Type[BasePermission], mutually_exclusive: bool = False):
        super(SecurityChecker, self).__init__(auto_error=True)
        self.permissions_classes = permission_classes
        self.mutually_exclusive = mutually_exclusive

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(SecurityChecker, self).__call__(request)

        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            
            token_info = self.info_from_jwt(credentials.credentials)

            if not token_info:
                raise HTTPException(status_code=403, detail="Invalid token credentials")

            conditions = [permission_class.has_permission(token_info) for permission_class in self.permissions_classes]
            if self.mutually_exclusive:
                if not any(conditions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Permission denied")
            else:
                if not all(conditions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Permission denied")
                
            return token_info
        else:
            raise HTTPException(status_code=403, detail="Credentials not provided")

    def info_from_jwt(self, token, **kwargs):
        """
        Check and retrieve authentication information from custom bearer token.
        Returned value will be passed in 'token_info' parameter of your operation function, if there is one.
        'sub' or 'uid' will be set in 'user' parameter of your operation function, if there is one.

        :param token Token provided by Authorization header
        :type token: str
        :return: Decoded token information or None if token is invalid
        :rtype: dict | None
        """
        # Configure client
        keycloak_openid = KeycloakOpenID(server_url=config.APIConfig.KEYCLOAK_ENDPOINT,
                                        client_id=config.APIConfig.KEYCLOAK_CLIENT_ID,
                                        realm_name=config.APIConfig.KEYCLOAK_REALM)
        
        options = {"aud": config.APIConfig.KEYCLOAK_CLIENT_ID, "exp": None}

        try:
            return keycloak_openid.decode_token(token, validate=True, check_claims=options)
        except Exception as ex:
            logger.logger.error(f"Error decoding token: {ex}")
            return None
    
            
    def check_object_permission(self, token_info, obj):
        """Check if the user has permission for a specific object"""
        conditions = [permission_class.has_object_permission(token_info, obj) for permission_class in self.permissions_classes]
        if self.mutually_exclusive:
            if not any(conditions):
                 raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Permission denied for this resource"
                )
        else:
            if not all(conditions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Permission denied for this resource"
                )
        return True
    