import React from "react";
import mapboxgl, { LngLatLike } from "mapbox-gl";
import * as turf from "@turf/turf";
import { useParams } from "react-router-dom";
import { useAppSelector } from "../hooks";
import { fieldsSelectors } from "../features/fields/state/fields-slice";
import { gpsStore } from "../providers/gps-providers";
import { Point } from "@tornatura/coreapis";

interface FieldMapProps {
  detection?: mapPoint[];
  debugString?: string;
}

interface mapPoint {
  lng: number;
  lat: number;
  size?: number;
  color?: string;
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

export const FieldMap = ({ detection, debugString }: FieldMapProps) => {
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default"),
  );
  const mapContainerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<any>(null);
  const [mapLoaded, setMapLoaded] = React.useState(false);
  const currentPosition = React.useContext(gpsStore);

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

      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: "mapbox://styles/mapbox/satellite-streets-v12",
        center: centroid,
        zoom: 14,
      });

      mapRef.current.on("load", () => {
        console.log("map loaded", mapRef);

        // darken base layer
        // mapRef.current.setPaintProperty("satellite", "raster-brightness-min", 0);
        // mapRef.current.setPaintProperty("satellite", "raster-brightness-max", 0.5); // darker
        // mapRef.current.setPaintProperty("satellite", "raster-contrast", -0.3);
        mapRef.current.addLayer({
          id: "global-darken",
          type: "fill",
          source: fullGlobeSource,
          paint: {
            "fill-color": "rgba(0, 0, 0, 0.5)",
          },
        });

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
            "fill-color": "#fff",
            "fill-opacity": 0.3,
          },
        });
        mapRef.current.addLayer({
          id: "fieldShapeLine",
          type: "line",
          source: "fieldShape",
          layout: {},
          paint: {
            "line-color": "#fff",
            "line-width": 1.5,
            "line-opacity": 1.0, // outline opacity
          },
        });

        mapRef.current.fitBounds(fieldShapeBbox, {
          padding: { top: 50, bottom: 50, left: 50, right: 50 },
        });

        // --------------------------------------------------
        // Add source + layer for data (points)
        const points: mapPoint[] = [];

        const pointsGeoJSON = {
          type: "FeatureCollection",
          features: points.map((pt) => ({
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
            coordinates: points.map((pt) => [pt.lng, pt.lat]),
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
            "line-color": "#fff",
            "line-opacity": 0.5,
            "line-width": 3,
            "line-dasharray": [1, 1.5], // ← dashed line
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
            "circle-stroke-color": "#fff",
            "circle-stroke-opacity": 0.8,
            "circle-stroke-width": 1.5,
          },
        });

        // --------------------------------------------------
        // Add source + layer for current location
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

          if (mapRef.current) {
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
  }, [mapContainerRef, currentField]);

  React.useEffect(() => {
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

    // Optionally recenter map
    // mapRef.current!.setCenter([lng, lat]);
    // ----------------------------------
  }, [mapLoaded, currentPosition]);

  return <div ref={mapContainerRef} className="map-observations" data-debug={debugString}></div>;
};
