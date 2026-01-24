"""
Visualizzazione interattiva del rischio peronospora per province Emilia-Romagna
Mappa satellitare con Folium - Include tutte le settimane con navigazione
"""

import json
import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


import sys

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from peronospora import paths

# Load risk levels configuration
SCRIPT_DIR = paths.PACKAGE_DIR
with open(SCRIPT_DIR / "risk_levels.json", 'r', encoding='utf-8') as f:
    RISK_CONFIG = json.load(f)

# Mapping nomi province per match con shapefile
PROVINCE_MAPPING = {
    'bologna': 'Bologna',
    'ferrara': 'Ferrara',
    'forli_cesena': 'Forlì-Cesena',
    'modena': 'Modena',
    'parma': 'Parma',
    'piacenza': 'Piacenza',
    'ravenna': 'Ravenna',
    "reggio_nell_emilia": 'Reggio nell\'Emilia',
    'rimini': 'Rimini'
}


def get_color_from_level(level: int) -> str:
    """Get color from risk level (1-5)."""
    return RISK_CONFIG.get(str(level), {}).get("colore", "#888888")


def get_label_from_level(level: int) -> str:
    """Get label from risk level (1-5)."""
    return RISK_CONFIG.get(str(level), {}).get("label", "Unknown")


def load_all_predictions(predictions_dir=None):
    """Carica le predizioni per tutti i lead (0, 1)"""
    all_predictions = {}
    if predictions_dir is None:
        predictions_dir = paths.PREDICTIONS_DIR

    for lead in [0, 1]:
        file_path = Path(predictions_dir) / f'lead_{lead}.csv'

        if not file_path.exists():
            print(f"⚠ Warning: {file_path} not found, skipping lead {lead}")
            continue

        df = pd.read_csv(file_path)

        # Aggrega per provincia (media se ci sono record multipli)
        agg = df.groupby('NUTS_3').agg({
            'risk_score': 'mean',
            'risk_level': 'first',
            'risk_label': 'first',
            'temp': 'mean',
            'prec': 'sum',
            'rh': 'mean',
            'lw': 'sum',
            'forecast_base': 'first',
            'target_period_start': 'first',
            'target_period_end': 'first'
        }).reset_index()

        # Normalizza nomi province
        agg['province_name'] = agg['NUTS_3'].map(PROVINCE_MAPPING)

        # Filter to only mapped provinces (Emilia-Romagna)
        agg = agg[agg['province_name'].notna()]

        all_predictions[lead] = agg

    return all_predictions


def load_emilia_romagna_shapefile():
    """Carica shapefile province italiane e filtra Emilia-Romagna."""
    static_shapefile = paths.STATIC_DATA_DIR / "weather" / "shapefiles" / "province_emilia_romagna.shp"
    local_shapefile = paths.WEATHER_DIR / "shapefiles" / "province_emilia_romagna.shp"

    if static_shapefile.exists():
        gdf = gpd.read_file(static_shapefile)
        print(f"✓ Loaded shapefile from {static_shapefile}")
    elif local_shapefile.exists():
        gdf = gpd.read_file(local_shapefile)
        print(f"✓ Loaded shapefile from {local_shapefile}")
    else:
        print("Downloading Italy provinces shapefile...")
        url = "https://github.com/openpolis/geojson-italy/raw/master/geojson/limits_IT_provinces.geojson"

        try:
            gdf = gpd.read_file(url)
            print("✓ Downloaded shapefile from openpolis")

            emilia_province_names = list(PROVINCE_MAPPING.values())
            gdf = gdf[gdf['prov_name'].isin(emilia_province_names)]

            local_shapefile.parent.mkdir(parents=True, exist_ok=True)
            gdf.to_file(local_shapefile)
            print(f"✓ Saved shapefile to {local_shapefile}")

        except Exception as e:
            print(f"⚠ Error downloading shapefile: {e}")
            raise

    if 'prov_name' in gdf.columns:
        gdf = gdf.rename(columns={'prov_name': 'province_name'})
    elif 'DEN_UTS' in gdf.columns:
        gdf = gdf.rename(columns={'DEN_UTS': 'province_name'})

    if gdf.crs != 'EPSG:4326':
        gdf = gdf.to_crs('EPSG:4326')

    return gdf


