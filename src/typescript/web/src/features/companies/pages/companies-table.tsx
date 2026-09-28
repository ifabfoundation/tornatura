import React from "react";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesActions, companiesSelectors } from "../state/companies-slice";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { useNavigate } from "react-router-dom";
import Icon from "../../../components/Icon";
import { AdminPagination } from "../../../components/AdminPagination";
import { Organization, OrganizationsApi } from "@tornatura/coreapis";
import { getCoreApiConfiguration } from "../../../services/utils";
import "../../catalog-admin.css";

function escapeCsvValue(value: unknown) {
  const normalizedValue = String(value ?? "");
  return `"${normalizedValue.replace(/"/g, '""')}"`;
}


export function CompanyTable() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const companies = useAppSelector(companiesSelectors.selectAllCompanies);
  const totalCompanies = useAppSelector(companiesSelectors.selectCompaniesTotal);
  const companiesStatus = useAppSelector(companiesSelectors.selectCompaniesStatus);
  const [currentPage, setCurrentPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(25);

  const formatDateTime = (value?: number) => {
    if (!value) {
      return "N/D";
    }

    return new Date(value).toLocaleString("it-IT", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Aziende", subtitle: "Vista amministrazione" }));
  }, [dispatch]);

  React.useEffect(() => {
    dispatch(companiesActions.fetchCompaniesAction({ page: currentPage, limit: pageSize }));
  }, [currentPage, dispatch, pageSize]);

  const options: TableOptions = {
    defaultSortCol: "creationTime",
    defaultSortDir: "desc",
  };

  const columns: TableColumn[] = [
    {
      headerText: "Ragione Sociale",
      id: "name",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Partita Iva",
      id: "piva",
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
      headerText: "Telefono",
      id: "phone",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Data Di Registrazione",
      id: "creationTime",
      sortValueId: "creationTimeRaw",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Statistiche",
      id: "stats",
      type: "button",
      style: "secondary",
      buttonText: "Visualizza",
      onButtonClick: (row) => navigate(`/admin/companies/${row.orgId}/stats`),
    },
  ];

  const data = companies.map((c) => {
    return {
      orgId: c.orgId,
      name: c.name,
      piva: c.piva,
      email: c.contacts?.email ?? "",
      phone: c.contacts?.phone ?? "",
      creationTime: formatDateTime(c.creationTime),
      creationTimeRaw: c.creationTime ?? 0,
    };
  });

  const handleCsvDownload = async () => {
    const apiConfig = await getCoreApiConfiguration();
    const organizationsApi = new OrganizationsApi(apiConfig);
    const firstResponse = await organizationsApi.listOrganization(1, 1000);
    const exportCompanies = [...(firstResponse.data.data as Organization[])];
    const exportPageCount = Math.ceil(firstResponse.data.total / 1000);

    for (let page = 2; page <= exportPageCount; page += 1) {
      const response = await organizationsApi.listOrganization(page, 1000);
      exportCompanies.push(...(response.data.data as Organization[]));
    }

    const exportData = exportCompanies.map((company) => ({
      orgId: company.orgId,
      name: company.name,
      piva: company.piva,
      email: company.contacts?.email ?? "",
      phone: company.contacts?.phone ?? "",
      creationTime: formatDateTime(company.creationTime),
      creationTimeRaw: company.creationTime ?? 0,
    }));
    const csvHeaders = columns
      .filter((column) => column.type === "text")
      .map((column) => ({ id: column.id, headerText: column.headerText }));
    const sortedData = exportData.sort((left, right) => right.creationTimeRaw - left.creationTimeRaw);
    const csvRows = [
      csvHeaders.map((column) => escapeCsvValue(column.headerText)).join(","),
      ...sortedData.map((row) =>
        csvHeaders
          .map((column) =>
            escapeCsvValue((row as Record<string, unknown>)[column.id] ?? ""),
          )
          .join(","),
      ),
    ];
    const csvContent = `\uFEFF${csvRows.join("\n")}`;
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const today = new Date().toISOString().slice(0, 10);

    link.href = url;
    link.download = `aziende-${today}.csv`;
    link.click();

    URL.revokeObjectURL(url);
  };

  return (
    <div className="catalog-page">
      <header className="catalog-page__intro">
        <div>
          <p className="catalog-page__eyebrow">Amministrazione</p>
          <h2>Aziende</h2>
          <p>Consulta le aziende registrate, i contatti e la data di attivazione.</p>
        </div>
        <button
          type="button"
          className="trnt_btn outlined catalog-page__export"
          onClick={handleCsvDownload}
        >
          <Icon iconName="download" color="black" />
          Esporta CSV
        </button>
      </header>
      <section className="catalog-page__table mt-4">
        <div className="catalog-page__table-scroll">
          {companiesStatus === "pending" ? (
            <p className="catalog-form__hint catalog-page__loading">Caricamento aziende…</p>
          ) : (
            <TableCozy columns={columns} data={data} options={options} />
          )}
        </div>
        <AdminPagination
          currentPage={currentPage}
          pageSize={pageSize}
          pageSizeOptions={[25, 50, 100]}
          totalItems={totalCompanies}
          disabled={companiesStatus === "pending"}
          onPageChange={setCurrentPage}
          onPageSizeChange={(size) => {
            setPageSize(size);
            setCurrentPage(1);
          }}
        />
      </section>
    </div>
  );
}
