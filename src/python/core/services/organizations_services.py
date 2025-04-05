import datetime
from fastapi import HTTPException, status
from keycloak import KeycloakOpenID
import phasetwo
from phasetwo.apis.tags import organizations_api, organization_roles_api
from phasetwo.model.organization_representation import OrganizationRepresentation
from phasetwo.model.organization_role_representation import OrganizationRoleRepresentation
from core import config
from core.decorators import catch_api_exception
from core.models import OrganizationModel
from core.serializers import Organization, OrganizationCreatePayload, OrganizationUpdatePayload
from core.services.files_services import FileServices


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


def create_keycloak_organization(name: str):
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
    roles = [OrganizationRoleRepresentation(name="manage-agrifields"),
                OrganizationRoleRepresentation(name="view-agrifields"),
                OrganizationRoleRepresentation(name="view-datafiles"),
                OrganizationRoleRepresentation(name="manage-datafiles"),]
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
                description=item.description,
                logo=file_services.get_file_url(item.orgId, item.logo.category, item.logo.name),
                cover=file_services.get_file_url(item.orgId, item.cover.category, item.cover.name),
                creationTime=item.creationTime,
                lastUpdateTime=item.lastUpdateTime
            )
            
        if many:
            return [_create_instance(item) for item in obj]
        return _create_instance(obj)
    
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
        org_id = create_keycloak_organization(payload.name)

        if org_id is None:
             raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Bad Request organization already exists") 

        data.update({
            "orgId": org_id,
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

        organization.description = payload.description
        organization.logo = payload.logo
        organization.cover = payload.cover
        organization.lastUpdateTime = current_time
        organization.save()
    
        return self._serialize(organization)
    
