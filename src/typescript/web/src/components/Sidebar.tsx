import { useLocation, useNavigate, useParams } from "react-router-dom";
import React, { useState, Fragment, useRef } from "react";
import MenuItem from "./MenuItem";
import MenuItemFamily from "./MenuItemFamily";
import logo from "../assets/images/logo-full-white-color.svg";
import { IconName } from "./Icon";
import { useAppDispatch, useAppSelector } from "../hooks";
import { SidebarActions, SidebarSelectors } from "../features/sidebar/state/sidebar-slice";
import "./Sidebar.css";
import { companiesSelectors } from "../features/companies/state/companies-slice";
import { fieldsSelectors } from "../features/fields/state/fields-slice";
import Icon from "../components/Icon";

export interface MenuItemEntry {
  id: string;
  icon: IconName;
  text: string;
  path: string;
}

function CompanySelector() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const { companyId } = useParams();
  const companies = useAppSelector(companiesSelectors.selectAllCompanies);
  const ref = useRef<HTMLDivElement>(null);

  const handleCompanyChange = async (id: string) => {
    setOpen(false);
    navigate(`/companies/${id}/fields`, { replace: true });
  };

  const handeleBackClick = async () => {
    navigate(`/companies`, { replace: true });
  };

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <li className="context-selector-v2" data-open={open ? "true" : "false"}>
      <div className="main-area" onClick={() => handleCompanyChange(companyId!)}>
        <div className="circular-icon">
          <Icon iconName={"barn"} color={"white"} />
        </div>
        <div>
          <div className="label">AZIENDA</div>
          <div className="value">
            {companies.find((company) => company.orgId === companyId)?.name}
          </div>
        </div>
      </div>
      <button className="trnt_btn" onClick={() => setOpen(!open)}>
        <Icon iconName={"darrs"} color={"white"} />
      </button>
      <button className="trnt_btn" onClick={handeleBackClick}>
        <Icon iconName={"x"} color={"white"} />
      </button>

      <div ref={ref} className="context-selector-options-list">
        {companies.map((company) => {
          const fields = useAppSelector((state) =>
            fieldsSelectors.selectFieldsByOrgId(state, company.orgId),
          );
          const selected = company.orgId === companyId;
          return (
            <div
              className={`context-selector-option${selected ? " selected" : ""}`}
              key={company.orgId}
              onClick={() => handleCompanyChange(company.orgId)}
            >
              <span className="font-m-600">{company.name}</span>
              <span className={`font-s-label color-grey-4`}>{`${fields.length} camp${
                fields.length === 1 ? "o" : "i"
              }`}</span>
            </div>
          );
        })}
      </div>
    </li>
  );
}

function FieldSelector() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const { fieldId, companyId } = useParams();
  const fields = useAppSelector((state) => fieldsSelectors.selectFieldsByOrgId(state, companyId));
  const ref = useRef<HTMLDivElement>(null);

  const handleFieldChange = async (id: string) => {
    setOpen(false);
    navigate(`/companies/${companyId}/fields/${id}`, { replace: true });
  };

  const handeleBackClick = async () => {
    navigate(`/companies/${companyId}/fields`, { replace: true });
  };

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <li className="context-selector-v2" data-open={open ? "true" : "false"}>
      <div className="main-area" onClick={() => handleFieldChange(fieldId!)}>
        <div className="circular-icon">
          <Icon iconName={"sprout"} color={"white"} />
        </div>
        <div>
          <div className="label">CAMPO</div>
          <div className="value">{fields.find((field) => field.id === fieldId)?.name}</div>
        </div>
      </div>

      <button className="trnt_btn" onClick={() => setOpen(!open)}>
        <Icon iconName={"darrs"} color={"white"} />
      </button>
      <button className="trnt_btn" onClick={handeleBackClick}>
        <Icon iconName={"x"} color={"white"} />
      </button>

      <div ref={ref} className="context-selector-options-list">
        {fields.map((field) => {
          const selected = field.id === fieldId;
          return (
            <div
              className={`context-selector-option${selected ? " selected" : ""}`}
              key={field.id}
              onClick={() => handleFieldChange(field.id)}
            >
              {field.name}
            </div>
          );
        })}
      </div>
    </li>
  );
}

const familyRilevamenti = {
  famIcon: "checklist" as IconName,
  famText: "Rilevamenti",
  famState: "",
  famItems: [
    {
      text: "Peronospora / Foglia",
      state: "",
      path: "/",
    },
    {
      text: "Cimice asiatica / Trappole",
      state: "selected",
      path: "/",
    },
  ],
};
const familyModelli = {
  famIcon: "spark" as IconName,
  famText: "Modelli previsionali",
  famState: "",
  famItems: [
    {
      text: "Peronospora",
      state: "",
      path: "/modelli/peronospora",
    },
    {
      text: "Cimice asiatica",
      state: "selected",
      path: "/modelli/cimice-asiatica",
    },
    {
      text: "Flavescenza dorata",
      state: "",
      path: "/modelli/flavescenza-dorata",
    },
    {
      text: "Diabrotica",
      state: "",
      path: "/modelli/diabrotica",
    },
  ],
};

export default function SideBar() {
  const navigate = useNavigate();
  let location = useLocation();
  let params = useParams();
  const dispatch = useAppDispatch();
  const { menuEntries, menuBottomEntries } = useAppSelector(SidebarSelectors.selectMenuEntries);
  const [currentEntry, setCurrentEntry] = React.useState<string>("companies");
  const mobileOpen = useAppSelector((state) => state.sidebar.mobileOpen);

  React.useEffect(() => {
    let entry;
    for (let item of menuEntries) {
      if (location.pathname === item.path) {
        entry = item.id;
        setCurrentEntry(entry);
        break;
      }
    }

    for (let item of menuBottomEntries) {
      if (location.pathname === item.path) {
        entry = item.id;
        setCurrentEntry(entry);
        break;
      }
    }

    if (mobileOpen) {
      dispatch(SidebarActions.setMenuMobileOpen(false));
    }
  }, [location, menuEntries, menuBottomEntries]);

  return (
    <Fragment>
      <div className={"sidebar" + (mobileOpen ? " open" : "")}>
        <header style={{ zIndex: 5 }}>
          <div className="flex-grow-1 mt-1">
            <img
              src={logo}
              className="logo"
              alt="logo"
              width="135px"
              onClick={() => navigate("/")}
            />
          </div>
          <div className="line-colors" data-loading="false" />
        </header>
        <div className="hamburger-col"></div>
        <div className="level-1">
          <div>
            {params?.companyId && <CompanySelector />}
            {params?.fieldId && <FieldSelector />}
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

              <MenuItemFamily
                famIcon={familyRilevamenti.famIcon}
                famText={familyRilevamenti.famText}
                famState={familyRilevamenti.famState}
                famItems={familyRilevamenti.famItems}
              />

              <MenuItemFamily
                famIcon={familyModelli.famIcon}
                famText={familyModelli.famText}
                famState={familyModelli.famState}
                famItems={familyModelli.famItems}
              />
            </ul>
          </div>

          {/* <MenuItemFamily
            famIcon={testFamily.famIcon}
            famText={testFamily.famText}
            famState={"selected"}
            famItems={testFamily.famItems}
          /> */}

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