def create_popup_html(row):
    """Crea HTML per popup informativo"""
    color = get_color_from_level(row['risk_level'])

    html = f"""
    <div style="font-family: Arial, sans-serif; width: 300px;">
        <h3 style="margin: 0 0 10px 0; color: #333; border-bottom: 2px solid {color}; padding-bottom: 5px;">
            {row['province_name']}
        </h3>

        <div style="background-color: {color}; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px; text-align: center;">
            <div style="font-size: 24px; font-weight: bold;">{row['risk_score']:.2f}</div>
            <div style="font-size: 14px; font-weight: bold;">Livello {row['risk_level']} - {row['risk_label']}</div>
        </div>

        <table style="width: 100%; font-size: 13px;">
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 5px;"><b>🌡️ Temperatura</b></td>
                <td style="padding: 5px; text-align: right;">{row['temp']:.1f}°C</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>🌧️ Precipitazioni</b></td>
                <td style="padding: 5px; text-align: right;">{row['prec']:.1f} mm</td>
            </tr>
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 5px;"><b>💧 Umidità</b></td>
                <td style="padding: 5px; text-align: right;">{row['rh']:.0f}%</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>🍃 Bagnatura fogliare</b></td>
                <td style="padding: 5px; text-align: right;">{row['lw']:.0f} ore</td>
            </tr>
        </table>

        <div style="margin-top: 10px; padding: 8px; background-color: #e8f4f8; border-left: 4px solid #3498db; font-size: 12px;">
            <b>📅 Periodo previsione:</b><br>
            {row['target_period_start']} / {row['target_period_end']}
        </div>
    </div>
    """
    return html


def create_legend_html():
    """Crea HTML per legenda rischi"""
    html = """
    <div style="position: fixed;
                bottom: 50px; right: 50px;
                width: 200px;
                background-color: white;
                border: 2px solid grey;
                border-radius: 10px;
                z-index: 9999;
                padding: 15px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);">

        <h4 style="margin: 0 0 10px 0; text-align: center; color: #333; border-bottom: 2px solid #333; padding-bottom: 5px;">
            Livelli di Rischio
        </h4>

        <div style="font-size: 13px;">
    """

    # From highest to lowest
    for level in [5, 4, 3, 2, 1]:
        color = get_color_from_level(level)
        label = get_label_from_level(level)
        html += f"""
        <div style="margin: 8px 0; display: flex; align-items: center;">
            <div style="width: 30px; height: 20px; background-color: {color};
                        border: 1px solid #333; margin-right: 10px; border-radius: 3px;">
            </div>
            <span><b>{level}</b> - {label}</span>
        </div>
        """

    html += """
        </div>

        <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 10px; color: #666; text-align: center;">
            Peronospora Risk Model
        </div>
    </div>
    """

    return html


