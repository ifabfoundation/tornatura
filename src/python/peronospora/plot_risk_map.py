"""
Visualizzazione interattiva del rischio peronospora per tutte le province italiane
Mappa satellitare con Folium - Include tutte le settimane con navigazione
"""

import json
import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
from pathlib import Path
from datetime import datetime
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

# Load province mapping from centralized config
with open(SCRIPT_DIR / "data" / "provinces_italy.json", 'r', encoding='utf-8') as f:
    _PROVINCES_CONFIG = json.load(f)

# slug -> display_name (e.g. "forli_cesena" -> "Forlì-Cesena")
PROVINCE_MAPPING = {
    slug: info["display_name"]
    for slug, info in _PROVINCES_CONFIG.items()
}


def get_color_from_level(level: int) -> str:
    """Get color from risk level (0-4)."""
    return RISK_CONFIG.get(str(level), {}).get("colore", "#888888")


def get_label_from_level(level: int) -> str:
    """Get label from risk level (0-4)."""
    return RISK_CONFIG.get(str(level), {}).get("label", "Unknown")


def get_description_from_score(score: float) -> str:
    """Get risk description from continuous score using range thresholds."""
    level = get_level_from_score(score)
    return RISK_CONFIG.get(str(level), {}).get("descrizione", "")


def get_color_from_score(score: float) -> str:
    """
    Get color from continuous risk score using range thresholds.
    
    Ranges:
        0.0 - 1.0  -> Verde (#00cc00)
        1.0 - 2.0  -> Giallo (#ffff00)
        2.0 - 3.0  -> Arancione (#ffa500)
        3.0 - 3.5  -> Arancione scuro (#ff6600)
        3.5 - 4.0  -> Rosso (#ff0000)
    """
    if score < 1.0:
        return "#00cc00"
    elif score < 2.0:
        return "#ffff00"
    elif score < 3.0:
        return "#ffa500"
    elif score < 3.5:
        return "#ff6600"
    else:
        return "#ff0000"


def get_level_from_score(score: float) -> int:
    """Get risk level from continuous score using range thresholds."""
    if score < 1.0:
        return 0
    elif score < 2.0:
        return 1
    elif score < 3.0:
        return 2
    elif score < 3.5:
        return 3
    else:
        return 4


def format_date_italian(date_str):
    """Convert YYYY-MM-DD to DD.MM.YYYY"""
    try:
        dt = datetime.strptime(str(date_str), '%Y-%m-%d')
        return dt.strftime('%d.%m.%Y')
    except:
        return date_str


def load_all_predictions(predictions_dir='predictions'):
    """Carica le predizioni per tutti i lead (0, 1)"""
    all_predictions = {}

    for lead in [0, 1]:
        file_path = Path(predictions_dir) / f'lead_{lead}.csv'

        if not file_path.exists():
            print(f"  Warning: {file_path} not found, skipping lead {lead}")
            continue

        df = pd.read_csv(file_path)

        # Aggrega per provincia (media se ci sono record multipli)
        agg = df.groupby('NUTS_3').agg({
            'risk_score': 'mean',
            'risk_level': 'first',
            'risk_label': 'first',
            'bbch_code': 'first',
            'plant_susceptibility': 'first',
            'temp': 'mean',
            'prec': 'sum',
            'rh': 'mean',
            'lw': 'sum',
            'forecast_base': 'first',
            'target_period_start': 'first',
            'target_period_end': 'first'
        }).reset_index()

        # Normalizza nomi province (slug -> display_name)
        agg['province_name'] = agg['NUTS_3'].map(PROVINCE_MAPPING)

        # Keep only provinces that we can map
        agg = agg[agg['province_name'].notna()]

        all_predictions[lead] = agg

    return all_predictions


