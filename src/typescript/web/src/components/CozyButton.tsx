import Icon, { IconName } from "./Icon";

interface CozyButtonProps {
  iconName: IconName;
  text: string;
  onClick?: () => void;
}

export default function CozyButton({ iconName, text, onClick }: CozyButtonProps) {
  // const [isActive, setIsActive] = useState(false);
  return (
    <button className="cozy-button" onClick={onClick}>
      <div className="btn-content">
        <span className="icon-normal">
          <Icon iconName={iconName} color={"black"} />
        </span>
        <span className="icon-active">
          <Icon iconName={iconName} color={"yellow"} />
        </span>
        <span>{text}</span>
      </div>
    </button>
  );
}
