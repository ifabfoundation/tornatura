import { Button } from "react-bootstrap";
import styled from "styled-components";
import { useAppSelector } from "../hooks";
import { userSelectors } from "../features/users/state/user-slice";
import keycloakInstance from "../providers/keycloak";
import { headerbarSelectors } from "../features/headerbar/state/headerbar-slice";


const Row = styled.div`
  display: flex;
  flex-direction: row;
  width: 100%;
  padding: 5px;
  align-items: center;
`;

const Column = styled.div<{ $grow?: number, $order?: number }>`
  flex-grow: ${props => props.$grow ? props.$grow : 1};
  order: ${props => props.$order ? props.$order : 1};
`;

const Branding = styled.div`
  flex-grow: 1;
  max-width: 300px;
`;

const Container = styled.div<{ $direction: string, $justifyContent: string, $alignItems: string }>`
  display: flex;
  width: 100%;
  padding: 5px;
  flex-direction: ${props => props.$direction};
  justify-content: ${props => props.$justifyContent};
  align-items: ${props => props.$alignItems};
`;

const Title = styled.div`
  align-self: flex-start;
`;


export default function TopBar() {
  const currentUser = useAppSelector(userSelectors.selectUser);
  const title = useAppSelector(headerbarSelectors.selectTitle);

  const handleSignOut = () => {
    keycloakInstance.logout()
  }

  return (
    <Row>
      <Branding>
        Tornatura
      </Branding>
      <Column $grow={2}>
        <Container 
          $direction="row" 
          $justifyContent="space-between" 
          $alignItems="center"
        >
          <Column>
            <Title>
              {title}
            </Title>
          </Column>
          <Column $grow={2} style={{alignSelf: "flex-end"}}>
            <Container
              $direction='row'
              $justifyContent='flex-end'
              $alignItems='center'
            >
              {currentUser?.firstName} {currentUser?.lastName}
              <img src="https://ui-avatars.com/api/?name=Avatar&rounded=true" style={{marginLeft: "4px"}}/>
              <Button onClick={handleSignOut}>Logout</Button>
            </Container>
          </Column>
        </Container>
      </Column>
    </Row>
  );
}