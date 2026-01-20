import { useState } from "react";
import Icon, { IconName } from "../components/Icon";
import { Link } from "react-router-dom";

interface MenuItemFamilyProps {
  famIcon: IconName;
  famText: string;
  famState: string;
  // famIsOpen: boolean;
  famItems: SubmenuItemProps[];
}

interface SubmenuItemProps {
  text: string;
  state: string;
  path: string;
}

function SubmenuItem({ text, state, path }: SubmenuItemProps) {
  const className = `menu-item ${state}`;

  return (
    <li className={className}>
      <Link to={path}>
        <span className="text">{text}</span>
      </Link>
    </li>
  );
}

function MenuItemFamily({ famIcon, famText, famState, famItems }: MenuItemFamilyProps) {
  const [isOpen, setIsOpen] = useState<boolean>(famState == "selected" ? true : false);

  const className = `menu-item-family ${famState}`;
  const color = famState == "selected" ? "yellow" : "white";
  const textClassName = famState == "selected" ? "color-accent" : "color-white";

  return (
    <>
      <li
        className={className}
        data-open={isOpen ? "true" : "false"}
        onClick={() => {
          setIsOpen(!isOpen);
        }}
      >
        <Icon iconName={famIcon} color={color} />
        <span className={`text-container font-w-600 ${textClassName}`}>{famText}</span>
        <span className="arrow-container text-right flex-grow-1">
          <Icon iconName={"darrs"} color={color} />
        </span>
      </li>
      {isOpen && (
        <div className="subitems-wrapper">
          <ul className="menu-items">
            {famItems.map((item, i) => {
              const state = item.state === "selected" ? "selected" : "normal";
              const className = `menu-item ${famState}`;

              return <SubmenuItem key={i} text={item.text} state={state} path={item.path} />;
            })}
          </ul>
        </div>
      )}
    </>
  );
}

export default MenuItemFamily;
