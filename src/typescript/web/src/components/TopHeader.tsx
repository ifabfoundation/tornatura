import logo from "../assets/images/logo-full-white-color.svg";
import { useNavigate } from "react-router-dom";

export default function TopBar() {
  const navigate = useNavigate();
  return (
    <div className="headerbar dark external">
      <div>
        <img src={logo} alt="back" className="logo pointer" onClick={() => navigate("/")} />
      </div>
    </div>
  );
}
