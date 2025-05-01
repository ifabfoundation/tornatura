import { Button, Stack } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import styled from "styled-components";


const MenuItem = styled(Button)`
  width: 100%;
  text-align: left !important;
  padding: 10px;
  font-size: 1.2em;
`;


export default function SideBar() {
  const navigate = useNavigate();

  const handleMenuItemClick = (path: string) => {
    navigate(path);
  };

  return (
    <Stack gap={2}>
      <div className="p-1 d-grid">
        <MenuItem 
          variant="outline-primary" 
          size='lg'
          onClick={() => handleMenuItemClick('/')}
        >
          Dashboard
        </MenuItem>
      </div>
      <div className="p-1 d-grid">
        <MenuItem 
          variant="outline-primary" 
          size='lg'
          onClick={() => handleMenuItemClick('/companies')}
        >
          Aziende
        </MenuItem>
      </div>
    </Stack>
  );
}