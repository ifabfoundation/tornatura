import React from "react";
import Modal from "./Modal";

interface ModalConfirmProps {
  handleCancel: () => void;
  title: string;
  content: React.ReactNode;
  action: string;
  handleConfirm: () => void;
}

export function ModalConfirm({
  handleCancel,
  title,
  content,
  action,
  handleConfirm,
}: ModalConfirmProps) {
  return (
    <Modal closeModal={handleCancel} title={title}>
      <section>
        <div>{content}</div>
        <hr />
        <div className="buttons-wrapper">
          <button className="trnt_btn secondary" onClick={handleCancel}>
            Annulla
          </button>
          <button className="trnt_btn primary" onClick={handleConfirm}>
            {action}
          </button>
        </div>
      </section>
    </Modal>
  );
}
