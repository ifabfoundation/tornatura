import React from "react";

interface StepperProps {
  items: string[];
  currentStep: number;
  handleBackClick?: () => void;
  handleStepClick?: (stepIndex: number) => void;
  handleExitClick?: () => void;
  itemRecaps?: string[];
}

export const Stepper: React.FC<StepperProps> = ({
  items,
  currentStep,
  handleBackClick,
  handleStepClick,
  handleExitClick,
  itemRecaps,
}) => {
  const stepsNum = items.length;
  const hasExitButton = !!handleExitClick;

  return (
    <div className="stepper-container">
      {hasExitButton && (
        <button
          className="trnt_btn primary me-1 me-md-0 ms-md-2 ms-xl-1"
          data-type="round"
          onClick={handleExitClick}
        >
          &times;
        </button>
      )}
      <div className="flex-grow-1">
        <div className="stepper-wrapper">
          {handleBackClick && currentStep > 0 && (
            <button className="stepper-back-button m-0" onClick={handleBackClick}>
              &larr;
            </button>
          )}
          <ol
            className="stepper"
            data-has-recaps={itemRecaps && itemRecaps.length > 0 ? "true" : "false"}
            style={{ "--steps-num": `${stepsNum}` } as React.CSSProperties}
          >
            {items.map((item, index) => {
              const stepIndex = index;
              const stepNumber = index + 1;
              const isDone = currentStep > stepIndex;
              const isCurrent = currentStep === stepIndex;
              const handleItemClick = () => {
                if (isDone && handleStepClick) {
                  // handleBackClick();
                  handleStepClick(stepIndex);
                }
              };
              const itemRecap = itemRecaps && itemRecaps[index] ? itemRecaps[index] : null;
              return (
                <li
                  key={index}
                  data-step-num={stepNumber}
                  data-done={isDone ? "true" : "false"}
                  data-current={isCurrent ? "true" : "false"}
                  onClick={handleItemClick}
                >
                  <div className="text-center">
                    <span>{item}</span>
                    {itemRecap && (
                      <>
                        <br />
                        {/* <span className="font-s-600 opacity-05">{itemRecap}</span> */}
                        <span className="font-s-label opacity-05">{itemRecap}</span>
                      </>
                    )}
                  </div>
                </li>
              );
            })}
          </ol>
        </div>
      </div>
    </div>
  );
};
export default Stepper;