def load_italy_shapefile():
    """Carica shapefile di tutte le province italiane."""
    local_shapefile = Path('data/weather/shapefiles/province_italia.shp')

    if local_shapefile.exists():
        gdf = gpd.read_file(local_shapefile)
        print(f"  Loaded shapefile from {local_shapefile}")
    else:
        print("  Downloading Italy provinces shapefile...")
        url = "https://github.com/openpolis/geojson-italy/raw/master/geojson/limits_IT_provinces.geojson"

        try:
            gdf = gpd.read_file(url)
            print("  Downloaded shapefile from openpolis")

            local_shapefile.parent.mkdir(parents=True, exist_ok=True)
            gdf.to_file(local_shapefile)
            print(f"  Saved shapefile to {local_shapefile}")

        except Exception as e:
            print(f"  Error downloading shapefile: {e}")
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
    color = get_color_from_score(row['risk_score'])
    
    start_date = format_date_italian(row['target_period_start'])
    end_date = format_date_italian(row['target_period_end'])

    html = f"""
    <div style="font-family: Arial, sans-serif; width: 300px;">
        <h3 style="margin: 0 0 10px 0; color: #333; border-bottom: 2px solid {color}; padding-bottom: 5px;">
            {row['province_name']}
        </h3>

        <div style="background-color: {color}; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px; text-align: center;">
            <div style="font-size: 24px; font-weight: bold;">{row['risk_score']:.2f}</div>
            <div style="font-size: 14px; font-weight: bold;">Livello {row['risk_level']} - {row['risk_label']}</div>
        </div>

        <div style="padding: 8px; background-color: #f9f9f9; border-left: 4px solid {color}; margin-bottom: 10px; font-size: 12px; color: #555; font-style: italic;">
            {get_description_from_score(row['risk_score'])}
        </div>

        <table style="width: 100%; font-size: 13px;">
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 5px;"><b>🍇 Stadio BBCH</b></td>
                <td style="padding: 5px; text-align: right;">{int(row['bbch_code'])}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>🎯 Suscettibilita</b></td>
                <td style="padding: 5px; text-align: right;">{row['plant_susceptibility']:.2f}</td>
            </tr>
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 5px;"><b>🌡️ Temperatura</b></td>
                <td style="padding: 5px; text-align: right;">{row['temp']:.1f}°C</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>🌧️ Precipitazioni</b></td>
                <td style="padding: 5px; text-align: right;">{row['prec']:.1f} mm</td>
            </tr>
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 5px;"><b>💧 Umidita</b></td>
                <td style="padding: 5px; text-align: right;">{row['rh']:.0f}%</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>🍃 Bagnatura fogliare</b></td>
                <td style="padding: 5px; text-align: right;">{row['lw']:.0f} ore</td>
            </tr>
        </table>

        <div style="margin-top: 10px; padding: 8px; background-color: #e8f4f8; border-left: 4px solid #3498db; font-size: 12px;">
            <b>📅 Periodo previsione:</b><br>
            {start_date} - {end_date}
        </div>
    </div>
    """
    return html


def create_legend_html():
    """Crea HTML per legenda rischi con range"""
    
    legend_items = [
        {"range": "3.5 - 4.0", "color": "#ff0000", "label": "Rischio molto elevato"},
        {"range": "3.0 - 3.5", "color": "#ff6600", "label": "Rischio elevato"},
        {"range": "2.0 - 3.0", "color": "#ffa500", "label": "Attenzione"},
        {"range": "1.0 - 2.0", "color": "#ffff00", "label": "Sorveglianza"},
        {"range": "0.0 - 1.0", "color": "#00cc00", "label": "Nessun rischio"},
    ]
    
    html = """
    <div style="position: fixed;
                top: 20px; right: 20px;
                width: 340px;
                background-color: white;
                border: 2px solid grey;
                border-radius: 12px;
                z-index: 9998;
                padding: 24px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);">

        <h4 style="margin: 0 0 18px 0; text-align: center; color: #333; border-bottom: 2px solid #333; padding-bottom: 12px; font-size: 20px; font-weight: bold;">
            Livelli di Rischio
        </h4>

        <div style="font-size: 15px;">
    """

    for item in legend_items:
        html += f"""
        <div style="margin: 12px 0; display: flex; align-items: center;">
            <div style="width: 45px; height: 32px; background-color: {item['color']};
                        border: 1px solid #333; margin-right: 14px; border-radius: 4px; flex-shrink: 0;">
            </div>
            <span><b>{item['range']}</b> - {item['label']}</span>
        </div>
        """

    html += """
        </div>
    </div>
    """

    return html


