import React from "react";

interface StepperProps {
  items: string[];
  currentStep: number;
  handleBackClick?: () => void;
}

export const Stepper: React.FC<StepperProps> = ({ items, currentStep, handleBackClick }) => {
  const stepsNum = items.length;

  return (
    <div className="stepper-wrapper">
      {handleBackClick && currentStep > 0 && (
        <button className="stepper-back-button m-0" onClick={handleBackClick}>
          &larr;
        </button>
      )}
      <ol
        className="stepper"
        // data-steps={3}
        style={{ "--steps-num": `${stepsNum}` } as React.CSSProperties}
      >
        {items.map((item, index) => {
          const stepIndex = index;
          const stepNumber = index + 1;
          const isDone = currentStep > stepIndex;
          const isCurrent = currentStep === stepIndex;
          const handleItemClick = () => {
            if (isDone && handleBackClick) {
              handleBackClick();
            }
          };
          return (
            <li
              key={index}
              data-step-num={stepNumber}
              data-done={isDone ? "true" : "false"}
              data-current={isCurrent ? "true" : "false"}
              onClick={handleItemClick}
            >
              <span>{item}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
};
export default Stepper;
