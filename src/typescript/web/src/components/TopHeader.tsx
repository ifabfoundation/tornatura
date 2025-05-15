import logo from "../assets/images/logo-full-white-color.svg";

export default function TopBar() {
  return (
    <div className="headerbar dark">
      <div>
        <img src={logo} alt="back" />
      </div>
    </div>
  );
}
