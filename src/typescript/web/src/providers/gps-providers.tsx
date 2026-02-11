import { Point } from "@tornatura/coreapis";
import React from "react";
import { createContext, PropsWithChildren } from "react";
import { isMobileDevice } from "../helpers/common";


const initialState: Point = {
  lat: 0.0,
  lng: 0.0,
};

const gpsStore = createContext(initialState);

const CurrentPositionProvider = (props: PropsWithChildren) => {
  const { children } = props;
  const [currentPosition, setCurrentPosition] = React.useState<Point>(initialState);
  const [options, setOptions] = React.useState({})

  function success(pos: GeolocationPosition ) {
    const crd = pos.coords;
    setCurrentPosition({lat: crd.latitude, lng: crd.longitude});
  }
  
  function error(err: GeolocationPositionError) {
    console.error(`ERROR(${err.code}): ${err.message}`);
  }

  React.useEffect(() => {
    if (isMobileDevice()) {
      setOptions({
        enableHighAccuracy: true, 
        maximumAge: 0, 
        timeout: 10000 
      });
    } else {
      setOptions({
        enableHighAccuracy: false, 
        maximumAge: 3600000 * 24
      })
    }
  }, []);

  React.useEffect(() => {
    const id = navigator.geolocation.watchPosition(success, error, options);
    return () => {
      navigator.geolocation.clearWatch(id);
    }
  }, [options]);

  return (
    <gpsStore.Provider
      value={currentPosition}
    >
      {children}
    </gpsStore.Provider>
  );
};

export { gpsStore, CurrentPositionProvider };