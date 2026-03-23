import React from "react";
import mapboxgl, { LngLatLike } from "mapbox-gl";
import MapboxLanguage from "@mapbox/mapbox-gl-language";
import * as turf from "@turf/turf";
import { useParams } from "react-router-dom";
import { Point } from "@tornatura/coreapis";
import { useAppSelector } from "../hooks";
import { fieldsSelectors } from "../features/fields/state/fields-slice";
import { gpsStore } from "../providers/gps-providers";
import * as nuts from "../helpers/nuts.json";


const modelValueToRiskLevel = (value: number): number => {
  if (value > 80) return 4;
  else if (value > 60) return 3;
  else if (value > 40) return 2;
  else if (value > 20) return 1;
  else return 0;
};

const getRiskColor = (riskLevel?: number): string => {
  switch (riskLevel) {
    case 0:
      return "9FDC71"; // Green
    case 1:
      return "FFFF00"; // Yellow
    case 2:
      return "FFA500"; // Orange
    case 3:
      return "FF0000"; // Red
    case 4:
      return "FF0000"; // Red
    default:
      return "CCCCCC"; // Grey for unknown
  }
};

const dataMap = [
  { id: "ITC11", code: "TO", name: "Torino" },
  { id: "ITC12", code: "VC", name: "Vercelli" },
  { id: "ITC13", code: "BI", name: "Biella" },
  { id: "ITC14", code: "VB", name: "Verbano-Cusio-Ossola" },
  { id: "ITC15", code: "NO", name: "Novara" },
  { id: "ITC16", code: "CN", name: "Cuneo" },
  { id: "ITC17", code: "AT", name: "Asti" },
  { id: "ITC18", code: "AL", name: "Alessandria" },
  { id: "ITC20", code: "AO", name: "Valle d’Aosta" },
  { id: "ITC31", code: "IM", name: "Imperia" },
  { id: "ITC32", code: "SV", name: "Savona" },
  { id: "ITC33", code: "GE", name: "Genova" },
  { id: "ITC34", code: "SP", name: "La Spezia" },
  { id: "ITC41", code: "VA", name: "Varese" },
  { id: "ITC42", code: "CO", name: "Como" },
  { id: "ITC43", code: "LC", name: "Lecco" },
  { id: "ITC44", code: "SO", name: "Sondrio" },
  { id: "ITC46", code: "BG", name: "Bergamo" },
  { id: "ITC47", code: "BS", name: "Brescia" },
  { id: "ITC48", code: "PV", name: "Pavia" },
  { id: "ITC49", code: "LO", name: "Lodi" },
  { id: "ITC4A", code: "CR", name: "Cremona" },
  { id: "ITC4B", code: "MN", name: "Mantova" },
  { id: "ITC4C", code: "MI", name: "Milano" },
  { id: "ITC4D", code: "MB", name: "Monza e della Brianza" },
  { id: "ITF11", code: "AQ", name: "L’Aquila" },
  { id: "ITF12", code: "TE", name: "Teramo" },
  { id: "ITF13", code: "PE", name: "Pescara" },
  { id: "ITF14", code: "CH", name: "Chieti" },
  { id: "ITF21", code: "IS", name: "Isernia" },
  { id: "ITF22", code: "CB", name: "Campobasso" },
  { id: "ITF31", code: "CE", name: "Caserta" },
  { id: "ITF32", code: "BN", name: "Benevento" },
  { id: "ITF33", code: "NA", name: "Napoli" },
  { id: "ITF34", code: "AV", name: "Avellino" },
  { id: "ITF35", code: "SA", name: "Salerno" },
  { id: "ITF43", code: "TA", name: "Taranto" },
  { id: "ITF44", code: "BR", name: "Brindisi" },
  { id: "ITF45", code: "LE", name: "Lecce" },
  { id: "ITF46", code: "FG", name: "Foggia" },
  { id: "ITF47", code: "BA", name: "Bari" },
  { id: "ITF48", code: "BT", name: "Barletta-Andria-Trani" },
  { id: "ITF51", code: "PZ", name: "Potenza" },
  { id: "ITF52", code: "MT", name: "Matera" },
  { id: "ITF61", code: "CS", name: "Cosenza" },
  { id: "ITF62", code: "KR", name: "Crotone" },
  { id: "ITF63", code: "CZ", name: "Catanzaro" },
  { id: "ITF64", code: "VV", name: "Vibo Valentia" },
  { id: "ITF65", code: "RC", name: "Reggio Calabria" },
  { id: "ITG11", code: "TP", name: "Trapani" },
  { id: "ITG12", code: "PA", name: "Palermo" },
  { id: "ITG13", code: "ME", name: "Messina" },
  { id: "ITG14", code: "AG", name: "Agrigento" },
  { id: "ITG15", code: "CL", name: "Caltanissetta" },
  { id: "ITG16", code: "EN", name: "Enna" },
  { id: "ITG17", code: "CT", name: "Catania" },
  { id: "ITG18", code: "RG", name: "Ragusa" },
  { id: "ITG19", code: "SR", name: "Siracusa" },
  { id: "ITG2D", code: "SS", name: "Sassari" },
  { id: "ITG2E", code: "NU", name: "Nuoro" },
  { id: "ITG2F", code: "CA", name: "Cagliari" },
  { id: "ITG2G", code: "OR", name: "Oristano" },
  { id: "ITG2H", code: "SU", name: "Sud Sardegna" },
  { id: "ITH10", code: "BZ", name: "Bolzano-Bozen" },
  { id: "ITH20", code: "TN", name: "Trento" },
  { id: "ITH31", code: "VR", name: "Verona" },
  { id: "ITH32", code: "VI", name: "Vicenza" },
  { id: "ITH33", code: "BL", name: "Belluno" },
  { id: "ITH34", code: "TV", name: "Treviso" },
  { id: "ITH35", code: "VE", name: "Venezia" },
  { id: "ITH36", code: "PD", name: "Padova" },
  { id: "ITH37", code: "RO", name: "Rovigo" },
  { id: "ITH41", code: "PN", name: "Pordenone" },
  { id: "ITH42", code: "UD", name: "Udine" },
  { id: "ITH43", code: "GO", name: "Gorizia" },
  { id: "ITH44", code: "TS", name: "Trieste" },
  { id: "ITH51", code: "PC", name: "Piacenza" },
  { id: "ITH52", code: "PR", name: "Parma" },
  { id: "ITH53", code: "RE", name: "Reggio nell’Emilia" },
  { id: "ITH54", code: "MO", name: "Modena" },
  { id: "ITH55", code: "BO", name: "Bologna" },
  { id: "ITH56", code: "FE", name: "Ferrara" },
  { id: "ITH57", code: "RA", name: "Ravenna" },
  { id: "ITH58", code: "FC", name: "Forlì-Cesena" },
  { id: "ITH59", code: "RN", name: "Rimini" },
  { id: "ITI11", code: "MS", name: "Massa-Carrara" },
  { id: "ITI12", code: "LU", name: "Lucca" },
  { id: "ITI13", code: "PT", name: "Pistoia" },
  { id: "ITI14", code: "FI", name: "Firenze" },
  { id: "ITI15", code: "PO", name: "Prato" },
  { id: "ITI16", code: "LI", name: "Livorno" },
  { id: "ITI17", code: "PI", name: "Pisa" },
  { id: "ITI18", code: "AR", name: "Arezzo" },
  { id: "ITI19", code: "SI", name: "Siena" },
  { id: "ITI1A", code: "GR", name: "Grosseto" },
  { id: "ITI21", code: "PG", name: "Perugia" },
  { id: "ITI22", code: "TR", name: "Terni" },
  { id: "ITI31", code: "PU", name: "Pesaro e Urbino" },
  { id: "ITI32", code: "AN", name: "Ancona" },
  { id: "ITI33", code: "MC", name: "Macerata" },
  { id: "ITI34", code: "AP", name: "Ascoli Piceno" },
  { id: "ITI35", code: "FM", name: "Fermo" },
  { id: "ITI41", code: "VT", name: "Viterbo" },
  { id: "ITI42", code: "RI", name: "Rieti" },
  { id: "ITI43", code: "RM", name: "Roma" },
  { id: "ITI44", code: "LT", name: "Latina" },
  { id: "ITI45", code: "FR", name: "Frosinone" },
];

