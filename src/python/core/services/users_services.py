from keycloak import KeycloakAdmin

from core import config
from core.decorators import catch_api_exception
from core.serializers import User


def get_keycloak_admin():
    keycloak_admin = KeycloakAdmin(
        server_url=config.APIConfig.KEYCLOAK_ENDPOINT,
        client_id=config.APIConfig.KEYCLOAK_CLIENT_ID,
        client_secret_key=config.APIConfig.KEYCLOAK_CLIENT_SECRET,
        realm_name=config.APIConfig.KEYCLOAK_REALM)
    
    return keycloak_admin


class UserServices:
    serializer = User

    def _serialize(self, obj, many=False):
        """Serialize object(s) to serializer instances
        
        Args:
            obj: Object or list of objects to serialize
            many: If True, treats obj as a list of objects
            
        Returns:
            Serializer instance or list of serializer instances
        """
        def _create_instance(item: dict) -> User:
            return self.serializer(
                id=item.get("id"),
                firstName=item.get("firstName"),
                lastName=item.get("lastName"),
                enabled=item.get("enabled"),
                email=item.get("email"),
                emailVerified=item.get("emailVerified"),
                creationTime=item.get("createdTimestamp")
            )
            
        if many:
            return [_create_instance(item) for item in obj]
        return _create_instance(obj)
    
    @catch_api_exception
    def list(self):
        """List Users
        :rtype: List[User]
        """
        keycloak_admin = get_keycloak_admin()
        groups = keycloak_admin.get_groups()

        data = []
        for group in groups:
            if group.get("name") == "tornatura":
                users = keycloak_admin.get_group_members(group.get("id"))
                data.extend(self._serialize(users, many=True))

        return data
    
    @catch_api_exception
    def get(self, token_info):
        """get User
        :rtype: User
        """
        keycloak_admin = get_keycloak_admin()
        user = keycloak_admin.get_user(token_info["sub"])
        user = self._serialize(user)

        if "admin" in token_info["resource_access"][config.APIConfig.KEYCLOAK_CLIENT_ID]["roles"]:
            user.accountType = "admin"
        elif "agronomist" in token_info["resource_access"][config.APIConfig.KEYCLOAK_CLIENT_ID]["roles"]:
            user.accountType = "agronomist"
        elif "company" in token_info["resource_access"][config.APIConfig.KEYCLOAK_CLIENT_ID]["roles"]:
            user.accountType = "company"
        
        user.organizations = [{"id": org_id, "name": token_info["organizations"][org_id]["name"], "roles": token_info["organizations"][org_id]["roles"]} for org_id in token_info["organizations"].keys()]
        return user
    
    