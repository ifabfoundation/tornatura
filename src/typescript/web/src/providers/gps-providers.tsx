import { Point } from "@tornatura/coreapis";
import React from "react";
import { createContext, PropsWithChildren } from "react";


const initialState: Point = {
  lat: 0.0,
  lng: 0.0,
};

const gpsStore = createContext(initialState);

const CurrentPositionProvider = (props: PropsWithChildren) => {
  const { children } = props;
  const [currentPosition, setCurrentPosition] = React.useState<Point>(initialState);

  function success(pos: GeolocationPosition ) {
    const crd = pos.coords;
    setCurrentPosition({lat: crd.latitude, lng: crd.longitude});
  }
  
  function error(err: GeolocationPositionError) {
    console.error(`ERROR(${err.code}): ${err.message}`);
  }
  
  const options: any = {
    enableHighAccuracy: false,
    maximumAge: 3600000 * 24,
  };

  React.useEffect(() => {
    navigator.permissions.query({ name: 'geolocation' }).then((result) => {
      if (result.state === 'granted') {
        // Permission already granted — proceed with geolocation
        navigator.geolocation.getCurrentPosition(success);
      } else if (result.state === 'prompt') {
        // Permission not yet granted — request it by calling geolocation API
        navigator.geolocation.getCurrentPosition(success, error);
      } else if (result.state === 'denied') {
        // Permission denied — inform the user and offer a way to change settings
        console.log('Geolocation access denied. Please enable it in browser settings.');
      }
      // Listen for changes in permission state
      result.addEventListener('change', () => {
        console.log('Geolocation permission state changed:', result.state);
      });
    });
  }, []);

  React.useEffect(() => {
    const id = navigator.geolocation.watchPosition(success, error, options);
    return () => {
      navigator.geolocation.clearWatch(id);
    }
  }, []);

  return (
    <gpsStore.Provider
      value={currentPosition}
    >
      {children}
    </gpsStore.Provider>
  );
};

export { gpsStore, CurrentPositionProvider };