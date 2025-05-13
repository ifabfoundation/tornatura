import { useLocation, useNavigate, useParams } from "react-router-dom";
import React, { Fragment } from "react";
import MenuItem from "./MenuItem";
import logo from "../assets/images/logo-full-white-color.svg";
import { IconName } from "./Icon";
import { useAppSelector } from "../hooks";
import { SidebarSelectors } from "../features/sidebar/state/sidebar-slice";
import larr from "../assets/images/larr.svg";
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
  const { companyId } = useParams();
  const companies = useAppSelector(companiesSelectors.selectAllCompanies);

  const handleCompanyChange = async (id: string) => {
    navigate(`/companies/${id}/fields`, { replace: true });
  };

  const handeleBackClick = async () => {
    navigate(`/companies`, { replace: true });
  };

  return (
    <li className="context-selector">
      <button onClick={handeleBackClick}>
        <Icon iconName={"ifab_x"} state={"normal"} />
      </button>
      <div className="main-area">
        <label data-name="SELEZIONE AZIENDA">
          <select
            id="company"
            name="company"
            value={companyId}
            onChange={(e) => {
              const selectedCompanyId = e.target.value;
              handleCompanyChange(selectedCompanyId);
            }}
          >
            {companies.map((company) => (
              <option key={company.orgId} value={company.orgId}>
                {company.name}
              </option>
            ))}
          </select>
        </label>
      </div>
    </li>
  );
}

function FieldSelector() {
  const navigate = useNavigate();
  const { fieldId, companyId } = useParams();
  const fields = useAppSelector((state) => fieldsSelectors.selectFieldsByOrgId(state, companyId));

  const handleFieldChange = async (id: string) => {
    navigate(`/companies/${companyId}/fields/${id}`, { replace: true });
  };

  const handeleBackClick = async () => {
    navigate(`/companies/${companyId}/fields`, { replace: true });
  };

  return (
    <li className="context-selector">
      <button onClick={handeleBackClick}>
        <Icon iconName={"ifab_x"} state={"normal"} />
      </button>
      <div className="main-area">
        <label data-name="SELEZIONE CAMPO">
          <select
            id="field"
            name="field"
            value={fieldId}
            onChange={(e) => {
              const selectedFieldId = e.target.value;
              handleFieldChange(selectedFieldId);
            }}
          >
            {fields.map((field) => (
              <option key={field.id} value={field.id}>
                {field.name}
              </option>
            ))}
          </select>
        </label>
      </div>
    </li>
  );
}

export default function SideBar() {
  let location = useLocation();
  let params = useParams();
  const { menuEntries, menuBottomEntries } = useAppSelector(SidebarSelectors.selectMenuEntries);
  const [currentEntry, setCurrentEntry] = React.useState<string>("companies");

  React.useEffect(() => {
    let entry;
    for (let item of menuEntries) {
      if (location.pathname.includes(item.path)) {
        entry = item.id;
        setCurrentEntry(entry);
        break;
      }
    }

    for (let item of menuBottomEntries) {
      if (location.pathname.includes(item.path)) {
        entry = item.id;
        setCurrentEntry(entry);
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
          <div className="line-colors" data-loading="false" />
        </header>
        <div className="hamburger-col"></div>
        <div className="level-1" style={{ width: "inrehit", paddingTop: "0" }}>
          <ul className="menu-items">
            {params?.companyId && <CompanySelector />}
            {params?.fieldId && <FieldSelector />}
            <div className="mt-4"></div>
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
