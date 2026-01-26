import { useRef, useEffect, useState } from "react";
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
  const contentRef = useRef<HTMLDivElement | null>(null);
  const hasSelectecChild = famItems.some((item) => item.state === "selected");
  const isOpenInitial = famState == "selected" || hasSelectecChild ? true : false;
  const [isOpen, setIsOpen] = useState<boolean>(isOpenInitial);

  useEffect(() => {
    if (contentRef.current) {
      if (isOpen) {
        // expand to content height
        contentRef.current.style.maxHeight = contentRef.current.scrollHeight + "px";
      } else {
        // collapse to zero height
        contentRef.current.style.maxHeight = "0px";
      }
    }
  }, [isOpen]);

  const className = `menu-item-family ${famState}`;
  const color = "white";
  const textClassName = "color-white";
  // const color = famState == "selected" ? "yellow" : "white";
  // const textClassName = famState == "selected" ? "color-accent" : "color-white";

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
      <div className="subitems-wrapper" data-open={isOpen ? "true" : "false"} ref={contentRef}>
        <ul className="menu-items">
          {famItems.map((item, i) => {
            const state = item.state === "selected" ? "selected" : "normal";
            return <SubmenuItem key={i} text={item.text} state={state} path={item.path} />;
          })}
        </ul>
      </div>
    </>
  );
}

export default MenuItemFamily;
