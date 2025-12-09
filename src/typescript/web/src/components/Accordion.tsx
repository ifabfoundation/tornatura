import Icon, { IconName } from "./Icon";
import React, { useState, ReactNode } from "react";

export interface AccordionItem {
  id: string;
  title: string;
  content: ReactNode;
  icon: IconName;
}

interface AccordionProps {
  items: AccordionItem[];
}

export const Accordion: React.FC<AccordionProps> = ({ items }) => {
  const [openItemId, setOpenItemId] = useState<string | null>(null);

  const toggleItem = (id: string) => {
    setOpenItemId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="accordion">
      {items.map((item) => (
        <AccordionSection
          key={item.id}
          item={item}
          isOpen={openItemId === item.id}
          onToggle={() => toggleItem(item.id)}
        />
      ))}
    </div>
  );
};

interface SectionProps {
  item: AccordionItem;
  isOpen: boolean;
  onToggle: () => void;
}

const AccordionSection: React.FC<SectionProps> = ({ item, isOpen, onToggle }) => {
  return (
    <div className="accordion-section" data-open={isOpen === true ? "true" : "false"}>
      <button className="accordion-header" onClick={onToggle}>
        <span className="accordion-header-left">
          {item.icon && <Icon iconName={item.icon} color={"black"} />}
          {item.icon && <span>&nbsp;</span>}
          <span className="accordion-title">{item.title}</span>
        </span>
        <span className={`accordion-arrow ${isOpen ? "open" : ""}`}></span>
      </button>

      {isOpen && <div className="accordion-content">{item.content}</div>}
    </div>
  );
};
