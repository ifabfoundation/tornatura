import { useDispatch, useSelector } from "react-redux";
import { AppDispatch, RootState } from "./store";

import { useLocation } from "react-router-dom";
import React from "react";
import ReactGA from "react-ga4";

export const useAppSelector = useSelector.withTypes<RootState>();
export const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export interface AuxState {
  status: "idle" | "pending" | "succeeded" | "failed";
  total: number;
  error: any;
  currentRequestId: string;
}



export function usePageTracking() {
  const location = useLocation();

  React.useEffect(() => {
    ReactGA.send({
      hitType: "pageview",
      page: location.pathname + location.search,
    });
  }, [location]);
}