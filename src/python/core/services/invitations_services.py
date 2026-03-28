import datetime
import secrets
import os
from typing import List, Optional
from mongoengine import DoesNotExist
from fastapi import HTTPException

from jinja2 import Environment, FileSystemLoader
from core import config
from core.models import InvitationModel
from core.serializers import AccountTypeEnum, Invitation, InvitationCreatePayload, InvitationPublic, StatusResponse
from core.decorators import catch_api_exception
from core.services.organizations_services import OrganizationServices
from core.services.users_services import ClientRole, UserServices
from core.services.organizations_services import OrganizationDefaultRole, OrganizationCustomRole
from core.utils import send_email

env = Environment(loader=FileSystemLoader(os.path.join(config.APIConfig.BASE_DIR, 'templates/')))


class InvitationServices:
    """Service for managing organization invitations"""

    model = InvitationModel
    serializer = Invitation

    def _serialize(self, obj, many=False):
        """Serialize MongoDB document(s) to Pydantic model(s)"""
        organization_services = OrganizationServices()
        def _create_instance(item) -> Invitation:
            organization = None
            if item.orgId:
                try:
                    organization = organization_services.get(item.orgId)
                except DoesNotExist:
                    organization = None
            return self.serializer(
                id=str(item.id),
                email=item.email,
                orgId=item.orgId,
                organization=organization,
                inviterId=item.inviterId,
                role=item.role,
                token=item.token,
                status=item.status,
                expiresAt=item.expiresAt,
                acceptedAt=item.acceptedAt,
                deleted=item.deleted,
                creationTime=item.creationTime,
                lastUpdateTime=item.lastUpdateTime
            )

        if many:
            return [_create_instance(item) for item in obj]
        return _create_instance(obj)

    def _generate_token(self) -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(32)

    def _get_current_timestamp(self) -> int:
        """Get current timestamp in milliseconds"""
        return int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)

    def _get_expiration_timestamp(self, days=7) -> int:
        """Get expiration timestamp (default 7 days)"""
        current = self._get_current_timestamp()
        return current + (days * 24 * 60 * 60 * 1000)

    def _format_date_it(self, value: datetime.datetime) -> str:
        months = [
            "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
            "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
        ]
        return f"{value.day} {months[value.month - 1]} {value.year}"

    @catch_api_exception
    def create(self, org_id: Optional[str], payload: InvitationCreatePayload, token_info: dict):
        """
        Create a new invitation

        Special cases:
        1. Standard: org_id provided, invitee joins that org
        2. Agronomist → New Company Owner: org_id is null, company owner will create org later

        Steps:
        1. Validate organization exists (if org_id provided)
        2. Check for duplicate pending invitation
        3. Generate token
        4. Save invitation
        5. Send email
        """

        inviter_id = token_info["sub"]
        organization_services = OrganizationServices()
        user_services = UserServices()
        inviter = user_services.get(token_info)
        target_email = payload.email.strip().lower()

        if inviter.email and inviter.email.strip().lower() == target_email:
            raise HTTPException(
                status_code=400,
                detail="You cannot invite yourself"
            )

        # Use orgId from payload (can be null for company owner invitations)
        actual_org_id = payload.orgId

        # Special case: Agronomist inviting company owner who doesn't exist yet
        # In this case, orgId can be null
        if payload.role == ClientRole.CompanyOwner.value and payload.orgId is None and inviter.accountType == AccountTypeEnum.agronomist:
            # Agronomist inviting a new company owner - orgId can be null
            org_name = None
            if actual_org_id:
                # If org_id provided, validate it exists
                try:
                    org = organization_services.get(actual_org_id)
                    org_name = org.name
                except DoesNotExist:
                    raise HTTPException(status_code=404, detail="Organization not found")
            else:
                # No org_id - this is fine for company owner invitations
                # Use inviter's name as context
                inviter = user_services.get(token_info)
                org_name = f"{inviter.firstName}'s network"
                actual_org_id = None  # Keep it null
        else:
            # Standard invitation - org_id is required
            if not actual_org_id:
                raise HTTPException(
                    status_code=400,
                    detail="Organization ID is required for this invitation"
                )
            try:
                org = organization_services.get(actual_org_id)
                org_name = org.name
            except DoesNotExist:
                raise HTTPException(status_code=404, detail="Organization not found")

        # Check for duplicate pending invitation
        # For company owner invitations without org, only check email + inviter
        if actual_org_id:
            members = organization_services.list_members(actual_org_id)
            for member in members:
                if member.user.email.lower() == target_email:
                    raise HTTPException(
                        status_code=400,
                        detail="User is already a member of this organization"
                    )
            existing = self.model.objects(
                email=target_email,
                orgId=actual_org_id,
                status="pending",
                deleted=False
            ).first()
        else:
            existing = self.model.objects(
                email=target_email,
                inviterId=inviter_id,
                role=ClientRole.CompanyOwner.value,
                orgId__exists=False,  # Check for null orgId
                status="pending",
                deleted=False
            ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="A pending invitation already exists for this email"
            )

        # Create invitation
        current_time = self._get_current_timestamp()
        invitation = self.model(
            email=target_email,
            orgId=actual_org_id,  # Can be null for company owner invitations
            inviterId=inviter_id,
            role=payload.role,
            token=self._generate_token(),
            status="pending",
            expiresAt=self._get_expiration_timestamp(),
            deleted=False,
            creationTime=current_time,
            lastUpdateTime=current_time
        )
        invitation.save()

        # Send invitation email
        inviter_name = f"{inviter.firstName} {inviter.lastName}"
        self._send_invitation_email(invitation, inviter_name, org_name)

        return self._serialize(invitation)
    
    @catch_api_exception
    def get(self, invitation_id: str, token_info: dict):
        invitation = self.model.objects(id=invitation_id, deleted=False).first()

        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")
        
        return self._serialize(invitation)

    @catch_api_exception
    def validate_token(self, token: str):
        """Validate invitation token and return public invitation details"""
        from core.serializers import InvitationValidateResponse, InvitationPublic

        try:
            invitation = self.model.objects(
                token=token,
                deleted=False
            ).first()

            if not invitation:
                return InvitationValidateResponse(
                    valid=False,
                    error="Invalid invitation token"
                )

            # Check if expired
            current_time = self._get_current_timestamp()
            if invitation.expiresAt < current_time:
                invitation.status = "expired"
                invitation.lastUpdateTime = current_time
                invitation.save()
                return InvitationValidateResponse(
                    valid=False,
                    error="Invitation has expired"
                )

            # Check if not pending
            if invitation.status != "pending":
                return InvitationValidateResponse(
                    valid=False,
                    error=f"Invitation already {invitation.status}"
                )

            # Get organization and inviter details
            organization_services = OrganizationServices()
            user_services = UserServices()

            # Handle null orgId for company owner invitations
            org = None
            if invitation.orgId:
                org = organization_services.get(invitation.orgId)

            inviter = user_services.get_by_id(invitation.inviterId)

            invitation_public = InvitationPublic(
                id=str(invitation.id),
                email=invitation.email,
                role=invitation.role,
                status=invitation.status,
                organization=org,  # Can be None for company owner invitations
                inviter=inviter,
                expiresAt=invitation.expiresAt,
                creationTime=invitation.creationTime
            )

            return InvitationValidateResponse(
                valid=True,
                invitation=invitation_public
            )

        except DoesNotExist:
            return InvitationValidateResponse(
                valid=False,
                error="Invalid invitation token"
            )

    @catch_api_exception
    def accept(self, token: str, user_id: str, token_info: dict, org_id: Optional[str] = None):
        """
        Accept an invitation - add user to organization

        Special case: If invitee is a company owner being invited by an agronomist,
        and they don't have an organization yet, they need to create one first.
        The org_id parameter should be provided after organization creation.
        """

        invitation = self.model.objects(
            token=token,
            status="pending",
            deleted=False
        ).first()

        if not invitation:
            raise HTTPException(status_code=400, detail="Invalid or expired invitation")

        # Verify email matches authenticated user
        user_email = token_info.get("email", "")
        if invitation.email.lower() != user_email.lower():
            raise HTTPException(
                status_code=400,
                detail=f"This invitation is for {invitation.email}. Please sign in with the correct account."
            )

        # Check if expired
        if invitation.expiresAt < self._get_current_timestamp():
            raise HTTPException(status_code=400, detail="Invitation has expired")

        organization_services = OrganizationServices()
        user_services = UserServices()
        
        # Special case: Company owner invited by agronomist
        if invitation.role == ClientRole.CompanyOwner.value and invitation.orgId is None:
            # Check if user has an organization
            user = user_services.get_by_id(user_id)
            user_orgs = user.organizations

            # If no org_id provided and user has no organizations, they need to create one
            if not org_id and len(user_orgs) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Company owner must create an organization before accepting invitation. Please provide org_id parameter after creating your organization."
                )

            # Use provided org_id or user's first organization
            target_org_id = org_id if org_id else user_orgs[0].id

            # Update invitation with the target org_id (for null orgId invitations)
            if not invitation.orgId:
                invitation.orgId = target_org_id

            # Add the inviter (agronomist) to the company owner's organization
            try:
                organization_services.add_member(target_org_id, invitation.inviterId)
                # Give agronomist appropriate permissions
                organization_services.assign_role(target_org_id, invitation.inviterId, OrganizationDefaultRole.ViewMembers)
                organization_services.assign_role(target_org_id, invitation.inviterId, OrganizationDefaultRole.ViewOrganization)
                organization_services.assign_role(target_org_id, invitation.inviterId, OrganizationCustomRole.ViewAgrifields)
                organization_services.assign_role(target_org_id, invitation.inviterId, OrganizationCustomRole.ManageAgrifields)
                organization_services.assign_role(target_org_id, invitation.inviterId, role=OrganizationCustomRole.ManageDataFiles)
                organization_services.assign_role(target_org_id, invitation.inviterId, role=OrganizationDefaultRole.ManageInvitations)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to add agronomist to organization: {str(e)}")

            org = organization_services.get(target_org_id)
            org_name = org.name
        else:
            # Standard case: Add invitee to inviter's organization
            try:
                organization_services.add_member(invitation.orgId, user_id)
                organization_services.assign_role(invitation.orgId, user_id, OrganizationDefaultRole.ViewMembers)
                if invitation.role == ClientRole.Agronomist.value:
                    organization_services.assign_role(invitation.orgId, user_id, OrganizationDefaultRole.ViewOrganization)
                    organization_services.assign_role(invitation.orgId, user_id, OrganizationCustomRole.ViewAgrifields)
                    organization_services.assign_role(invitation.orgId, user_id, OrganizationCustomRole.ManageAgrifields)
                    organization_services.assign_role(invitation.orgId, user_id, OrganizationCustomRole.ManageDataFiles)
                    organization_services.assign_role(invitation.orgId, user_id, OrganizationDefaultRole.ManageInvitations)
                elif invitation.role == ClientRole.CompanyOwner.value:
                    user_services.assign_role(user_id, ClientRole.CompanyOwner)
                    organization_services.assign_role(user_id=user_id, org_id=invitation.orgId, role=OrganizationDefaultRole.ManageOrganization)
                    organization_services.assign_role(user_id=user_id, org_id=invitation.orgId, role=OrganizationDefaultRole.ManageMembers)
                    organization_services.assign_role(user_id=user_id, org_id=invitation.orgId, role=OrganizationCustomRole.ManageAgrifields)
                    organization_services.assign_role(user_id=user_id, org_id=invitation.orgId, role=OrganizationCustomRole.ManageDataFiles)
                    organization_services.assign_role(user_id=user_id, org_id=invitation.orgId, role=OrganizationDefaultRole.ManageInvitations)
                elif invitation.role == ClientRole.CompanyManager.value:
                    user_services.assign_role(user_id, ClientRole.CompanyManager)
                    organization_services.assign_role(user_id=user_id, org_id=invitation.orgId, role=OrganizationDefaultRole.ViewOrganization)
                    organization_services.assign_role(user_id=user_id, org_id=invitation.orgId, role=OrganizationDefaultRole.ManageMembers)
                    organization_services.assign_role(user_id=user_id, org_id=invitation.orgId, role=OrganizationCustomRole.ManageAgrifields)
                    organization_services.assign_role(user_id=user_id, org_id=invitation.orgId, role=OrganizationCustomRole.ManageDataFiles)
                    organization_services.assign_role(user_id=user_id, org_id=invitation.orgId, role=OrganizationDefaultRole.ManageInvitations)
                elif invitation.role == ClientRole.CompanyStandard.value:
                    organization_services.assign_role(invitation.orgId, user_id, OrganizationDefaultRole.ViewOrganization)
                    organization_services.assign_role(invitation.orgId, user_id, OrganizationCustomRole.ViewAgrifields)
                    organization_services.assign_role(invitation.orgId, user_id, OrganizationCustomRole.ManageDetections)
                    organization_services.assign_role(invitation.orgId, user_id, role=OrganizationCustomRole.ManageDataFiles)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to add member: {str(e)}")

            org = organization_services.get(invitation.orgId)
            org_name = org.name

        # Update invitation status
        current_time = self._get_current_timestamp()
        invitation.status = "accepted"
        invitation.acceptedAt = current_time
        invitation.lastUpdateTime = current_time
        invitation.save()

        # Send notification to inviter
        inviter = user_services.get_by_id(invitation.inviterId)
        user = user_services.get_by_id(user_id)
        inviter_name = f"{inviter.firstName} {inviter.lastName}"
        invitee_name = f"{user.firstName} {user.lastName}"

        self._send_accepted_notification(
            invitation,
            invitee_name,
            inviter.email,
            inviter_name,
            org_name
        )

        return StatusResponse(
            status=200,
            message=f"Invitation accepted successfully. You are now connected with {org_name}."
        )

    @catch_api_exception
    def decline(self, token: str):
        """Decline an invitation"""
        invitation = self.model.objects(
            token=token,
            status="pending",
            deleted=False
        ).first()

        if not invitation:
            raise HTTPException(status_code=400, detail="Invalid or expired invitation")

        current_time = self._get_current_timestamp()
        invitation.status = "declined"
        invitation.lastUpdateTime = current_time
        invitation.save()

        return StatusResponse(status=200, message="Invitation declined")

    @catch_api_exception
    def list_by_organization(self, org_id: str, status: Optional[str] = "pending") -> List:
        """List invitations for an organization"""
        query = {"orgId": org_id, "deleted": False}
        if status:
            query["status"] = status

        invitations = self.model.objects(**query).order_by('-creationTime')
        return self._serialize(invitations, many=True)

    @catch_api_exception
    def list_by_email(self, email: str) -> List:
        """List pending invitations for a user email"""
        invitations = self.model.objects(
            email=email,
            status="pending",
            deleted=False
        ).order_by('-creationTime')

        return self._serialize(invitations, many=True)

    @catch_api_exception
    def delete(self, invitation_id: str):
        """Soft delete (revoke) an invitation"""
        invitation = self.model.objects(id=invitation_id, deleted=False).first()

        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")

        current_time = self._get_current_timestamp()
        invitation.deleted = True
        invitation.status = "revoked"
        invitation.lastUpdateTime = current_time
        invitation.save()

        return StatusResponse(status=200, message="Invitation revoked successfully")

    @catch_api_exception
    def resend(self, invitation_id: str):
        """Resend invitation with new token"""
        invitation = self.model.objects(
            id=invitation_id,
            status="pending",
            deleted=False
        ).first()

        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")

        # Generate new token and extend expiration
        current_time = self._get_current_timestamp()
        invitation.token = self._generate_token()
        invitation.expiresAt = self._get_expiration_timestamp()
        invitation.lastUpdateTime = current_time
        invitation.save()

        # Resend email
        user_services = UserServices()
        organization_services = OrganizationServices()
        inviter = user_services.get_by_id(invitation.inviterId)
        inviter_name = f"{inviter.firstName} {inviter.lastName}"

        # Handle null orgId for company owner invitations
        if invitation.orgId:
            org = organization_services.get(invitation.orgId)
            org_name = org.name
        else:
            org_name = f"{inviter.firstName}'s network"

        self._send_invitation_email(invitation, inviter_name, org_name)

        return StatusResponse(status=200, message="Invitation resent successfully")

    def _send_invitation_email(self, invitation, inviter_name: str, org_name: str):
        """Send invitation email using Jinja2 template"""
        template = env.get_template('email_invitation.html')

        expires_at = datetime.datetime.fromtimestamp(
            invitation.expiresAt / 1000,
            tz=datetime.timezone.utc
        )
        expires_date = self._format_date_it(expires_at)

        # Link goes to invitation accept page
        invitation_link = f"{config.APIConfig.FRONTEND_URL}/invitations/accept?token={invitation.token}"

        email_body = template.render(
            inviterName=inviter_name,
            organizationName=org_name,
            role=self._format_invitation_role(invitation.role),
            invitationLink=invitation_link,
            expiresDate=expires_date
        )

        send_email(
            receiver_email=invitation.email,
            subject=f"Invito {org_name}",
            email_body=email_body
        )

    def _send_accepted_notification(self, invitation, invitee_name: str, inviter_email: str, inviter_name: str, org_name: str):
        """Notify inviter that invitation was accepted"""
        template = env.get_template('email_invitation_accepted.html')

        # Handle null orgId (should be updated by accept() method before this is called)
        org_link = f"{config.APIConfig.FRONTEND_URL}/companies/{invitation.orgId}" if invitation.orgId else config.APIConfig.FRONTEND_URL

        email_body = template.render(
            inviterName=inviter_name,
            inviteeName=invitee_name,
            organizationName=org_name,
            role=self._format_invitation_role(invitation.role),
            organizationLink=org_link
        )

        send_email(
            receiver_email=inviter_email,
            subject=f"{invitee_name} ha accettato il tuo invito",
            email_body=email_body
        )

    def _format_invitation_role(self, role: str):
        if role == ClientRole.Agronomist.value:
            return "Agronomo"
        elif role == ClientRole.CompanyManager.value:
            return "Manager"
        elif role == ClientRole.CompanyOwner.value:
            return "Amministratore"
        elif role == ClientRole.CompanyStandard.value:
            return "Collaboratore"
        else:
            return role
