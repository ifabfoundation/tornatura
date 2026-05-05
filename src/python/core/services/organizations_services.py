import datetime
from enum import Enum
import json
import os
from typing import Union
from fastapi import HTTPException, status
from keycloak import KeycloakOpenID
import phasetwo
from phasetwo.apis.tags import organizations_api, organization_roles_api, organization_memberships_api
from phasetwo.model.organization_representation import OrganizationRepresentation
from phasetwo.model.organization_role_representation import OrganizationRoleRepresentation
from urllib import error, request
from core import config
from core.decorators import catch_api_exception
from core.models import OrganizationModel
from core.serializers import Organization, OrganizationCreatePayload, OrganizationUpdatePayload, OrganizationMember, StatusResponse
from core.services.files_services import FileServices
from core.services.users_services import UserServices


class OrganizationDefaultRole(Enum):
    ViewOrganization = "view-organization"
    ManageOrganization = "manage-organization"
    ViewMembers = "view-members"
    ManageMembers = "manage-members"
    ViewInvitions = "view-invitations"
    ManageInvitations = "manage-invitations"

class OrganizationCustomRole(Enum):
    ManageAgrifields = "manage-agrifields"
    ViewAgrifields = "view-agrifields"
    ViewDataFiles = "view-datafiles"
    ManageDataFiles = "manage-datafiles"
    ViewDetections = "view-detections"
    ManageDetections = "manage-detections"


def get_service_access_token():
    # call auth service to create organization
    keycloak_openid = KeycloakOpenID(
        server_url=config.APIConfig.KEYCLOAK_ENDPOINT,
        client_id=config.APIConfig.KEYCLOAK_CLIENT_ID,
        client_secret_key=config.APIConfig.KEYCLOAK_CLIENT_SECRET,
        realm_name=config.APIConfig.KEYCLOAK_REALM
    )

    auth_payload = keycloak_openid.token(grant_type=["client_credentials"])
    return auth_payload["access_token"]


