import { useAppDispatch, useAppSelector } from "../../../hooks";
import React, { Fragment } from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import _ from "lodash";
import { fieldsSelectors } from "../state/fields-slice";
import { SearchBox } from "@mapbox/search-js-react";
import mapboxgl, { LngLatLike} from "mapbox-gl";
import { useParams } from "react-router-dom";
import { Point } from "@tornatura/coreapis";
import * as turf from "@turf/turf";
import { detectionsSelectors } from "../../detections/state/detections-slice";

export function FieldMap() {
  const dispatch = useAppDispatch();
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default")
  );
  const detections = useAppSelector(state => detectionsSelectors.selectDetectionbyFieldId(state, fieldId ?? "default"));
  const mapContainerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<any>(null);
  const [mapLoaded, setMapLoaded] = React.useState(false);
  const [inputValue, setInputValue] = React.useState("");
  // const markerRef = React.useRef<Marker | null>(null);


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

        /*mapRef.current.on('click', function (e: any) {
          const { lng, lat } = e.lngLat;
          if (markerRef.current) {
            markerRef.current.setLngLat([lng, lat]);
          } else {
            markerRef.current = new mapboxgl.Marker()
              .setLngLat([lng, lat])
              .addTo(mapRef.current!);
          }
        });*/

        for (let detection of detections) {
          new mapboxgl.Marker()
            .setLngLat([detection.position.lng, detection.position.lat])
            .addTo(mapRef.current!);
        }

        setMapLoaded(true);
      });

      return () => {
        mapRef.current.remove();
      };
    }
  }, [mapContainerRef, currentField, detections]);

  return (
    <Fragment>
      {mapLoaded && (
        <div className="mapbox-searchbox-wrapper field-map-mapbox-searchbox-wrapper">
          {/*@ts-ignore*/}
          <SearchBox
            options={{
              language: "it",
              country: "IT",
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
        </div>
      )}
      <div ref={mapContainerRef} id="map"></div>
    </Fragment>
  );
}
