from enum import Enum
import json
import os
import random
import string
from jinja2 import Environment, FileSystemLoader
from keycloak import KeycloakAdmin, KeycloakOpenID
import phasetwo
from phasetwo.apis.tags import users_api
from phasetwo.model.organization_representation import OrganizationRepresentation
from phasetwo.model.organization_role_representation import OrganizationRoleRepresentation
from core import config
from core.decorators import catch_api_exception
from core.serializers import AccountTypeEnum, User, UserCreatePayload, UserUpdatePayload, FileInfo
from core.services.files_services import FileServices
from core.utils import send_email

env = Environment(loader=FileSystemLoader(os.path.join(config.APIConfig.BASE_DIR, 'templates/')))

class ClientRole(Enum):
    Admin = "admin-access"
    Agronomist = "agronomist-access"
    CompanyOwner = "company-owner-access"
    CompanyManager = "company-manager-access"
    CompanyStandard = "company-standard-access"


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
            obj =  self.serializer(
                id=item.get("id"),
                firstName=item.get("firstName"),
                lastName=item.get("lastName"),
                enabled=item.get("enabled"),
                email=item.get("email"),
                emailVerified=item.get("emailVerified"),
                phone=item.get("attributes", {}).pop("phone", [''])[0],
                piva=item.get("attributes", {}).pop("piva", [''])[0],
                avatar=item.get("attributes", {}).pop("avatar", [''])[0],
                accountType=item.get("accountType"),
                organizations=item.get("organizations", []),
                creationTime=item.get("createdTimestamp")
            )

            if obj.avatar:
                file_services = FileServices()
                obj.avatar = file_services.get_avatar_url(obj.id, obj.avatar)
        
            return obj
            
        if many:
            return [_create_instance(item) for item in obj]
        return _create_instance(obj)
    
    @classmethod
    def _get_client(cls) -> dict | None:
        keycloak_admin = get_keycloak_admin()
        clients = keycloak_admin.get_clients()
        for client in clients:
            if client["clientId"] == config.APIConfig.KEYCLOAK_CLIENT_ID:
                return client
        
        return None      
    
    @classmethod
    def _get_user_account_type(cls, user_id: str) -> str:
        keycloak_admin = get_keycloak_admin()
        roles = keycloak_admin.get_all_roles_of_user(user_id)
        rolenames = [role["name"] for role in roles['clientMappings'][config.APIConfig.KEYCLOAK_CLIENT_ID]["mappings"]]

        if ClientRole.Admin.value in rolenames:
            return AccountTypeEnum.admin
        elif ClientRole.Agronomist.value in rolenames:
            return AccountTypeEnum.agronomist
        else:
            return AccountTypeEnum.standard

    @classmethod   
    def _list_user_organizations(cls, user_id: str) -> list:
        """List all organizations membership for a user"""
        keycloak_openid = KeycloakOpenID(
            server_url=config.APIConfig.KEYCLOAK_ENDPOINT,
            client_id=config.APIConfig.KEYCLOAK_CLIENT_ID,
            client_secret_key=config.APIConfig.KEYCLOAK_CLIENT_SECRET,
            realm_name=config.APIConfig.KEYCLOAK_REALM
        )

        auth_payload = keycloak_openid.token(grant_type=["client_credentials"])
        token = auth_payload["access_token"]

        configuration = phasetwo.Configuration(
            host=f"{config.APIConfig.KEYCLOAK_ENDPOINT}/realms",
            access_token = token
        )

        client = phasetwo.ApiClient(configuration)
        api_client = users_api.UsersApi(client)

        try:
            data = []
            response = api_client.realm_users_user_id_orgs_get(path_params={
                "realm": config.APIConfig.KEYCLOAK_REALM,
                "userId": user_id,
            })
            
            for org in json.loads(response.response.data):
                response = api_client.realm_users_user_id_orgs_org_id_roles_get(path_params={
                    "realm": config.APIConfig.KEYCLOAK_REALM,
                    "userId": user_id,
                    "orgId": org["id"]
                })
                data.append({
                    "id": org["id"],
                    "name": org["name"],
                    "roles": [role["name"] for role in json.loads(response.response.data)]
                })

            return data        
        except phasetwo.ApiException as e:
            print("Exception when calling UsersApi->Roles: %s\n" % e)
            return []
        
    @classmethod
    def assign_role(cls, user_id: str, rolename: ClientRole) -> str:
        keycloak_admin = get_keycloak_admin()
        client = cls._get_client()
        client_id = client["id"]
        role = keycloak_admin.get_client_role(client_id, rolename.value)
        response = keycloak_admin.assign_client_role(
            user_id=user_id,
            client_id=client_id,
            roles=[role]
        )
        print(f"Role {rolename.value} assigned to user {user_id}: {response}")
        
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
                for user in users:
                    user.update({
                        "accountType": self._get_user_account_type(user["id"]),
                        "organizations": self._list_user_organizations(user["id"])
                    })
                    data.append(self._serialize(user))

        return data
    
    @catch_api_exception
    def get(self, token_info):
        """get User
        :rtype: User
        """
        keycloak_admin = get_keycloak_admin()
        user = keycloak_admin.get_user(token_info["sub"])
        user.update({
            "accountType": self._get_user_account_type(token_info["sub"]),
            "organizations": self._list_user_organizations(token_info["sub"])
        })

        return self._serialize(user)

    def get_by_id(self, user_id: str):
        """Get User by ID
        :param user_id: Keycloak user ID
        :rtype: User
        """
        keycloak_admin = get_keycloak_admin()
        user = keycloak_admin.get_user(user_id)
        user.update({
            "accountType": self._get_user_account_type(user_id),
            "organizations": self._list_user_organizations(user_id)
        })

        return self._serialize(user)
    
    @catch_api_exception
    def create(self, payload: UserCreatePayload):
        """create User
        :rtype: User
        """
        keycloak_admin = get_keycloak_admin()
        data = payload.model_dump()
        data.pop("accountType")
        data.pop("phone")
        data.pop("organization")
        piva = data.pop("piva")
        piva = piva if piva is not None else ""
        data.update({
            "username": payload.email,
            "enabled": True,
            "emailVerified": True,
            "groups": ["tornatura"],
            "attributes": {
                "phone": [payload.phone],
                "piva": [piva],
                "avatar": [""]
            }
        })
        user_id = keycloak_admin.create_user(data, True)

        length = 10
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        keycloak_admin.set_user_password(user_id, random_string, temporary=True)
        
        if AccountTypeEnum.agronomist == payload.accountType:
            rolename =  ClientRole.Agronomist
        else:
            rolename =  ClientRole.CompanyStandard

        self.assign_role(user_id, rolename)
        user = keycloak_admin.get_user(user_id)
        user.update({
            "accountType": self._get_user_account_type(user_id),
            "organizations": self._list_user_organizations(user_id)
        })

        template = env.get_template('email_registration.html')
        email_body = template.render(realName=user["firstName"], pwd=random_string, link=config.APIConfig.FRONTEND_URL)
        send_email(receiver_email=user["email"], subject="Benvenuto su Tornatura", email_body=email_body)
        
        return self._serialize(user)
    

    @catch_api_exception
    def update(self, token_info, payload: UserUpdatePayload):
        """update User
        :rtype: User
        """
        keycloak_admin = get_keycloak_admin()
        user = keycloak_admin.get_user(token_info["sub"])
        
        if payload.firstName is not None:
            user["firstName"] = payload.firstName
        
        if payload.lastName is not None:
            user["lastName"] = payload.lastName
        
        if payload.phone is not None:
            user["attributes"]["phone"] = [payload.phone]
        
        keycloak_admin.update_user(user_id=token_info["sub"], payload=user)

        return self.get(token_info)
    

    @catch_api_exception
    def update_avatar(self, token_info: dict, avatar: str | None):
        """update User Avatar
        :rtype: User
        """
        keycloak_admin = get_keycloak_admin()
        user = keycloak_admin.get_user(token_info["sub"])
        
        if avatar is not None:
            user["attributes"]["avatar"] = [avatar]
        
        keycloak_admin.update_user(user_id=token_info["sub"], payload=user)
        return self.get(token_info)
    

    @catch_api_exception
    def get_groups(self, user_id: str):
        """List groups
        :rtype: List[str]
        """
        keycloak_admin = get_keycloak_admin()
        groups = keycloak_admin.get_user_groups(user_id)
        return [group.get("name") for group in groups]
        