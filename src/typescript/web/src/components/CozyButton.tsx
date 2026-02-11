import { Fragment } from "react/jsx-runtime";
import Icon, { IconName } from "./Icon";
import React from "react";

interface CozyButtonProps {
  iconName?: IconName;
  content: React.ReactNode;
  btnSize?: "small" | "large";
  onClick?: () => void;
  arrow?: boolean;
  additionalClasses?: string[];
}

export default function CozyButton({
  iconName,
  btnSize,
  content,
  onClick,
  arrow = false,
  additionalClasses = [],
}: CozyButtonProps) {
  // const [isActive, setIsActive] = useState(false);
  const classes = ["cozy-button", arrow ? "" : "unarrowed", ...additionalClasses];
  return (
    <button className={classes.join(" ")} onClick={onClick} data-size={btnSize ? btnSize : "large"}>
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
        <span>{content}</span>
      </div>
    </button>
  );
}