def create_satellite_map_all_weeks(all_predictions, gdf, output_file='risk_map_satellite.html'):
    """Crea mappa interattiva con satellite imagery e navigazione tra settimane"""

    # Centro Italia
    center_lat = 42.0
    center_lon = 12.5

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        tiles=None,
        control_scale=True
    )

    # Solo layer Satellite Esri (default)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
        overlay=False,
        control=False
    ).add_to(m)

    # Raccogli le date per i bottoni
    week_dates = {}
    
    for lead in sorted(all_predictions.keys()):
        predictions = all_predictions[lead]
        start_date = format_date_italian(predictions['target_period_start'].iloc[0])
        end_date = format_date_italian(predictions['target_period_end'].iloc[0])
        week_dates[lead] = f"{start_date} - {end_date}"

    # Crea i FeatureGroup per ogni lead
    for lead in sorted(all_predictions.keys()):
        predictions = all_predictions[lead]
        merged = gdf.merge(predictions, on='province_name', how='left')

        layer_name = f"week_{lead}"
        
        fg = folium.FeatureGroup(
            name=layer_name,
            show=(lead == 0)
        )

        for _, row in merged.iterrows():
            if pd.notna(row.get('risk_score')):
                color = get_color_from_score(row['risk_score'])

                geojson = folium.GeoJson(
                    row['geometry'].__geo_interface__,
                    style_function=lambda x, c=color: {
                        'fillColor': c,
                        'color': 'rgba(255,255,255,0.6)',
                        'weight': 1.8,
                        'fillOpacity': 0.32,
                        'opacity': 0.5
                    },
                    highlight_function=lambda x: {
                        'weight': 2.5,
                        'fillOpacity': 0.55
                    },
                    tooltip=folium.Tooltip(
                        f"""<div style="font-family: Arial; font-size: 16px; padding: 10px;">
                            <b style="font-size: 18px;">{row['province_name']}</b><br>
                            <hr style="margin: 6px 0; border: 0; border-top: 1px solid #ccc;">
                            <b>Rischio:</b> {row['risk_score']:.2f} (Livello {int(row['risk_level'])} - {row['risk_label']})<br>
                            <div style="margin: 4px 0; font-size: 13px; color: #555; font-style: italic;">
                                {get_description_from_score(row['risk_score'])}
                            </div>
                            <hr style="margin: 6px 0; border: 0; border-top: 1px solid #ccc;">
                            🍇 BBCH: {int(row['bbch_code'])} | 🎯 Susc: {row['plant_susceptibility']:.2f}<br>
                            🌡️ {row['temp']:.1f}°C | 🌧️ {row['prec']:.1f} mm |
                            💧 {row['rh']:.0f}% | 🍃 {row['lw']:.0f} ore
                        </div>""",
                        sticky=True
                    ),
                    popup=folium.Popup(
                        create_popup_html(row),
                        max_width=400
                    )
                )
                geojson.add_to(fg)

                centroid = row['geometry'].centroid
                label = folium.Marker(
                    location=[centroid.y, centroid.x],
                    icon=folium.DivIcon(html=f"""
                        <div class="risk-label" style="
                                    font-weight: bold;
                                    color: white;
                                    text-shadow:
                                        -2px -2px 0 #000,
                                        2px -2px 0 #000,
                                        -2px 2px 0 #000,
                                        2px 2px 0 #000,
                                        -2px 0 0 #000,
                                        2px 0 0 #000,
                                        0 -2px 0 #000,
                                        0 2px 0 #000;
                                    text-align: center;
                                    white-space: nowrap;">
                            {row['risk_score']:.1f}
                        </div>
                    """)
                )
                label.add_to(fg)

        fg.add_to(m)

    # Aggiungi LayerControl nascosto (per il JavaScript)
    folium.LayerControl(position='topright', collapsed=True).add_to(m)

    # Aggiungi legenda
    m.get_root().html.add_child(folium.Element(create_legend_html()))

    # Get forecast date from first available lead
    first_lead = min(all_predictions.keys())
    forecast_date = format_date_italian(all_predictions[first_lead]['forecast_base'].iloc[0])

    # Crea titolo con bottoni di navigazione
    btn_0_dates = week_dates.get(0, "N/A")
    btn_1_dates = week_dates.get(1, "N/A")
    
    title_html = f'''
    <style>
        .leaflet-control-layers {{
            display: none !important;
        }}
        .leaflet-div-icon {{
            background: transparent !important;
            border: none !important;
        }}
    </style>
    
    <div style="position: fixed;
                top: 15px;
                left: 50%;
                transform: translateX(-50%);
                width: auto;
                min-width: 550px;
                max-width: 750px;
                background-color: rgba(255, 255, 255, 0.95);
                border: 3px solid #333;
                border-radius: 12px;
                z-index: 9999;
                padding: 22px 40px;
                text-align: center;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
        <h2 style="margin: 0; color: #2c3e50; font-size: 28px; font-weight: bold;">
            🍇 Modello Previsionale Rischio Peronospora
        </h2>
        <div style="margin-top: 12px; font-size: 18px; color: #555;">
            Previsione del: <b>{forecast_date}</b>
        </div>
        <div style="margin-top: 18px; display: flex; justify-content: center; gap: 15px;">
            <button id="btn_lead_0" onclick="showLead(0)" 
                    style="padding: 14px 24px; font-size: 16px; font-weight: bold; 
                           background-color: #3498db; color: white; border: none; 
                           border-radius: 8px; cursor: pointer; transition: all 0.2s;">
                ◀ {btn_0_dates}
            </button>
            <button id="btn_lead_1" onclick="showLead(1)" 
                    style="padding: 14px 24px; font-size: 16px; font-weight: bold; 
                           background-color: #95a5a6; color: white; border: none; 
                           border-radius: 8px; cursor: pointer; transition: all 0.2s;">
                {btn_1_dates} ▶
            </button>
        </div>
    </div>
    
    <script>
    var currentLead = 0;
    
    function showLead(lead) {{
        currentLead = lead;
        
        var checkboxes = document.querySelectorAll('.leaflet-control-layers-overlays input[type="checkbox"]');
        
        checkboxes.forEach(function(checkbox, index) {{
            var label = checkbox.nextSibling ? checkbox.nextSibling.textContent.trim() : '';
            
            if (label.includes('week_0')) {{
                if (lead === 0 && !checkbox.checked) {{
                    checkbox.click();
                }} else if (lead === 1 && checkbox.checked) {{
                    checkbox.click();
                }}
            }} else if (label.includes('week_1')) {{
                if (lead === 1 && !checkbox.checked) {{
                    checkbox.click();
                }} else if (lead === 0 && checkbox.checked) {{
                    checkbox.click();
                }}
            }}
        }});
        
        var btn0 = document.getElementById('btn_lead_0');
        var btn1 = document.getElementById('btn_lead_1');
        
        if (lead === 0) {{
            btn0.style.backgroundColor = '#3498db';
            btn1.style.backgroundColor = '#95a5a6';
        }} else {{
            btn0.style.backgroundColor = '#95a5a6';
            btn1.style.backgroundColor = '#3498db';
        }}
    }}
    
    document.addEventListener('DOMContentLoaded', function() {{
        setTimeout(function() {{
            showLead(0);
        }}, 300);
    }});
    </script>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    plugins.Fullscreen(
        position='bottomright',
        title='Espandi mappa',
        title_cancel='Esci da schermo intero',
        force_separate_button=True
    ).add_to(m)

    # Fit bounds to Emilia-Romagna as default view
    er_provinces = [
        "Bologna", "Ferrara", "Forlì-Cesena", "Modena", "Parma",
        "Piacenza", "Ravenna", "Reggio nell'Emilia", "Rimini"
    ]
    gdf_er = gdf[gdf['province_name'].isin(er_provinces)]
    if len(gdf_er) > 0:
        bounds = gdf_er.total_bounds
    else:
        bounds = gdf.total_bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    zoom_scale_js = folium.Element('''
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        // Wait for the map to be available
        var checkMap = setInterval(function() {
            var mapEl = document.querySelector('.folium-map');
            if (!mapEl || !mapEl._leaflet_id) return;
            clearInterval(checkMap);

            var mapObj = null;
            for (var key in window) {
                if (window[key] instanceof L.Map) { mapObj = window[key]; break; }
            }
            if (!mapObj) return;

            function updateLabelSizes() {
                var zoom = mapObj.getZoom();
                // Scale: at zoom 6 (all Italy) -> 10px, zoom 8 (ER) -> 16px, zoom 10+ -> 22px
                var size = Math.max(8, Math.min(26, 3 * zoom - 8));
                var shadow = Math.max(1, Math.round(size / 8));
                var labels = document.querySelectorAll('.risk-label');
                labels.forEach(function(el) {
                    el.style.fontSize = size + 'px';
                    el.style.textShadow =
                        '-'+shadow+'px -'+shadow+'px 0 #000,' +
                        shadow+'px -'+shadow+'px 0 #000,' +
                        '-'+shadow+'px '+shadow+'px 0 #000,' +
                        shadow+'px '+shadow+'px 0 #000,' +
                        '-'+shadow+'px 0 0 #000,' +
                        shadow+'px 0 0 #000,' +
                        '0 -'+shadow+'px 0 #000,' +
                        '0 '+shadow+'px 0 #000';
                });
            }

            mapObj.on('zoomend', updateLabelSizes);
            // Initial call
            updateLabelSizes();
        }, 200);
    });
    </script>
    ''')
    m.get_root().html.add_child(zoom_scale_js)

    m.save(output_file)
    print(f"  Satellite map saved to: {output_file}")

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
    print("PERONOSPORA RISK MAP - ITALIA")
    print("="*70)

    print("\n1. Loading predictions...")
    all_predictions = load_all_predictions(args.predictions_dir)

    if len(all_predictions) == 0:
        print("  No predictions found!")
        return

    for lead, pred in all_predictions.items():
        print(f"   Lead {lead}: {len(pred)} provinces")

    print("\n2. Loading shapefile...")
    gdf = load_italy_shapefile()
    print(f"   {len(gdf)} provinces")

    print("\n3. Creating map...")
    create_satellite_map_all_weeks(all_predictions, gdf, output_file=args.output)

    print("\n" + "="*70)
    print(f"  Map saved to '{args.output}'")
    print("="*70)


if __name__ == '__main__':
    main()
