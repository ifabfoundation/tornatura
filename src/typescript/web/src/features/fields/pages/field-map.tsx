import { useAppDispatch, useAppSelector } from "../../../hooks";
import React, { Fragment } from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Col, Container, Row } from "react-bootstrap";
import _ from "lodash";
import { fieldsSelectors } from "../state/fields-slice";
import mapboxgl, { LngLatLike } from "mapbox-gl";
import { useParams } from "react-router-dom";
import { Point } from "@tornatura/coreapis";
import * as turf from "@turf/turf";

export function FieldMap() {
  const dispatch = useAppDispatch();
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default")
  );
  const mapContainerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<any>(null);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Mappa", subtitle: "Subtitle" }));
  }, []);

  React.useEffect(() => {
    if (mapContainerRef.current && currentField) {
      mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_API_TOKEN;

      let data: number[][] = [];
      currentField.map.forEach((point: Point) => {
        data.push([point.lng, point.lat]);
      });

      let centroid: LngLatLike = [12.5736108, 41.29246];
      if (data.length > 2) {
        const polygon = turf.polygon([data]);
        const result = turf.centroid(polygon);
        centroid = [result.geometry.coordinates[0], result.geometry.coordinates[1]];
      }

      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: "mapbox://styles/mapbox/satellite-v9",
        center: centroid,
        zoom: 14,
      });

      mapRef.current.on("load", () => {
        const source = mapRef.current.getSource("maine");
        if (!source) {
          mapRef.current.addSource("maine", {
            type: "geojson",
            data: {
              type: "Feature",
              geometry: {
                type: "Polygon",
                coordinates: [data],
              },
            },
          });
        }

        mapRef.current.addLayer({
          id: "maine",
          type: "fill",
          source: "maine",
          layout: {},
          paint: {
            "fill-color": "#c4c920",
            "fill-opacity": 0.7,
          },
        });
      });
    }
  }, [mapContainerRef, currentField]);

  return (
    <Fragment>
      <div ref={mapContainerRef} id="map"></div>
    </Fragment>
  );
}
