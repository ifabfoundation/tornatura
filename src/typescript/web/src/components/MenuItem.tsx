import Icon, { IconName, IconState } from "../components/Icon";
import { Link } from "react-router-dom";

interface MenuItemProps {
  icon: IconName;
  text: string;
  state: IconState;
  path: string;
}

function MenuItem({ icon, text, state, path }: MenuItemProps) {
  const className = `menu-item ${state}`;

  return (
    <li className={className}>
      <Icon iconName={icon} state={state} />
      <Link to={path}>
        <span className="text">{text}</span>
      </Link>
    </li>
  );
}

export default MenuItem;
