import { Card, Col, Container, ListGroup, Row } from "react-bootstrap";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import React from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Point } from "@tornatura/coreapis";


export function CompaniesList() {
  const dispatch = useAppDispatch();
  const companies = useAppSelector(companiesSelectors.selectAllCompanies);
  const [position, setPosition] = React.useState<Point>();

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({title: "Aziende", subtitle: "Subtitle"}));
  }, []); 

  React.useEffect(() => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition((position) => {
        setPosition({lng: position.coords.longitude, lat: position.coords.latitude});
      });
    } else {
      
    }    
  }, []); 

  return (
    <div>
      <h1>La tua posizione corrente</h1>
      <div>
        Lng: {position?.lng} Lat: {position?.lat}
      </div>
      <h1>Lista Aziende</h1>
      <Container>
        <Row>
          {companies.map((company, index) => {
            return (
              <Col sm={3} key={index}>
                <Card>
                  <Card.Header>{company.name}</Card.Header>
                  <Card.Img variant="top" src={company.cover} />
                  <Card.Body>
                    <Card.Text>
                      {company.description}
                    </Card.Text>
                  </Card.Body>
                </Card>
              </Col>
            );
          })}
        </Row>
      </Container>
      <h1>Lista Campi modello</h1>
      <Container>
        <Row>
          {companies.map((company, index) => {
            return (
              <Col sm={3} key={index}>
                <Card>
                  <Card.Header>{company.name}</Card.Header>
                  <Card.Img variant="top" src={company.cover} />
                  <Card.Body>
                    <Card.Text>
                      {company.description}
                    </Card.Text>
                  </Card.Body>
                  <ListGroup variant="flush">
                    <ListGroup.Item>22 rilevamenti</ListGroup.Item>
                    <ListGroup.Item>Barbabietola</ListGroup.Item>
                  </ListGroup>
                </Card>
              </Col>
            );
          })}
        </Row>
      </Container>
      <div className="mb-3"></div>
        <form autoComplete="off">
          <div className="input-row">
            <label>
              Nome
              <input
                id="name"
                name="name"
                type="text"
                placeholder="Name"
              />
            </label>
            <div className="error">Nome richiesto</div>
          </div>
          <div className="input-row">
            <label>
              Type
              <select
                id="typeId"
                name="typeId"
              >
                <option  value=''>Choose a type</option>
                <option  value='pippo'>Pippo</option>
                <option  value='pluto'>Pluto</option>
              </select>
            </label>
          </div>
          <div className="input-row">
            <label>
              Description
              <textarea
                id="description"
                name="description"
                placeholder=""
                rows={15}
                cols={50}
              >
              </textarea>
            </label>
          </div>
          <hr />
          <div className="buttons-wrapper">
            <button className="secondary" onClick={() => {}}>Cancel</button>
            <input type="submit" className="primary" value="Create" />
          </div>
        </form>
    </div>
  );
}