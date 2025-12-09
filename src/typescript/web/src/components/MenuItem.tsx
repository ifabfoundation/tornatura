import Icon, { IconName } from "../components/Icon";
import { Link } from "react-router-dom";

interface MenuItemProps {
  icon: IconName;
  text: string;
  state: string;
  path: string;
}

function MenuItem({ icon, text, state, path }: MenuItemProps) {
  const className = `menu-item ${state}`;
  const color = state === "selected" ? "yellow" : "white";

  return (
    <li className={className}>
      <Icon iconName={icon} color={color} />
      <Link to={path}>
        <span className="text">{text}</span>
      </Link>
    </li>
  );
}

export default MenuItem;
