import React from "react";
import mapboxgl, { LngLatLike } from "mapbox-gl";
import * as turf from "@turf/turf";
import { useParams } from "react-router-dom";
import { useAppSelector } from "../hooks";
import { fieldsSelectors } from "../features/fields/state/fields-slice";
import { gpsStore } from "../providers/gps-providers";
import { Detection, Point } from "@tornatura/coreapis";
import { detectionsSelectors } from "../features/detections/state/detections-slice";
import { enrichedMapPoints } from "../helpers/detections";
import { detectionTypesSelectors } from "../features/detection-types/state/detection-types-slice";
import { observationTypesSelectors } from "../features/observation-types/state/observation-types-slice";

interface FieldMapletProps {
  // id of a detection
  // if provided, shows the detection points on the map
  detectionId: string | null | undefined;

  // (to be implemented)
  // id of a detection
  // if provided, shows the phantom points on the map
  phantomId?: string;

  // (to be implemented)
  // map padding options
  padding?: {};

  // (to be implemented) - refer to https://docs.mapbox.com/mapbox-gl-js/example/toggle-interaction-handlers/
  // map interactions on/off
  // available interactions: "scrollZoom", "boxZoom", "dragRotate", "dragPan", "keyboard", "doubleClickZoom", "touchZoomRotate"
  // all on by default
  interactions?: {};
}

function isPointInsideField(pointLon: number, pointLat: number, areaPoints: number[][]) {
  if (areaPoints.length > 2) {
    const polygon = turf.polygon([areaPoints]);
    const point = turf.point([pointLon, pointLat]);
    const isContained = turf.booleanContains(polygon, point);
    return isContained;
  }
  return false;
}

