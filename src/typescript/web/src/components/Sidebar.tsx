import { useLocation } from "react-router-dom";
import React, { Fragment } from "react";
import MenuItem from "./MenuItem";
import logo from "../assets/images/logo-full-white-color.svg";
import { IconName } from "./Icon";
import { useAppSelector } from "../hooks";
import { SidebarSelectors } from "../features/sidebar/state/sidebar-slice";

export interface MenuItemEntry {
  id: string;
  icon: IconName;
  text: string;
  path: string;
}

export default function SideBar() {
  let location = useLocation();
  const { menuEntries, menuBottomEntries } = useAppSelector(SidebarSelectors.selectMenuEntries);
  const [currentEntry, setCurrentEntry] = React.useState<string>("companies");

  React.useEffect(() => {
    let entry;
    for (let item of menuEntries) {
      if (location.pathname.includes(item.path)) {
        entry = item.id;
        setCurrentEntry(item.id);
        break;
      }
    }

    for (let item of menuBottomEntries) {
      if (location.pathname.includes(item.path)) {
        entry = item.id;
        setCurrentEntry(item.id);
        break;
      }
    }
  }, [location, menuEntries, menuBottomEntries]);

  return (
    <Fragment>
      <div className="sidebar">
        <header style={{ zIndex: 5 }}>
          <div className="flex-grow-1 mt-1">
            <img src={logo} className="logo" alt="logo" width="135px" />
          </div>
          <div className="line-colors loading" />
        </header>
        <div className="hamburger-col"></div>
        <div className="level-1">
          <ul className="menu-items">
            {menuEntries.map((item, i) => {
              const state = currentEntry === item.id ? "selected" : "normal";
              return (
                <MenuItem
                  key={i}
                  icon={item.icon}
                  text={item.text}
                  state={state}
                  path={item.path}
                />
              );
            })}
          </ul>
          <ul className="menu-items">
            {menuBottomEntries.map((item, i) => {
              const state = currentEntry === item.id ? "selected" : "normal";
              return (
                <MenuItem
                  key={i}
                  icon={item.icon}
                  text={item.text}
                  state={state}
                  path={item.path}
                />
              );
            })}
          </ul>
        </div>
      </div>
    </Fragment>
  );
}
