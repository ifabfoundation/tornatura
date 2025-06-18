import { useAppDispatch, useAppSelector } from "../../../hooks";
import React, { Fragment } from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import _ from "lodash";
import { fieldsSelectors } from "../state/fields-slice";
import { SearchBox } from "@mapbox/search-js-react";
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
  const [mapLoaded, setMapLoaded] = React.useState(false);
  const [inputValue, setInputValue] = React.useState("");

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
        style: "mapbox://styles/mapbox/satellite-streets-v12",
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

        setMapLoaded(true);
      });
    }
  }, [mapContainerRef, currentField]);

  return (
    <Fragment>
      {mapLoaded && <div style={{maxWidth: "400px", margin: '20px', zIndex: 2}}>
        <SearchBox
          options={{
            language: 'it',
            country: 'IT'
          }}
          accessToken={process.env.REACT_APP_MAPBOX_API_TOKEN ?? ""}
          map={mapRef.current}
          mapboxgl={mapboxgl}
          value={inputValue}
          onChange={(d) => {
            setInputValue(d);
          }}
          marker
        />
      </div>}
      <div ref={mapContainerRef} id="map"></div>
    </Fragment>
  );
}