export const FieldMaplet = ({ detectionId, padding, interactions }: FieldMapletProps) => {
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default"),
  );
  const mapContainerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<any>(null);
  const [mapLoaded, setMapLoaded] = React.useState(false);
  const currentPosition = React.useContext(gpsStore);

  const [selectedDetection, setSelectedDetection] = React.useState<Detection | null>(null);
  const detections = useAppSelector((state) =>
    detectionsSelectors.selectDetectionbyFieldId(state, fieldId ?? "default"),
  );
  const detectionTypes = useAppSelector((state) =>
    detectionTypesSelectors.selectDetectionTypesByField(state, fieldId ?? "default"),
  );
  const observationTypes = useAppSelector((state) =>
    observationTypesSelectors.selectObservationTypes(state),
  );

  function getDetectionPoints() {
    if (selectedDetection) {
      const points = selectedDetection?.detectionData?.points
        ? selectedDetection.detectionData.points
        : [];
      console.log("FieldMap points", points);

      for (let detectionType of detectionTypes) {
        if (detectionType.id === selectedDetection.detectionTypeId) {
          const observationType = observationTypes.find(
            (ot) => ot.id === detectionType.observationTypeId,
          );
          console.log("••• observationType", observationType);
          if (observationType) {
            return enrichedMapPoints(points, observationType);
          }
        }
      }
    }
    return [];
  }

  React.useEffect(() => {
    console.log("TTTTTTTTTT detectionId", detectionId);
    if (detectionId) {
      const det = detections.find((d) => d.id === detectionId);
      if (det) {
        setSelectedDetection(det);
      } else {
        setSelectedDetection(null);
      }
    }
  }, [detectionId]);

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

      const defaultInteractions = {
        dragPan: true,
        dragRotate: true,
        scrollZoom: true,
        doubleClickZoom: true,
        touchZoomRotate: true,
        keyboard: true,
      };
      const mergedInteractions = {
        ...defaultInteractions,
        ...interactions,
      };

      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: "mapbox://styles/mapbox/satellite-streets-v12",
        center: centroid,
        zoom: 18,
        ...mergedInteractions,
      });

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
            "fill-color": "rgba(28, 28, 28, 0.7)",
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
            "fill-color": "rgba(255, 255, 255, 0.2)", // fill color
            "fill-opacity": 1.0, // fill opacity
          },
        });
        mapRef.current.addLayer({
          id: "fieldShapeLine",
          type: "line",
          source: "fieldShape",
          layout: {},
          paint: {
            "line-color": "rgba(255, 255, 255, 0.4)", // outline color
            "line-width": 2,
            "line-opacity": 1.0, // outline opacity
          },
        });

        //merge a default object with optional parameter
        const paddingDefault = { top: 50, bottom: 50, left: 50, right: 50 };
        const paddingMerged = {
          ...paddingDefault,
          ...(typeof padding === "object" ? padding : {}),
        };
        mapRef.current.fitBounds(fieldShapeBbox, {
          padding: paddingMerged,
        });

        // --------------------------------------------------
        // (Add source + layer for detection phantom)
        // --------------------------------------------------

        // --------------------------------------------------
        // Add source + layer for selected detection
        // --------------------------------------------------

        const pointsGeoJSON = {
          type: "FeatureCollection",
          features: getDetectionPoints().map((pt) => ({
            type: "Feature",
            geometry: {
              type: "Point",
              coordinates: [pt.lng, pt.lat],
            },
            properties: {
              size: pt.size,
              color: pt.color,
            },
          })),
        };
        const lineGeoJSON = {
          type: "Feature",
          geometry: {
            type: "LineString",
            coordinates: getDetectionPoints().map((pt) => [pt.lng, pt.lat]),
          },
          properties: {},
        };
        console.log("••• pointsGeoJSON", JSON.stringify(pointsGeoJSON));
        mapRef.current!.addSource("dataPointsPath", {
          type: "geojson",
          data: lineGeoJSON,
        });
        mapRef.current!.addLayer({
          id: "dataPoints",
          type: "line",
          source: "dataPointsPath",
          paint: {
            "line-color": "rgba(255, 255, 255, 0.9)",
            "line-opacity": 1.0,
            "line-width": 2,
            "line-dasharray": [1, 0.5], // ← dashed line
          },
        });

        mapRef.current!.addSource("dataPoints", {
          type: "geojson",
          data: pointsGeoJSON,
        });

        mapRef.current!.addLayer({
          id: "dataPointsDots",
          type: "circle",
          source: "dataPoints",
          paint: {
            "circle-radius": ["get", "size"],
            "circle-color": ["get", "color"],
            "circle-opacity": 0.8,
            "circle-stroke-color": "rgba(255, 255, 255, 0.9)",
            "circle-stroke-opacity": 1.0,
            "circle-stroke-width": 1.5,
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

        mapRef.current.on("click", function (e: any) {
          const { lng, lat } = e.lngLat;

          // Check if inside field shape
          let point: Point = {
            lat: lat,
            lng: lng,
          };
          console.log(">>> clicked point", point);

          const isIt = isPointInsideField(lng, lat, areaPoints);
          console.log(">>> isPointInsideField? " + isIt);
          if (!isIt) {
            turf.polygon([areaPoints]);
            const polygon = turf.polygon([areaPoints]);
            const p = turf.point([lng, lat]);
            const boundary = turf.polygonToLine(polygon);
            const safeBoundary =
              boundary.type === "FeatureCollection"
                ? boundary.features[0] // or merge them if needed
                : boundary;
            const nearest = turf.nearestPointOnLine(safeBoundary, p);
            point = {
              lat: nearest.geometry.coordinates[1],
              lng: nearest.geometry.coordinates[0],
            };
            // alert("Attenzione: il punto selezionato non è all'interno del campo!");
            console.log(">>> nearest point on field boundary", nearest);
          }
        });

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

  const minPointSize = 2;
  React.useEffect(() => {
    if (mapLoaded) {
      console.log("pippppoooooooo detection change");
      const selectedDetectionMapPoints = getDetectionPoints();

      const sourcePath = mapRef.current!.getSource("dataPointsPath") as mapboxgl.GeoJSONSource;

      const lineGeoJSON: GeoJSON.Feature = {
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: selectedDetectionMapPoints.map((pt) => [pt.lng, pt.lat]),
        },
        properties: {},
      };
      sourcePath?.setData(lineGeoJSON);

      const sourcePoints = mapRef.current!.getSource("dataPoints") as mapboxgl.GeoJSONSource;
      const pointsGeoJSON: GeoJSON.FeatureCollection = {
        type: "FeatureCollection",
        features: selectedDetectionMapPoints.map((pt) => ({
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: [pt.lng, pt.lat],
          },
          properties: {
            size: pt.size > 0 ? pt.size : minPointSize, // default size if not provided
            color: pt.color,
          },
        })),
      };
      sourcePoints?.setData(pointsGeoJSON);
    }
  }, [selectedDetection, mapLoaded]);

  if (!selectedDetection && !mapLoaded) {
    return <div>Detection not found</div>;
  } else {
    return <div ref={mapContainerRef} className="map-observations"></div>;
  }
};
