import Icon, { IconName } from "./Icon";
import React, { useRef, useState, useEffect, ReactNode } from "react";

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
  const contentRef = useRef<HTMLDivElement | null>(null);

  /* ---------------------- PART 6: Height Animation Logic ---------------------- */
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

      {/* ---------------------- PART 8: Animated Container ---------------------- */}
      <div
        ref={contentRef}
        className="accordion-animated"
        style={{
          overflow: "hidden",
          maxHeight: "0px", // initial collapsed state
          transition: "max-height 0.3s ease", // smooth animation
        }}
      >
        <div className="accordion-content">{item.content}</div>

        {/*  
      {isOpen && <div className="accordion-content">{item.content}</div>}
        */}
      </div>
    </div>
  );
};