interface MapNUTSDataProps {
  provinceData?: { nuts_3_name: string; value: number }[];
}

export const MapNUTSData = ({ provinceData }: MapNUTSDataProps) => {
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default"),
  );
  const mapContainerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<any>(null);
  const [mapLoaded, setMapLoaded] = React.useState(false);
  const currentPosition = React.useContext(gpsStore);

  console.log("DEBUG NUTS", nuts);

  const getProvinceDS = (inputData?: any[]) => {
    let passedFeatures: any[] = [];
    // @ts-ignore
    nuts.features.forEach((f: any) => {
      const id = f.properties.NUTS_ID;
      const nuts_3_name = f.properties.NUTS_NAME;
      const level = f.properties.LEVL_CODE;
      let pass = 0;
      if (id.startsWith("IT")) {
        pass++;
      }
      if (level == 3) {
        pass++;
      }
      if (pass == 2 && inputData) {
        const code = dataMap.find((d) => d.id === id)?.code || "??";
        f.properties.code = code;
        let value = inputData.find((d) => d.code === code)?.value || null;
        if (value === null) {
          value =
            inputData.find(
              (d) => d.nuts_3_name?.trim().toLowerCase() === nuts_3_name?.trim().toLowerCase(),
            )?.value || null;
        }
        f.properties.value = value !== null ? value : 0.0;
        passedFeatures.push(f);
      }
    });
    return passedFeatures;
  };

  const italy_NUTS_3 = {
    type: "FeatureCollection",
    features: getProvinceDS(provinceData),
  };
  console.log("••• italy_NUTS_3", italy_NUTS_3);

  React.useEffect(() => {
    if (mapContainerRef.current && currentField) {
      mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_API_TOKEN;

      let areaPoints: number[][] = [];
      currentField.map.forEach((point: Point) => {
        areaPoints.push([point.lng, point.lat]);
      });
      if (areaPoints.length <= 2) {
        console.log("••• not enough points to draw the field shape", areaPoints);
        return;
      }

      let centroid: LngLatLike = [12.5736108, 41.29246];
      let fieldShapeBbox: any;
      if (areaPoints.length > 2) {
        const polygon = turf.polygon([areaPoints]);
        const result = turf.centroid(polygon);
        centroid = [result.geometry.coordinates[0], result.geometry.coordinates[1]];
        fieldShapeBbox = turf.bbox(polygon);
        console.log("••• bbox", fieldShapeBbox);
      }

      const interactions = {
        dragPan: true,
        dragRotate: true,
        scrollZoom: true,
        doubleClickZoom: true,
        touchZoomRotate: true,
        keyboard: true,
      };

      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: "mapbox://styles/mapbox/satellite-streets-v12",
        center: centroid,
        zoom: 5,
        ...interactions,
      });
      mapRef.current.addControl(new MapboxLanguage({ defaultLanguage: "it" }));

      mapRef.current.on("load", () => {
        console.log("map loaded", mapRef);

        // --------------------------------------------------
        // Add source + layer for dark cover
        // --------------------------------------------------

        let fullGlobeSource = {
          type: "geojson",
          data: {
            type: "Feature",
            geometry: {
              type: "Polygon",
              coordinates: [
                [
                  [-180, -85],
                  [180, -85],
                  [180, 85],
                  [-180, 85],
                  [-180, -85],
                ],
              ],
            },
          },
        };

        // darken base layer
        // mapRef.current.setPaintProperty("satellite", "raster-brightness-min", 0);
        // mapRef.current.setPaintProperty("satellite", "raster-brightness-max", 0.5); // darker
        // mapRef.current.setPaintProperty("satellite", "raster-contrast", -0.3);
        mapRef.current.addLayer({
          id: "global-darken",
          type: "fill",
          source: fullGlobeSource,
          paint: {
            "fill-color": "rgba(28, 28, 28, 0.4)",
          },
        });

        // --------------------------------------------------
        // Add source + layer for areas
        // --------------------------------------------------

        // Add NUTS source
        mapRef.current!.addSource("italy_NUTS_3_source", {
          type: "geojson",
          data: italy_NUTS_3,
        });

        // Build a match expression for fill-color based on data
        const colorExpression: any[] = ["match", ["get", "NUTS_ID"]];
        italy_NUTS_3.features.forEach((d) => {
          const id = d.properties.NUTS_ID;
          const value = d.properties.value;
          const riskLevel = modelValueToRiskLevel(value);
          let color = "#" + getRiskColor(riskLevel);
          colorExpression.push(id, color);
        });
        colorExpression.push("#e0e0e0"); // default color

        // Fill layer for NUTS_3 polygons
        mapRef.current!.addLayer({
          id: "nuts3-fill",
          type: "fill",
          source: "italy_NUTS_3_source",
          paint: {
            "fill-color": colorExpression,
            "fill-opacity": 0.8,
          },
        });

        // Outline layer
        mapRef.current!.addLayer({
          id: "nuts3-outline",
          type: "line",
          source: "italy_NUTS_3_source",
          paint: {
            "line-color": "#111",
            "line-width": 0.5,
          },
        });

        // Build a match expression for labels (numbers)
        const labelExpression: any[] = ["match", ["get", "NUTS_ID"]];
        italy_NUTS_3.features.forEach((d) => {
          const id = d.properties.NUTS_ID;
          const value = d.properties.value;
          labelExpression.push(id, String(value));
        });
        labelExpression.push(""); // default: no label

        // Symbol layer for numbers at the center of each area
        mapRef.current!.addLayer({
          id: "nuts3-labels",
          type: "symbol",
          source: "italy_NUTS_3_source",
          layout: {
            "text-field": labelExpression,
            "text-size": 12,
            "text-font": ["Inter Bold", "Open Sans Bold", "Arial Unicode MS Bold"],
            "text-allow-overlap": true,
          },
          paint: {
            "text-color": "#222",
          },
        });

        // --------------------------------------------------
        // Add source + layer for field shape
        // --------------------------------------------------

        const source = mapRef.current.getSource("fieldShape");
        if (!source) {
          mapRef.current.addSource("fieldShape", {
            type: "geojson",
            data: {
              type: "Feature",
              geometry: {
                type: "Polygon",
                coordinates: [areaPoints],
              },
            },
          });
        }

        mapRef.current.addLayer({
          id: "fieldShape",
          type: "fill",
          source: "fieldShape",
          layout: {},
          paint: {
            "fill-color": "rgba(0, 0, 0, 0.05)", // fill color
            "fill-opacity": 1.0, // fill opacity
          },
        });
        mapRef.current.addLayer({
          id: "fieldShapeLine",
          type: "line",
          source: "fieldShape",
          layout: {},
          paint: {
            "line-color": "rgba(0, 0, 0, 0.9)", // outline color
            "line-width": 2,
            "line-opacity": 1.0, // outline opacity
          },
        });

        // --------------------------------------------------
        // Add source + layer for current location
        // --------------------------------------------------

        mapRef.current!.addSource("current-location", {
          type: "geojson",
          data: {
            type: "Feature",
            geometry: { type: "Point", coordinates: [0, 0] },
          },
        });

        // Static dot
        mapRef.current!.addLayer({
          id: "current-location-dot",
          type: "circle",
          source: "current-location",
          paint: {
            "circle-radius": 5,
            "circle-color": "#007AFF",
            "circle-opacity": 1,
          },
        });

        // Pulse layer
        mapRef.current!.addLayer({
          id: "current-location-pulse",
          type: "circle",
          source: "current-location",
          paint: {
            "circle-radius": 5,
            "circle-color": "#007AFF",
            "circle-opacity": 0,
            "circle-radius-transition": { duration: 0, delay: 0 },
            "circle-opacity-transition": { duration: 0, delay: 0 },
          },
        });

        function animatePulse(startTime: number) {
          const t = (performance.now() - startTime) / 1000;
          const cycle = 2; // seconds per pulse
          const minRadius = 5;
          const maxRadius = 40;
          const maxOpacity = 0.8;

          // Instead of one pulse, compute multiple overlapping pulses
          const pulses = 3; // number of simultaneous ripples
          const radii: number[] = [];
          const opacities: number[] = [];

          for (let i = 0; i < pulses; i++) {
            const offset = i * (cycle / pulses);
            const progress = ((t - offset) % cycle) / cycle;

            const radius = minRadius + progress * (maxRadius - minRadius);
            const opacity = maxOpacity * (1 - progress);

            radii.push(radius);
            opacities.push(opacity);
          }

          // Use the largest radius and highest opacity for the layer
          // (or dynamically create multiple layers if you want all visible)
          const radius = radii[0];
          const opacity = opacities[0];

          if (mapRef.current && mapRef.current.setPaintProperty) {
            mapRef.current.setPaintProperty("current-location-pulse", "circle-radius", radius);
            mapRef.current.setPaintProperty("current-location-pulse", "circle-opacity", opacity);
          }

          requestAnimationFrame(() => animatePulse(startTime));
        }

        animatePulse(performance.now());
        // --------------------------------------------------

        const bologna = italy_NUTS_3.features.find((f) => f.properties.NUTS_ID === "ITH55");
        // console.error(bologna);
        // let bolognaAreaPoints: number[][] = [];
        // bologna.geometry.coordinates[0].forEach((point: Point) => {
        //   bolognaAreaPoints.push(point);
        // });
        let bolognaAreaPoints: number[][] = bologna.geometry.coordinates[0];
        if (bolognaAreaPoints.length <= 2) {
          console.log("••• not enough points in bolognaAreaPoints", bolognaAreaPoints);
          return;
        }
        let BolognaBbox: any;
        if (bolognaAreaPoints.length > 2) {
          const polygon = turf.polygon([bolognaAreaPoints]);
          const result = turf.centroid(polygon);
          centroid = [result.geometry.coordinates[0], result.geometry.coordinates[1]];
          BolognaBbox = turf.bbox(polygon);
          console.log("••• bologna_bbox", BolognaBbox);
        }

        //merge a default object with optional parameter
        const padding = { top: 50, bottom: 50, left: 50, right: 50 };
        mapRef.current.fitBounds(BolognaBbox, {
          padding: padding,
        });
        // mapRef.current.setZoom(7);

        setMapLoaded(true);
      });

      return () => {
        mapRef.current.remove();
      };
    }
  }, [mapContainerRef.current, currentField]);

  React.useEffect(() => {
    if (mapLoaded) {
      // Update source data
      const source = mapRef.current!.getSource("current-location") as mapboxgl.GeoJSONSource;
      if (source) {
        source.setData({
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: [currentPosition.lng, currentPosition.lat],
          },
          properties: {}, // 👈 required by type definition
        });
      }
    }
    // Optionally recenter map
    // mapRef.current!.setCenter([lng, lat]);
    // ----------------------------------
  }, [mapLoaded, currentPosition]);

  React.useEffect(() => {
    if (mapLoaded) {
      // Update source data
      const source = mapRef.current!.getSource("italy_NUTS_3_source") as mapboxgl.GeoJSONSource;
      if (source) {
        const italy_NUTS_3 = {
          type: "FeatureCollection",
          features: getProvinceDS(provinceData),
        };
        console.log("••• italy_NUTS_3", italy_NUTS_3);
        
        // @ts-ignore
        source.setData(italy_NUTS_3);
      }
    }
    // Optionally recenter map
    // mapRef.current!.setCenter([lng, lat]);
    // ----------------------------------
  }, [mapLoaded, provinceData]);

  return <div ref={mapContainerRef} className="map-observations"></div>;
};
