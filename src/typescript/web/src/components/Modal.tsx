import { Fragment } from "react";
import x from "../assets/images/x.svg";

export interface ModalProps {
  closeModal: () => void;
  title: string;
  children: React.ReactNode;
}

export function Modal({ closeModal, title, children }: ModalProps) {
  return (
    <Fragment>
      <div className="modal-bg" onClick={closeModal}>
        <div className="mod-scrollable" onClick={stopPropagation}>
          <div className="modal">
            <header>
              <h2>{title}</h2>
              <a className="close" onClick={closeModal}>
                <img src={x} alt="" />
              </a>
            </header>
            <div className="mod-content">{children}</div>
          </div>
        </div>
      </div>
    </Fragment>
  );
}

export function ModalLarge({ closeModal, title, children }: ModalProps) {
  return (
    <Fragment>
      <div className="modal-bg" onClick={closeModal}>
        <div className="mod-scrollable" onClick={stopPropagation}>
          <div className="modal" style={{ width: "90vw", height: "80vh" }}>
            <header>
              <h2>{title}</h2>
              <a className="close" onClick={closeModal}>
                <img src={x} alt="" />
              </a>
            </header>
            <div className="mod-content">{children}</div>
          </div>
        </div>
      </div>
    </Fragment>
  );
}

function stopPropagation(e: any) {
  e.stopPropagation();
}

export default Modal;
