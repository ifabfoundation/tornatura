import { OverlayTrigger, Popover } from "react-bootstrap";

type InfoPopoverProps = {
  title: string;
  text: string;
  /**
   * Se presente, e' il termine stesso a essere cliccabile (es. "PAC" dentro una
   * frase). Senza, si mostra un piccolo bottone "i" da affiancare a un'etichetta.
   */
  label?: string;
  className?: string;
};

/**
 * Definizione che si apre al click e si chiude cliccando altrove. Serve per i
 * termini che agli agricoltori non sono ovvi (layer, raggio, PAC): la spiegazione
 * sta a un tocco di distanza senza occupare spazio nella pagina.
 */
export default function InfoPopover({ title, text, label, className }: InfoPopoverProps) {
  const popover = (
    <Popover className="info-popover">
      <Popover.Header as="h3" className="font-s-600">
        {title}
      </Popover.Header>
      <Popover.Body className="font-s">{text}</Popover.Body>
    </Popover>
  );
  return (
    <OverlayTrigger trigger="click" placement="auto" rootClose overlay={popover}>
      {label ? (
        <button type="button" className={`info-term ${className ?? ""}`}>
          {label}
        </button>
      ) : (
        <button type="button" className={`info-btn ${className ?? ""}`} aria-label={`Che cos'è: ${title}`}>
          i
        </button>
      )}
    </OverlayTrigger>
  );
}
