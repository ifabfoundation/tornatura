import React, { useState } from "react";
import rarr from "../assets/images/rarr.svg";
import _ from "lodash";
import Icon, { IconName } from "./Icon";

interface RowButtonProps {
  text?: string;
  icon?: IconName;
  style?: string;
  callback: () => void;
}

const RowButton: React.FC<RowButtonProps> = ({ text, icon, style, callback }) => {
  const className = `button${style ? ` ${style}` : ""}`;
  return (
    <a className={className} data-type="table" onClick={callback}>
      {icon && <Icon iconName={icon} color="black" />}
      {text}
    </a>
  );
};

export interface TableColumn {
  id: string;
  headerText: string;
  sortable?: boolean;
  sortValueId?: string;
  type: "text" | "button";
  style?: string;
  shrink?: boolean;
  align?: "left" | "center" | "right";
  buttonText?: string;
  buttonIcon?: IconName;
  onButtonClick?: (data: any) => void;
}

export interface TableOptions {
  icon?: string | null;
  defaultSortCol: string;
  defaultSortDir: "asc" | "desc";
  onRowClick?: (rowData: any) => void;
}

export interface TableCozyProps {
  columns: TableColumn[];
  data: any[];
  options: TableOptions;
}

const TableCozy: React.FC<TableCozyProps> = ({ columns, data, options }) => {
  const defaultOptions = {
    icon: null,
    defaultSortCol: columns[0].id,
    defaultSortDir: "asc",
    onRowClick: null,
  };

  options = Object.assign(defaultOptions, options);
  const [sortCol, setSortCol] = useState(options.defaultSortCol);
  const [sortDir, setSortDir] = useState(options.defaultSortDir);

  if (data.length === 0) {
    return <div className="font-m">Nessun dato</div>;
  }

  const hasRowCallback = typeof options.onRowClick === "function" ? true : false;
  const btnCols = columns.filter((col) => col.type === "button");
  let buttonsAreValid = btnCols.length > 0;
  btnCols.forEach((btnCol) => {
    if (btnCol.onButtonClick && typeof btnCol.onButtonClick !== "function") {
      throw `Button in column '${btnCol.id}' is missing a valid onButtonClick function`;
      buttonsAreValid = false;
    }
  });
  const rowsClickable = hasRowCallback && !buttonsAreValid;
  const activeSortColumn = columns.find((col) => col.id === sortCol);
  const sortValueId = activeSortColumn?.sortValueId ?? sortCol;
  const sortedData = _.orderBy(data, [sortValueId], [sortDir]);

  const handleSortClick = (id: string) => {
    if (sortCol !== id) {
      setSortCol(id);
      setSortDir("asc");
    } else {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    }
  };

  return (
    <div className="component-table-cozy">
      <header>
        {columns.map((col) => {
          let className = "cell";
          if (col.sortable) {
            className += " sortable";
          }
          if (col.sortable && col.id === sortCol) {
            className += sortDir === "asc" ? " sorted-asc" : " sorted-desc";
          }
          const callback = col.sortable
            ? () => {
                handleSortClick(col.id);
              }
            : () => {};
          return (
            <div key={col.id} className={className} onClick={callback}>
              <span className={`d-block text-${col.align ?? "left"}`}>{col.headerText}</span>
            </div>
          );
        })}
      </header>
      {sortedData.map((d: any, i: number) => {
        const rowClassName = "data-row" + (rowsClickable ? " clickable" : "");
        const rowCallback = rowsClickable
          ? () => {
              if (options.onRowClick) {
                options.onRowClick(d);
              }
            }
          : () => {};
        return (
          <div key={i} className={rowClassName} onClick={rowCallback}>
            {columns.map((col, j) => {
              if (col.type === "text") {
                const cell = d[col.id];
                return (
                  <div
                    className={`cell${col.shrink ? " shrink" : ""}`}
                    data-style={col.style}
                    key={j}
                  >
                    <div className={`w-100 text-${col.align ?? "left"}`}>{cell}</div>
                  </div>
                );
              } else if (col.type === "button") {
                const buttonCallback = () => {
                  if (col.onButtonClick) {
                    col.onButtonClick(d);
                  }
                };
                return (
                  <div className={`cell${col.shrink ? " shrink" : ""}`} key={j}>
                    <RowButton
                      text={col.buttonText}
                      icon={col.buttonIcon}
                      style={col.style}
                      callback={buttonCallback}
                    />
                  </div>
                );
              }
            })}
            {rowsClickable && (
              <div className="cell arrow" key={"arrow"}>
                <img src={rarr} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default TableCozy;
