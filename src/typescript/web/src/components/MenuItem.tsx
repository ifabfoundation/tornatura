import Icon, { IconName } from "../components/Icon";
import { Link } from "react-router-dom";

interface MenuItemProps {
  icon: IconName;
  text: string;
  state: string;
  path?: string;
  onClick?: () => void;
  addClass?: string;
}

function MenuItem({ icon, text, state, path, onClick, addClass }: MenuItemProps) {
  const className = `menu-item ${state} ${addClass || ""}`.trim();
  const color = state === "selected" ? "yellow" : "white";

  return (
    <li className={className} onClick={onClick}>
      <Icon iconName={icon} color={color} />
      {path ? (
        <Link to={path}>
          <span className="text">{text}</span>
        </Link>
      ) : (
        <span className="text color-white">{text}</span>
      )}
    </li>
  );
}

export default MenuItem;