def create_satellite_map_all_weeks(all_predictions, gdf, output_file=None):
    if output_file is None:
        output_file = str(paths.RISK_MAP_PATH)
    """Crea mappa interattiva con satellite imagery e navigazione tra settimane"""

    center_lat = 44.5
    center_lon = 11.5

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles=None,
        control_scale=True
    )

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Labels',
        overlay=True,
        control=True,
        opacity=0.7
    ).add_to(m)

    week_labels = {
        0: "📅 Settimana Corrente (lead 0)",
        1: "📅 Prossima Settimana (lead 1)"
    }

    for lead in sorted(all_predictions.keys()):
        predictions = all_predictions[lead]
        merged = gdf.merge(predictions, on='province_name', how='left')

        fg = folium.FeatureGroup(
            name=week_labels.get(lead, f"Lead {lead}"),
            show=(lead == 0)  # Show lead 0 by default
        )

        for _, row in merged.iterrows():
            if pd.notna(row.get('risk_score')):
                color = get_color_from_level(int(row['risk_level']))

                geojson = folium.GeoJson(
                    row['geometry'].__geo_interface__,
                    style_function=lambda x, c=color: {
                        'fillColor': c,
                        'color': 'white',
                        'weight': 3,
                        'fillOpacity': 0.6,
                        'opacity': 1
                    },
                    highlight_function=lambda x: {
                        'weight': 5,
                        'fillOpacity': 0.8
                    },
                    tooltip=folium.Tooltip(
                        f"""<div style="font-family: Arial; font-size: 13px; padding: 5px;">
                            <b style="font-size: 15px;">{row['province_name']}</b><br>
                            <hr style="margin: 5px 0; border: 0; border-top: 1px solid #ccc;">
                            <b>Rischio:</b> {row['risk_score']:.2f} (Livello {int(row['risk_level'])} - {row['risk_label']})<br>
                            <hr style="margin: 5px 0; border: 0; border-top: 1px solid #ccc;">
                            🌡️ Temp: {row['temp']:.1f}°C<br>
                            🌧️ Prec: {row['prec']:.1f} mm<br>
                            💧 Umidità: {row['rh']:.0f}%<br>
                            🍃 Bagnatura: {row['lw']:.0f} ore
                        </div>""",
                        sticky=True
                    ),
                    popup=folium.Popup(
                        create_popup_html(row),
                        max_width=350
                    )
                )
                geojson.add_to(fg)

                centroid = row['geometry'].centroid
                label = folium.Marker(
                    location=[centroid.y, centroid.x],
                    icon=folium.DivIcon(html=f"""
                        <div style="font-size: 12px;
                                    font-weight: bold;
                                    color: white;
                                    text-shadow:
                                        -1px -1px 0 #000,
                                        1px -1px 0 #000,
                                        -1px 1px 0 #000,
                                        1px 1px 0 #000,
                                        -2px 0 0 #000,
                                        2px 0 0 #000,
                                        0 -2px 0 #000,
                                        0 2px 0 #000;
                                    text-align: center;">
                            {row['province_name']}<br>
                            <span style="font-size: 16px;">{row['risk_score']:.1f}</span>
                        </div>
                    """)
                )
                label.add_to(fg)

        fg.add_to(m)

    m.get_root().html.add_child(folium.Element(create_legend_html()))

    # Get forecast date from first available lead
    first_lead = min(all_predictions.keys())
    forecast_date = all_predictions[first_lead]['forecast_base'].iloc[0]

    title_html = f'''
    <div style="position: fixed;
                top: 10px;
                left: 50%;
                transform: translateX(-50%);
                width: 600px;
                background-color: rgba(255, 255, 255, 0.95);
                border: 3px solid #333;
                border-radius: 10px;
                z-index: 9999;
                padding: 15px;
                text-align: center;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
        <h2 style="margin: 0; color: #2c3e50; font-size: 24px;">
            🍇 Rischio Peronospora - Emilia-Romagna
        </h2>
        <div style="margin-top: 8px; font-size: 14px; color: #555;">
            Previsione del: <b>{forecast_date}</b>
        </div>
        <div style="margin-top: 5px; font-size: 12px; color: #777;">
            Usa il controllo layer (angolo in alto a destra) per cambiare settimana
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    folium.LayerControl(position='topright', collapsed=False).add_to(m)

    plugins.Fullscreen(
        position='topright',
        title='Espandi mappa',
        title_cancel='Esci da schermo intero',
        force_separate_button=True
    ).add_to(m)

    plugins.MeasureControl(
        position='topleft',
        primary_length_unit='kilometers',
        secondary_length_unit='meters',
        primary_area_unit='hectares'
    ).add_to(m)

    m.save(output_file)
    print(f"✓ Satellite map saved to: {output_file}")

    return m


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate Peronospora Risk Map')
    parser.add_argument('--output', type=str, default=paths.RISK_MAP_PATH,
                       help='Output HTML file name')
    parser.add_argument('--predictions_dir', type=str, default=paths.PREDICTIONS_DIR,
                       help='Directory containing prediction CSV files')

    args = parser.parse_args()

    print("="*70)
    print("PERONOSPORA RISK MAP - SATELLITE VIEW")
    print("="*70)

    print("\n1. Loading predictions...")
    all_predictions = load_all_predictions(args.predictions_dir)

    if len(all_predictions) == 0:
        print("❌ No predictions found!")
        return

    for lead, pred in all_predictions.items():
        print(f"   ✓ Lead {lead}: {len(pred)} provinces")

    print("\n2. Loading shapefile...")
    gdf = load_emilia_romagna_shapefile()
    print(f"   ✓ {len(gdf)} provinces")

    print("\n3. Creating map...")
    create_satellite_map_all_weeks(all_predictions, gdf, output_file=args.output)

    print("\n" + "="*70)
    print(f"✓ Map saved to '{args.output}'")
    print("="*70)


if __name__ == '__main__':
    main()
