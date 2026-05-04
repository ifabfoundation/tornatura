import React from "react";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { userSelectors } from "../state/user-slice";
import { Container, Row, Col } from "react-bootstrap";


export function UserTable() {
  const dispatch = useAppDispatch();
  const users = useAppSelector(userSelectors.selectAllUsers);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Utenti", subtitle: "Vista amministrazione" }));
  }, []);

  const options: TableOptions = {
    defaultSortCol: "lastName",
    defaultSortDir: "asc",
  };

  const columns: TableColumn[] = [
    {
      headerText: "Nome",
      id: "firstName",
      sortable: true,
      style: "normal",
      type: "text",
    },   {
      headerText: "Cognome",
      id: "lastName",
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
    }
  ];

  return (
    <div>
      <section className="soft pb-3">
        <div className="">
          <Container fluid className="px-0">
            <Row>
              <Col xl={12} className="mt-0" style={{ overflowX: "auto" }}>
                <TableCozy columns={columns} data={users} options={options} />
              </Col>
            </Row>
          </Container>
        </div>
      </section>
    </div>
  );
}
