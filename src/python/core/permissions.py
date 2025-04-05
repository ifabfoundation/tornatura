# encoding: utf-8
from fastapi import Request, logger
from core import config


class BasePermission:
    """
    A base class from which all permission classes should inherit.
    """

    @classmethod
    def has_permission(cls, token_info):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True
    
    @classmethod
    def has_object_permission(cls, token_info, obj):
        """
        Return `True` if permission is granted for this specific object, `False` otherwise.
        """
        return True


class IsAuthenticated(BasePermission):
    """
    Permission class that allows access to authenticated users.
    """
    @classmethod
    def has_permission(cls, token_info):
        # If we have token_info, the user is authenticated
        return token_info is not None


class IsAdmin(BasePermission):
    """
    Permission for Admins
    """
    @classmethod
    def has_permission(cls, token_info):
        try:
            if "admin" in token_info["resource_access"][config.APIConfig.KEYCLOAK_CLIENT_ID]["roles"]:
                return True
            else:
                return False
        except Exception as ex:
            return False

class IsAgronomist(BasePermission):
    """
    Permission for Agronomists
    """
    @classmethod
    def has_permission(cls, token_info):
        try:
            if "agronomist" in token_info["resource_access"][config.APIConfig.KEYCLOAK_CLIENT_ID]["roles"]:
                return True
            else:
                return False
        except Exception as ex:
            return False

class CanViewOrganization(BasePermission):
    """
    Permission to view an organization's details
    """
    @classmethod
    def has_object_permission(cls, token_info, organization):
        try:
            if IsAdmin.has_permission(token_info):
                return True

            org_id = organization.orgId if hasattr(organization, 'orgId') else organization
            
            if "organizations" not in token_info:
                return False
            
            if org_id not in token_info["organizations"]:
                return False
                
            roles = token_info["organizations"][org_id]["roles"]
            return "view-organization" in roles or "manage-organization" in roles
            
        except Exception as ex:
            logger.logger.error(f"Error checking view organization permission: {ex}")
            return False


class CanManageOrganization(BasePermission):
    """
    Permission to manage an organization
    """
    @classmethod
    def has_object_permission(cls, token_info, organization):
        try:
            if IsAdmin.has_permission(token_info):
                return True
             
            org_id = organization.orgId if hasattr(organization, 'orgId') else organization
            
            if "organizations" not in token_info:
                return False
                
            if org_id not in token_info["organizations"]:
                return False
                
            roles = token_info["organizations"][org_id]["roles"]
            return "manage-organization" in roles
            
        except Exception as ex:
            logger.logger.error(f"Error checking manage organization permission: {ex}")
            return False
        

class CanViewOrganizationAgrifields(BasePermission):
    """
    Permission to view an organization's agrifields
    """
    @classmethod
    def has_object_permission(cls, token_info, organization):
        try:
            if IsAdmin.has_permission(token_info):
                return True
             
            org_id = organization.orgId if hasattr(organization, 'orgId') else organization
            
            if "organizations" not in token_info:
                return False
            
            if org_id not in token_info["organizations"]:
                return False
                
            roles = token_info["organizations"][org_id]["roles"]
            return "view-agrifields" in roles or "manage-agrifields" in roles
            
        except Exception as ex:
            logger.logger.error(f"Error checking view organization's agrifields permission: {ex}")
            return False

class CanManageOrganizationAgrifields(BasePermission):
    """
    Permission to view an organization's agrifields
    """
    @classmethod
    def has_object_permission(cls, token_info, organization):
        try:
            if IsAdmin.has_permission(token_info):
                return True
             
            org_id = organization.orgId if hasattr(organization, 'orgId') else organization
            
            if "organizations" not in token_info:
                return False
            
            if org_id not in token_info["organizations"]:
                return False
                
            roles = token_info["organizations"][org_id]["roles"]
            return "manage-agrifields" in roles
            
        except Exception as ex:
            logger.logger.error(f"Error checking manage organization's agrifields permission: {ex}")
            return False