class OrganizationServices:
    serializer = Organization
    model = OrganizationModel

    def _serialize(self, obj, many=False):
        """Serialize object(s) to serializer instances
        
        Args:
            obj: Object or list of objects to serialize
            many: If True, treats obj as a list of objects
            
        Returns:
            Serializer instance or list of serializer instances
        """
        file_services = FileServices()
        def _create_instance(item: OrganizationModel) -> Organization:
            return self.serializer(
                orgId=item.orgId,
                name=item.name,
                piva=item.piva,
                logo=file_services.get_file_url(item.orgId, item.logo.category, item.logo.name),
                cover=file_services.get_file_url(item.orgId, item.cover.category, item.cover.name),
                contacts={
                    "phone": item.contacts.phone,
                    "email": item.contacts.email
                },
                creationTime=item.creationTime,
                lastUpdateTime=item.lastUpdateTime
            )
            
        if many:
            return [_create_instance(item) for item in obj]
        return _create_instance(obj)
    
    
    @classmethod
    def _create_keycloak_organization(cls, name: str):
        token = get_service_access_token()

        configuration = phasetwo.Configuration(
            host=f"{config.APIConfig.KEYCLOAK_ENDPOINT}/realms",
            access_token = token
        )

        client = phasetwo.ApiClient(configuration)

        # Create a new Organization
        orgs_api = organizations_api.OrganizationsApi(client)
        roles_api = organization_roles_api.OrganizationRolesApi(client)
        org = OrganizationRepresentation(name=name, realm=config.APIConfig.KEYCLOAK_REALM)
        roles = [OrganizationRoleRepresentation(name=rolename.value) for rolename in OrganizationCustomRole]
        try:
            response = orgs_api.create_organization(org, path_params={
                "realm": config.APIConfig.KEYCLOAK_REALM
            })
            org_id = response.response.headers["Location"].split('/')[-1]
            for role in roles:
                roles_api.create_organization_role(role, path_params={ 
                    "realm": config.APIConfig.KEYCLOAK_REALM,
                    "orgId": org_id
                })
            return org_id
        except phasetwo.ApiException as e:
            print("Exception when calling OrganizationsApi->create_organization: %s\n" % e)
            return None
    
    @classmethod
    def is_organization_exists(cls, name: str):
        token = get_service_access_token()

        configuration = phasetwo.Configuration(
            host=f"{config.APIConfig.KEYCLOAK_ENDPOINT}/realms",
            access_token = token
        )

        client = phasetwo.ApiClient(configuration)
        orgs_api = organizations_api.OrganizationsApi(client)

        try:
            response = orgs_api.get_organizations(
                path_params={
                "realm": config.APIConfig.KEYCLOAK_REALM
                },
                query_params={
                    "search": name
                }
            )
            organizations = json.loads(response.response.data)
            if len(organizations) > 0:
                return True
            else:
                return False
        except phasetwo.ApiException as e:
            return False
    
    @classmethod
    def assign_role(cls, org_id: str, user_id: str, role: OrganizationDefaultRole | OrganizationCustomRole):
        token = get_service_access_token()

        configuration = phasetwo.Configuration(
            host=f"{config.APIConfig.KEYCLOAK_ENDPOINT}/realms",
            access_token = token
        )

        client = phasetwo.ApiClient(configuration)
        roles_api = organization_roles_api.OrganizationRolesApi(client)

        try:
            roles_api.grant_user_organization_role(
                path_params={
                    "realm": config.APIConfig.KEYCLOAK_REALM,
                    "userId": user_id,
                    "orgId": org_id,
                    "name": role.value
                },
            )
        except phasetwo.ApiException as e:
            print("Exception when calling OrganizationRolesApi->grant_user_organization_role: %s\n" % e)
    
    @classmethod
    def add_member(cls, org_id: str, user_id: str):
        token = get_service_access_token()

        configuration = phasetwo.Configuration(
            host=f"{config.APIConfig.KEYCLOAK_ENDPOINT}/realms",
            access_token = token
        )

        client = phasetwo.ApiClient(configuration)
        memberships_api = organization_memberships_api.OrganizationMembershipsApi(client)

        try:
            memberships_api.add_organization_member(
                path_params={
                    "realm": config.APIConfig.KEYCLOAK_REALM,
                    "userId": user_id,
                    "orgId": org_id,
                },
            )
        except phasetwo.ApiException as e:
            print("Exception when calling OrganizationMembershipsApi->add_organization_member: %s\n" % e)

    @classmethod
    def _get_member_roles(cls, org_id: str, user_id: str) -> list[str]:
        user = UserServices().get_by_id(user_id)
        for membership in user.organizations:
            if membership.id == org_id:
                return membership.roles
        return []

    @classmethod
    def get_member_role(cls, org_id: str, user_id: str) -> str:
        user = UserServices().get_by_id(user_id)
        member_roles = cls._get_member_roles(org_id, user_id)
        return cls._map_member_role(user, member_roles)

    @classmethod
    def _ensure_member_removal_allowed(cls, actor_id: str, org_id: str, user_id: str):
        if actor_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot remove yourself from this organization",
            )

        actor = UserServices().get_by_id(actor_id)
        actor_role = cls.get_member_role(org_id, actor_id)
        target_role = cls.get_member_role(org_id, user_id)

        if actor.accountType == "Agronomist" and target_role in {"company-owner", "company-manager"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agronomists cannot remove company owners or company managers",
            )

        if actor_role == "company-manager" and target_role == "company-owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Company managers cannot remove company owners",
            )

    @classmethod
    def remove_member(cls, actor_id: str, org_id: str, user_id: str):
        cls._ensure_member_removal_allowed(actor_id, org_id, user_id)
        token = get_service_access_token()
        configuration = phasetwo.Configuration(
            host=f"{config.APIConfig.KEYCLOAK_ENDPOINT}/realms",
            access_token = token
        )

        client = phasetwo.ApiClient(configuration)
        memberships_api = organization_memberships_api.OrganizationMembershipsApi(client)

        try:
            memberships_api.remove_organization_member(
                path_params={
                    "realm": config.APIConfig.KEYCLOAK_REALM,
                    "userId": user_id,
                    "orgId": org_id,
                },
            )
            return StatusResponse(status=200, message="User successfully removed")
        except phasetwo.ApiException as e:
            print("Exception when calling OrganizationMembershipsApi->remove_organization_member: %s\n" % e)
            raise HTTPException(status_code=e.status, detail=e.reason)

    @catch_api_exception
    def list(self):
        """List organizations
        :rtype: List[Organization]
        """
        organizations = self.model.objects(deleted=False)
        return self._serialize(organizations, many=True)
    
    @catch_api_exception
    def get(self, org_id: str):
        """get organization
        :rtype: Organization
        """
        organization = self.model.objects(orgId=org_id, deleted=False).first()
        if organization is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        return self._serialize(organization)
    
    @catch_api_exception
    def create(self, payload: OrganizationCreatePayload):
        """Create organization
        :rtype: Organization
        """
        data = payload.model_dump()
        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)
        org_id = self._create_keycloak_organization(payload.name)

        if org_id is None:
             raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Bad Request organization already exists") 

        file_services = FileServices()
        logo = file_services.upload_local_file(org_id, "media", os.path.join(config.APIConfig.BASE_DIR, "media/logo.jpg"))
        cover = file_services.upload_local_file(org_id, "media", os.path.join(config.APIConfig.BASE_DIR, "media/cover.jpg"))

        data.update({
            "orgId": org_id,
            "logo": {
                "name": logo,
                "category": "media"
            },
            "cover": {
                "name": cover,
                "category": "media"
            },
            "creationTime": current_time,
            "lastUpdateTime": current_time
        })
        organization = self.model(**data)
        organization.save()
        return self._serialize(organization)
    
    @catch_api_exception
    def update(self, org_id: str, payload: OrganizationUpdatePayload):
        """Update organization
        :rtype: Organization
        """
        organization = self.model.objects(orgId=org_id, deleted=False).first()
        if organization is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)

        if payload.name is not None:
            organization.name = payload.name
        
        if payload.piva is not None:
            organization.piva = payload.piva
        
        if payload.contacts is not None:
            organization.contacts.email = payload.contacts.email
            organization.contacts.phone = payload.contacts.phone
        
        if payload.cover is not None:
            organization.cover.category = payload.cover.category
            organization.cover.name = payload.cover.name
        
        if payload.logo is not None:
            organization.logo.category = payload.logo.category
            organization.logo.name = payload.logo.name
        
        organization.lastUpdateTime = current_time
        organization.save()
    
        return self._serialize(organization)

    @catch_api_exception
    def list_members(self, org_id: str):
        """List organization members with their roles
        :rtype: List[OrganizationMember]
        """
        token = get_service_access_token()
        configuration = phasetwo.Configuration(
            host=f"{config.APIConfig.KEYCLOAK_ENDPOINT}/realms",
            access_token=token
        )
        client = phasetwo.ApiClient(configuration)
        memberships_api = organization_memberships_api.OrganizationMembershipsApi(client)
        user_services = UserServices()

        response = memberships_api.get_organization_memberships(
            path_params = {
            "realm": config.APIConfig.KEYCLOAK_REALM,
            "orgId": org_id
        })

        if hasattr(response, "response"):
            members_data = json.loads(response.response.data)
        else:
            members_data = response
        members = []

        for member in members_data:
            user_id = member.get("id")
            if not user_id:
                continue
            groups = user_services.get_groups(user_id)
            if "tornatura" in groups:
                user = user_services.get_by_id(user_id)
                member_roles = []
                for membership in user.organizations:
                    if membership.id == org_id:
                        member_roles = membership.roles
                        break
                members.append(
                    OrganizationMember(
                        user=user,
                        role=self._map_member_role(user, member_roles)
                    )
                )
        return members

    @staticmethod
    def _map_member_role(user, member_roles):
        if user.accountType == "Agronomist":
            return "agronomist"
        if OrganizationDefaultRole.ManageOrganization.value in member_roles:
            return "company-owner"
        if OrganizationDefaultRole.ManageMembers.value in member_roles:
            return "company-manager"
        return "company-standard"
    
