import React from "react";
import Modal from "./Modal";

interface ModalConfirmProps {
  handleCancel: () => void;
  title: string;
  content: React.ReactNode;
  action: string;
  actionBtnClass?: string;
  handleConfirm: () => void;
}

export function ModalConfirm({
  handleCancel,
  title,
  content,
  action,
  actionBtnClass,
  handleConfirm,
}: ModalConfirmProps) {
  const className = actionBtnClass ? actionBtnClass : "primary";
  return (
    <Modal closeModal={handleCancel} title={title}>
      <section>
        <div className="font-m">{content}</div>
        <hr />
        <div className="buttons-wrapper text-center">
          <button className="trnt_btn secondary" onClick={handleCancel}>
            Annulla
          </button>
          <button className={`trnt_btn ${className}`} onClick={handleConfirm}>
            {action}
          </button>
        </div>
      </section>
    </Modal>
  );
}
