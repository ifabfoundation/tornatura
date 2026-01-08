import React, { Fragment } from "react";
import { useParams } from "react-router-dom";
import { Alert, Container } from "react-bootstrap";
import { OrganizationMember, OrganizationsApi } from "@tornatura/coreapis";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { useAppDispatch } from "../../../hooks";
import { getCoreApiConfiguration } from "../../../services/utils";

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
  const { companyId } = useParams<{ companyId: string }>();
  const [members, setMembers] = React.useState<OrganizationMember[]>([]);
  const [status, setStatus] = React.useState<"idle" | "pending" | "ready" | "error">("idle");
  const [error, setError] = React.useState<string>();

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Membri azienda", subtitle: "Subtitle" }));
  }, []);

  React.useEffect(() => {
    const loadMembers = async () => {
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
        console.log(err)
        setError(err?.response?.data?.detail ?? "Errore durante il caricamento dei membri");
        setStatus("error");
      }
    };

    loadMembers();
  }, [companyId]);

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

  const tableData = members.map((member) => ({
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
            <Alert variant="danger" dismissible>
              {error}
            </Alert>
          )}
          {status !== "error" && (
            <Fragment>
              <TableCozy columns={tableColumns} data={tableData} options={tableOptions} />
            </Fragment>
          )}
        </div>
      </section>
    </Container>
  );
}
