import { useAppDispatch, useAppSelector } from "../../../hooks";
import React from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import _ from "lodash";
import { fieldsSelectors } from "../state/fields-slice";
// import { SearchBox } from "@mapbox/search-js-react";
import mapboxgl, { LngLatLike } from "mapbox-gl";
import MapboxLanguage from "@mapbox/mapbox-gl-language";
import { useNavigate, useParams } from "react-router-dom";
import { Point } from "@tornatura/coreapis";
import * as turf from "@turf/turf";
import { detectionsSelectors } from "../../detections/state/detections-slice";

export function FieldMap() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { companyId, fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default"),
  );
  const detections = useAppSelector((state) =>
    detectionsSelectors.selectDetectionbyFieldId(state, fieldId ?? "default"),
  );
  const mapContainerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<any>(null);
  // const [mapLoaded, setMapLoaded] = React.useState(false);
  // const [inputValue, setInputValue] = React.useState("");

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
      let fieldShapeBbox: any;
      if (data.length > 2) {
        const polygon = turf.polygon([data]);
        const result = turf.centroid(polygon);
        centroid = [result.geometry.coordinates[0], result.geometry.coordinates[1]];
        fieldShapeBbox = turf.bbox(polygon);
      }

      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: "mapbox://styles/mapbox/satellite-streets-v12",
        center: centroid,
        zoom: 14,
      });
      mapRef.current.addControl(new MapboxLanguage({ defaultLanguage: "it" }));

      mapRef.current.on("load", () => {
        const source = mapRef.current.getSource("fieldShape");
        if (!source) {
          mapRef.current.addSource("fieldShape", {
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
          id: "fieldFill",
          type: "fill",
          source: "fieldShape",
          layout: {},
          paint: {
            "fill-color": "#EAFF00",
            "fill-opacity": 0.2,
          },
        });

        mapRef.current.addLayer({
          id: "fieldShapeLine",
          type: "line",
          source: "fieldShape",
          layout: {},
          paint: {
            "line-color": "#EAFF00", // outline color
            "line-width": 1,
            "line-opacity": 1.0, // outline opacity
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

        /*  
        for (let detection of detections) {
          new mapboxgl.Marker()
            .setLngLat([detection.position.lng, detection.position.lat])
            .addTo(mapRef.current!);
        }
        */

        const contW = mapContainerRef.current?.offsetWidth || 0;
        const contH = mapContainerRef.current?.offsetHeight || 0;
        mapRef.current.fitBounds(fieldShapeBbox, {
          padding: { top: contH * 0.4, bottom: contH * 0.4, left: contW * 0.4, right: contW * 0.4 },
        });

        // setMapLoaded(true);
      });

      return () => {
        mapRef.current.remove();
      };
    }
  }, [mapContainerRef, currentField, detections]);

  return (
    <>
      <div className="remove-content-padding-x remove-content-padding-y">
        {/*       {mapLoaded && (
        <div className="mapbox-searchbox-wrapper field-map-mapbox-searchbox-wrapper">
          {/*@ts-ignore* /}
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
 */}
        <div ref={mapContainerRef} id="map"></div>

        <button
          className="trnt_btn primary me-3 position-absolute top-0 start-0 m-3"
          data-type="round"
          onClick={() => {
            navigate(`/companies/${companyId}/fields/${fieldId}`, { replace: true });
          }}
        >
          &larr;
        </button>
      </div>
    </>
  );
}
