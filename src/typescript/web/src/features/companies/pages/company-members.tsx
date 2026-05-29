import React, { Fragment } from "react";
import { useParams } from "react-router-dom";
import { Alert, Container } from "react-bootstrap";
import { AccountTypeEnum, OrganizationMember, OrganizationsApi } from "@tornatura/coreapis";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { ModalConfirm } from "../../../components/ModalConfirm";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { getCoreApiConfiguration } from "../../../services/utils";
import { userSelectors } from "../../users/state/user-slice";

const MANAGE_MEMBERS_ROLE = "manage-members";
const MANAGE_INVITATIONS_ROLE = "manage-invitations";
const MANAGE_ORGANIZATION_ROLE = "manage-organization";
const COMPANY_OWNER_ROLE = "company-owner";
const COMPANY_MANAGER_ROLE = "company-manager";

const translateRole = (role: string) => {
  switch (role) {
    case "company-owner":
      return "Proprietario azienda";
    case "company-manager":
      return "Manager azienda";
    case "company-standard":
      return "Collaboratore";
    case "agronomist":
      return "Agronomo";
    default:
      return role;
  }
};

export function CompanyMembers() {
  const dispatch = useAppDispatch();
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);
  const { companyId } = useParams<{ companyId: string }>();
  const [members, setMembers] = React.useState<OrganizationMember[]>([]);
  const [status, setStatus] = React.useState<"idle" | "pending" | "ready" | "error">("idle");
  const [error, setError] = React.useState<string>();
  const [successMessage, setSuccessMessage] = React.useState<string>();
  const [selectedMember, setSelectedMember] = React.useState<OrganizationMember>();
  const [showRemoveModal, setShowRemoveModal] = React.useState(false);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Membri azienda", subtitle: "Subtitle" }));
  }, [dispatch]);

  const canManageMembers =
    currentUser.accountType === AccountTypeEnum.Admin ||
    (currentUser.organizations ?? []).some(
      (organization) =>
        organization.id === companyId &&
        (organization.roles.includes(MANAGE_MEMBERS_ROLE) ||
          (currentUser.accountType === AccountTypeEnum.Agronomist &&
            organization.roles.includes(MANAGE_INVITATIONS_ROLE))),
    );

  const loadMembers = React.useCallback(async () => {
    if (!companyId) {
      return;
    }
    setStatus("pending");
    setError(undefined);
    try {
      const apiConfig = await getCoreApiConfiguration();
      const organizationsApi = new OrganizationsApi(apiConfig);
      const response = await organizationsApi.listOrganizationMembers(companyId);
      setMembers(response.data);
      setStatus("ready");
    } catch (err: any) {
      console.log(err);
      setError(err?.response?.data?.detail ?? "Errore durante il caricamento dei membri");
      setStatus("error");
    }
  }, [companyId]);

  React.useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  const currentOrganizationMembership = React.useMemo(
    () => (currentUser.organizations ?? []).find((organization) => organization.id === companyId),
    [companyId, currentUser.organizations],
  );

  const currentMemberRole = React.useMemo(() => {
    if (currentUser.accountType === AccountTypeEnum.Admin) {
      return "admin";
    }
    if (currentUser.accountType === AccountTypeEnum.Agronomist) {
      return "agronomist";
    }
    const roles = currentOrganizationMembership?.roles ?? [];
    if (roles.includes(MANAGE_ORGANIZATION_ROLE)) {
      return COMPANY_OWNER_ROLE;
    }
    if (roles.includes(MANAGE_MEMBERS_ROLE)) {
      return COMPANY_MANAGER_ROLE;
    }
    return "company-standard";
  }, [currentOrganizationMembership?.roles, currentUser.accountType]);

  const canRemoveMember = React.useCallback(
    (member: OrganizationMember) => {
      if (!canManageMembers) {
        return false;
      }
      if (member.user.id === currentUser.id) {
        return false;
      }
      if (currentUser.accountType === AccountTypeEnum.Admin) {
        return true;
      }
      if (currentUser.accountType === AccountTypeEnum.Agronomist) {
        return member.role !== COMPANY_OWNER_ROLE && member.role !== COMPANY_MANAGER_ROLE;
      }
      if (currentMemberRole === COMPANY_MANAGER_ROLE) {
        return member.role !== COMPANY_OWNER_ROLE;
      }
      return true;
    },
    [canManageMembers, currentMemberRole, currentUser.accountType, currentUser.id],
  );

  const handleRemoveClick = (row: { member?: OrganizationMember }) => {
    if (!row.member || !canRemoveMember(row.member)) {
      return;
    }
    setSelectedMember(row.member);
    setShowRemoveModal(true);
  };

  const handleRemoveConfirm = async () => {
    if (!companyId || !selectedMember) {
      return;
    }

    try {
      const apiConfig = await getCoreApiConfiguration();
      const organizationsApi = new OrganizationsApi(apiConfig);
      const response = await organizationsApi.removeOrganizationMember(
        companyId,
        selectedMember.user.id,
      );
      setMembers((currentMembers) =>
        currentMembers.filter((member) => member.user.id !== selectedMember.user.id),
      );
      setSuccessMessage(response.data.message);
      setError(undefined);
    } catch (err: any) {
      console.log(err);
      setError(err?.response?.data?.detail ?? "Errore durante la rimozione del membro");
    } finally {
      setShowRemoveModal(false);
      setSelectedMember(undefined);
    }
  };

  const tableOptions: TableOptions = {
    defaultSortCol: "fullName",
    defaultSortDir: "asc",
  };

  const tableColumns: TableColumn[] = [
    {
      headerText: "Nome",
      id: "fullName",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Email",
      id: "email",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Ruolo",
      id: "role",
      sortable: true,
      style: "normal",
      type: "text",
    },
  ];

  if (canManageMembers) {
    tableColumns.push({
      headerText: "",
      id: "action1",
      type: "button",
      style: "normal",
      shrink: true,
      buttonIcon: "bin",
      onButtonClick: handleRemoveClick,
      buttonVisible: (row) => canRemoveMember(row.member),
    });
  }

  const tableData = members.map((member) => ({
    member,
    fullName: `${member.user.firstName} ${member.user.lastName}`.trim(),
    email: member.user.email,
    role: translateRole(member.role),
  }));

  if (status === "pending") {
    return (
      <Container>
        <div className="loading">Caricamento membri...</div>
      </Container>
    );
  }

  return (
    <Container>
      <section className="my-5">
        <div className="text-center">
          <h3 className="mb-4">Lista membri dell'azienda</h3>
          <p>Qui puoi vedere i membri assegnati a questa azienda.</p>
          <div className="my-4"></div>
          {error && (
            <Alert variant="danger" dismissible onClose={() => setError(undefined)}>
              {error}
            </Alert>
          )}
          {successMessage && (
            <Alert variant="success" dismissible onClose={() => setSuccessMessage(undefined)}>
              {successMessage}
            </Alert>
          )}
          {status !== "error" && (
            <Fragment>
              <TableCozy columns={tableColumns} data={tableData} options={tableOptions} />
            </Fragment>
          )}
        </div>
      </section>
      {showRemoveModal && selectedMember && (
        <ModalConfirm
          title="Rimozione membro"
          content={`Sei sicuro di voler rimuovere ${`${selectedMember.user.firstName} ${selectedMember.user.lastName}`.trim()} dall'azienda?`}
          action="Rimuovi"
          actionBtnClass="danger"
          handleCancel={() => {
            setShowRemoveModal(false);
            setSelectedMember(undefined);
          }}
          handleConfirm={handleRemoveConfirm}
        />
      )}
    </Container>
  );
}
