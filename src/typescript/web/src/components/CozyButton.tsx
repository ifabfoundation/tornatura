import { Fragment } from "react/jsx-runtime";
import Icon, { IconName } from "./Icon";

interface CozyButtonProps {
  iconName?: IconName;
  text: string;
  btnSize?: "small" | "large";
  onClick?: () => void;
}

export default function CozyButton({ iconName, btnSize, text, onClick }: CozyButtonProps) {
  // const [isActive, setIsActive] = useState(false);
  return (
    <button className="cozy-button" onClick={onClick} data-size={btnSize ? btnSize : "large"}>
      <div className="btn-content">
        {iconName && (
          <Fragment>
            <span className="icon-normal">
              <Icon iconName={iconName} color={"black"} />
            </span>
            <span className="icon-active">
              <Icon iconName={iconName} color={"yellow"} />
            </span>
          </Fragment>
        )}
        <span>{text}</span>
      </div>
    </button>
  );
}
