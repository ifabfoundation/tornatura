import React from "react";

type InfopanelProps = {
  isOpen?: boolean; // controlled
  closeInfopanel: () => void;
  title: string;
  children: React.ReactNode;
};

export function Infopanel({ isOpen, closeInfopanel, title, children }: InfopanelProps) {
  return (
    <div id="infopanel" data-open={isOpen ? "true" : "false"}>
      <div className="bg" onClick={closeInfopanel}></div>
      <div className="panel">
        <header>
          <h2>{title}</h2>
          <button className="trnt_btn type-round narrow-x slim-y outlined" onClick={closeInfopanel}>
            Chiudi
          </button>
        </header>
        <div className="contents">{children}</div>
      </div>
    </div>
  );
}
