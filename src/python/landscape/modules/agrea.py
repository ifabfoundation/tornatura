"""Sorgente AGREA: i piani colturali dichiarati dalle aziende agricole.

E' la SECONDA sorgente del servizio, accanto a iColt, e ha una natura diversa che
va tenuta presente in ogni affermazione:

  iColt  = osservazione satellitare invernale, nessun bias dichiarativo, soglia
           0,5 ha, copre la PIANURA e praticamente nulla sopra i 200 m di quota.
  AGREA  = dichiarazione amministrativa per la PAC. Copre la collina, contiene
           bosco ed elementi caratteristici del paesaggio, nomina le specie, ma
           esiste solo per le aziende che presentano il piano colturale — e la
           documentazione ARPAE avverte che "non tutte le aziende agricole hanno
           l'obbligo di presentare tale dichiarazione".

Misure che giustificano le scelte di questo modulo:
  - AGREA copre piu' di iColt in 21 punti di prova su 24; iColt e' cieca (sotto il
    5% del cerchio) sopra i 200 m di quota o il 15% di pendenza.
  - Aderenza alle statistiche ufficiali: AGREA 97,6% della SAU censita, iColt
    74,1%; vite entro 0,4-5,9% contro -22/-26%.
  - L'89% di iColt e' contenuto in AGREA, ma il 51% di AGREA e' fuori da iColt.
    In pianura sono ridondanti (IoU 0,77), in collina c'e' solo AGREA (IoU 0,07).
  - L'accordo geometrico particella per particella e' circa l'80%, non il 100%:
    in pianura, dove esistono entrambe, quel disaccordo e' l'unica stima onesta
    dell'incertezza da mostrare all'utente.

I dati si leggono PER FINESTRA dal GeoParquet 1.1 con colonna bbox di copertura,
non dalla cache in memoria: misurato 423-865 MB di RSS contro 5.983 MB, a parita'
di latenza e senza avvio a freddo di 6 secondi.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

import geopandas as gpd
import shapely
from landscape import paths
from landscape.modules import config
from shapely.geometry import Point


class AgreaUnavailable(RuntimeError):
    """I file AGREA non sono sul volume: il servizio continua sul solo iColt."""


# Specie dichiarata -> codice del registro colture di tornatura. E' l'inverso di
# HARVEST_TO_AGREA_SPECIES, calcolato una volta perche' serve a ogni feature.
SPECIE_A_HARVEST = {
    sp: code
    for code, insieme in config.HARVEST_TO_AGREA_SPECIES.items()
    for sp in insieme
}


def display_name(specie: str) -> str:
    """Nome leggibile della specie. Solo presentazione, 1:1, senza accorpare.

    `capitalize` e non `title`: AGREA scrive tutto in maiuscolo e `title`
    produrrebbe "Erba Medica" e "Ortive A Pieno Campo".
    """
    esplicito = config.AGREA_DISPLAY_NAME.get(specie)
    if esplicito:
        return esplicito
    return specie[:1].upper() + specie[1:].lower() if specie else specie


def available() -> bool:
    return paths.AGREA_COLTURE_PARQUET.exists()


def elements_available() -> bool:
    return paths.AGREA_ELEMENTI_PARQUET.exists()


def pieces_available() -> bool:
    """Il layer fine c'e'? Se no il disegno del campo resta quello a mano."""
    return paths.AGREA_PARCELLE_PARQUET.exists()


def _buffer(lat: float, lng: float, radius_m: float):
    """Buffer in metri e in gradi, piu' il suo bbox: il bbox serve alla lettura."""
    centro = gpd.GeoSeries([Point(lng, lat)], crs=4326).to_crs(config.METRIC_EPSG)
    metrico = centro.buffer(radius_m).iloc[0]
    geografico = gpd.GeoSeries([metrico], crs=config.METRIC_EPSG).to_crs(4326).iloc[0]
    return metrico, geografico, geografico.bounds


def _leggi(path, bbox: Tuple[float, float, float, float]) -> gpd.GeoDataFrame:
    if not path.exists():
        raise AgreaUnavailable(f"file non presente: {path}")
    return gpd.read_parquet(path, bbox=bbox)


def parcels(
    lat: float, lng: float, radius_m: float, harvest: Optional[str] = None
) -> gpd.GeoDataFrame:
    """Appezzamenti dichiarati dentro il buffer, con la geometria RITAGLIATA.

    Ritagliata perche' gli ettari dichiarati devono coincidere con la superficie
    disegnata: una particella a cavallo del bordo contribuisce solo per la parte
    interna.
    """
    metrico, geografico, bbox = _buffer(lat, lng, radius_m)
    g = _leggi(paths.AGREA_COLTURE_PARQUET, bbox)
    if g.empty:
        g["ha_in_buffer"] = []
        return g

    metriche = g.geometry.to_crs(config.METRIC_EPSG).make_valid()
    ritagliate = metriche.intersection(metrico)
    g["ha_in_buffer"] = ritagliate.area / 10_000
    g = g.set_geometry(
        gpd.GeoSeries(ritagliate.values, index=g.index, crs=config.METRIC_EPSG).to_crs(
            4326
        )
    )
    g = g[g["ha_in_buffer"] > 0.001]

    specie_utente = config.HARVEST_TO_AGREA_SPECIES.get((harvest or "").strip(), set())
    g["is_crop"] = g["cls"].isin(specie_utente) if specie_utente else False
    return g


def seminatural(lat: float, lng: float, radius_m: float) -> Dict[str, Any]:
    """Quota di elementi semi-naturali nel buffer: bosco piu' siepi e margini.

    E' la variabile che la letteratura indica come driver per Halyomorpha halys
    (Tamherini et al. 2023, scala migliore 3 km) e per Drosophila suzukii
    (Santoiemma et al. 2018), e che iColt non contiene affatto.

    Gli elementi caratteristici sono 902.542 poligoni regionali per il 2,5% degli
    ettari: si conservano come CENTROIDE piu' superficie e si contano per
    appartenenza del centroide al buffer. Misurato lo scarto contro il ritaglio
    esatto: 0,0-2,0%, su elementi con mediana 166 m2. Non si servono mai come
    geometria al client.
    """
    metrico, geografico, bbox = _buffer(lat, lng, radius_m)
    buffer_ha = metrico.area / 10_000

    bosco_ha = 0.0
    if available():
        g = _leggi(paths.AGREA_COLTURE_PARQUET, bbox)
        b = g[g["cls"].str.upper() == "BOSCO"]
        if not b.empty:
            metriche = b.geometry.to_crs(config.METRIC_EPSG).make_valid()
            bosco_ha = float(metriche.intersection(metrico).area.sum() / 10_000)

    elementi_ha = 0.0
    elementi_n = 0
    if elements_available():
        e = _leggi(paths.AGREA_ELEMENTI_PARQUET, bbox)
        if not e.empty:
            dentro = e[e.geometry.to_crs(config.METRIC_EPSG).within(metrico)]
            elementi_ha = float(dentro["ha"].sum())
            elementi_n = int(len(dentro))

    totale = bosco_ha + elementi_ha
    return {
        "bosco_ha": round(bosco_ha, 1),
        "elementi_ha": round(elementi_ha, 1),
        "elementi_n": elementi_n,
        "ha": round(totale, 1),
        "pct_of_buffer": round(100 * totale / buffer_ha, 1) if buffer_ha else 0.0,
        # L'approssimazione va dichiarata dove viene usata, non nascosta.
        "elementi_method": "centroide nel buffer (scarto misurato 0-2%)",
    }


def composition(
    lat: float, lng: float, radius_m: float, harvest: Optional[str] = None
) -> Dict[str, Any]:
    """Composizione colturale dichiarata, nella stessa forma di quella iColt."""
    g = parcels(lat, lng, radius_m, harvest)
    metrico, _, _ = _buffer(lat, lng, radius_m)
    buffer_ha = metrico.area / 10_000

    # Il denominatore e' la superficie AGRICOLA dichiarata: il bosco e' copertura
    # del suolo, non coltura, e va tenuto fuori dalle percentuali colturali.
    agricole = g[g["is_crop_class"]] if "is_crop_class" in g.columns else g
    agri_ha = float(agricole["ha_in_buffer"].sum()) if not agricole.empty else 0.0

    breakdown: List[Dict[str, Any]] = []
    if not agricole.empty:
        grouped = (
            agricole.groupby("cls")
            .agg(ha=("ha_in_buffer", "sum"), parcels=("ha_in_buffer", "size"))
            .sort_values("ha", ascending=False)
        )
        famiglie = (
            agricole.groupby("cls")["family"].first().to_dict()
            if "family" in agricole.columns
            else {}
        )
        residuo_ha = 0.0
        residuo_classi = 0
        for cls, row in grouped.iterrows():
            n = int(row["parcels"])
            ha = float(row["ha"])
            if n < config.MIN_PARCELS_PER_ROW:
                residuo_ha += ha
                residuo_classi += 1
                continue
            breakdown.append(
                {
                    "icolt_class": display_name(str(cls)),
                    "declared": str(cls),
                    "family": famiglie.get(str(cls), config.FAMILY_OTHER),
                    "ha": round(ha, 1),
                    "pct": round(100 * ha / agri_ha, 1) if agri_ha else 0.0,
                    "parcels": n,
                }
            )
        if residuo_ha > 0:
            breakdown.append(
                {
                    "icolt_class": config.OTHER_ROW_LABEL,
                    "family": config.FAMILY_OTHER,
                    "ha": round(residuo_ha, 1),
                    "pct": round(100 * residuo_ha / agri_ha, 1) if agri_ha else 0.0,
                    "parcels": None,
                    "merged_classes": residuo_classi,
                }
            )

    crop = resolve_crop(harvest)
    if crop is not None:
        if crop["mappable"] and agri_ha > 0:
            specie_utente = set(crop.get("agrea_species") or [])
            crop_ha = float(
                agricole.loc[agricole["cls"].isin(specie_utente), "ha_in_buffer"].sum()
            )
            crop["ha"] = round(crop_ha, 1)
            crop["pct_of_agri"] = round(100 * crop_ha / agri_ha, 1)
            crop["has_area"] = crop_ha > 0
        else:
            crop["ha"] = None
            crop["pct_of_agri"] = None
            crop["has_area"] = False

    return {
        "source": "AGREA piani colturali grafici",
        "year": config.AGREA_YEAR,
        "buffer_ha": round(buffer_ha, 1),
        "mapped_ha": round(float(g["ha_in_buffer"].sum()), 1) if not g.empty else 0.0,
        "agri_ha": round(agri_ha, 1),
        "mapped_pct_of_buffer": round(
            100 * float(g["ha_in_buffer"].sum()) / buffer_ha, 1
        )
        if buffer_ha and not g.empty
        else 0.0,
        "parcels": int(len(agricole)),
        "crop": crop,
        "composition": breakdown,
    }


def resolve_crop(harvest: Optional[str]) -> Optional[Dict[str, Any]]:
    """Coltura di tornatura -> specie AGREA dichiarate.

    Tutte e otto le colture di tornatura hanno una specie propria nel dato: qui
    NON esiste il caso "non distinguibile" che iColt ha per mais, barbabietola e
    albicocco. Resta solo il caso in cui il codice coltura del campo non e' fra
    gli otto del registro (codici legacy), che si dichiara come tale.
    """
    if not harvest:
        return None
    code = harvest.strip()
    specie_set = config.HARVEST_TO_AGREA_SPECIES.get(code)
    if specie_set:
        principale = sorted(specie_set)[0]
        return {
            "harvest": code,
            "agrea_species": sorted(specie_set),
            "icolt_class": display_name(principale),
            "mappable": True,
            "reason": None,
        }
    return {
        "harvest": code,
        "agrea_species": [],
        "icolt_class": None,
        "mappable": False,
        "reason": config.REASON_UNKNOWN,
    }


def parcels_geojson(
    lat: float, lng: float, radius_m: float, harvest: Optional[str] = None
) -> Dict[str, Any]:
    """Geometrie dichiarate per il disegno sulla mappa."""
    g = parcels(lat, lng, radius_m, harvest)
    features: List[Dict[str, Any]] = []
    truncated = False
    disegnati_ha = 0.0
    totale_ha = float(g["ha_in_buffer"].sum()) if not g.empty else 0.0
    if not g.empty:
        # Soglia di disegno: i poligoni minuscoli non si vedono sulla mappa ma
        # pesano. I numeri restano calcolati su tutto.
        g = g[g["ha_in_buffer"] >= config.AGREA_MAP_MIN_HA]
        disegnati_ha = float(g["ha_in_buffer"].sum()) if not g.empty else 0.0
        out = g.sort_values("ha_in_buffer", ascending=False)
        if len(out) > config.MAX_PARCELS:
            out = out.head(config.MAX_PARCELS)
            truncated = True
        # `harvest_code` permette al client di riconoscere la coltura del campo
        # dell'utente senza una seconda chiamata. Si ripete per feature ma e' una
        # stringa corta e gzip la comprime bene.
        out = out.assign(
            icolt_class=out["cls"].map(display_name),
            harvest_code=out["cls"].map(SPECIE_A_HARVEST),
            ha=out["ha_in_buffer"].round(2),
        )[
            [
                "icolt_class",
                "harvest_code",
                "family",
                "ha",
                "is_crop",
                "geometry",
            ]
        ]
        features = json.loads(out.to_json(drop_id=True))["features"]
    return {
        "count": len(features),
        "truncated": truncated,
        "map_min_ha": config.AGREA_MAP_MIN_HA,
        "map_pct_of_area": round(100 * disegnati_ha / totale_ha, 1)
        if totale_ha
        else 0.0,
        "parcels": {"type": "FeatureCollection", "features": features},
    }


def _coordinate_arrotondate(nodo: Any, decimali: int) -> Any:
    """Arrotonda una struttura di coordinate GeoJSON, in profondita'.

    Riceve il valore di `coordinates`, cioe' liste annidate di float fino a
    qualsiasi profondita' (punto, anello, poligono, multipoligono).

    Si fa sulla RISPOSTA e non sul file: il file resta a precisione piena, perche'
    e' da lui che si ricava il confine da salvare. L'arrotondamento e'
    deterministico per coordinata, quindi due vertici identici in ingresso restano
    identici in uscita e i bordi condivisi non si aprono.
    """
    if isinstance(nodo, list):
        return [_coordinate_arrotondate(x, decimali) for x in nodo]
    return round(nodo, decimali) if isinstance(nodo, float) else nodo


def pieces_geojson(lat: float, lng: float, radius_m: float) -> Dict[str, Any]:
    """I pezzi selezionabili, per disegnare un campo nuovo scegliendoli.

    Due differenze sostanziali rispetto a `parcels_geojson`, che serve la pagina
    del paesaggio:

    1. **Le geometrie NON sono ritagliate sul buffer.** La' il ritaglio e'
       giusto, perche' gli ettari dichiarati devono coincidere con la superficie
       disegnata. Qui sarebbe un danno: un campo a cavallo del bordo della vista
       verrebbe troncato, e l'utente accetterebbe come confine del proprio campo
       una linea che e' solo il bordo della finestra. Si restituisce il pezzo
       INTERO appena tocca la finestra.
    2. **Nessun accorpamento per anonimato.** Sulla pagina del paesaggio le
       classi con meno di tre appezzamenti si accorpano, perche' una riga con un
       appezzamento e' il campo di un'azienda riconoscibile. Qui la geometria
       serve proprio a scegliere un singolo pezzo, e chi disegna il proprio campo
       lo sta gia' guardando dalla foto satellitare: nascondere il confine non
       proteggerebbe nulla e renderebbe la funzione inutile.

    `ha` e' la superficie del pezzo calcolata in UTM 32N in preparazione: il
    client NON deve ricalcolarla dal poligono ricevuto.
    """
    if not pieces_available():
        raise AgreaUnavailable("layer fine non presente sul volume")

    _, _, bbox = _buffer(lat, lng, radius_m)
    g = _leggi(paths.AGREA_PARCELLE_PARQUET, bbox)
    truncated = False
    soglia_effettiva = config.AGREA_PIECE_MIN_HA
    features: List[Dict[str, Any]] = []
    if not g.empty:
        # Tetto sui VERTICI, tenendo i pezzi piu' grandi: a vista larga i piccoli
        # non sono cliccabili comunque, e il peso della risposta e' proporzionale
        # ai vertici e non al numero di pezzi.
        g = g.sort_values("ha", ascending=False)
        # `get_num_coordinates` restituisce un array, e cumsum/all/any sono suoi
        # metodi: si evita di dipendere da numpy, che nel resolve arriva solo di
        # rimbalzo da pandas e che Pants non sa attribuire.
        cumulati = shapely.get_num_coordinates(g.geometry.values).cumsum()
        entro = cumulati <= config.AGREA_PIECES_VERTEX_BUDGET
        if not entro.all():
            # Almeno un pezzo si serve sempre, anche se da solo sfonda il tetto.
            if not entro.any():
                entro[0] = True
            g = g[entro]
            truncated = True
            soglia_effettiva = round(float(g["ha"].min()), 2)
        out = g.assign(
            crop=g["cls"].map(display_name),
            harvest_code=g["cls"].map(SPECIE_A_HARVEST),
            ha=g["ha"].round(2),
        )[
            [
                "pid",
                "app_id",
                "app_n",
                "crop",
                "harvest_code",
                "family",
                "ha",
                "is_crop_class",
                "geometry",
            ]
        ]
        features = json.loads(out.to_json(drop_id=True))["features"]
        for f in features:
            f["geometry"]["coordinates"] = _coordinate_arrotondate(
                f["geometry"]["coordinates"], config.AGREA_PIECES_COORD_DECIMALS
            )

    return {
        "source": config.AGREA_SOURCE,
        "year": config.AGREA_YEAR,
        "count": len(features),
        # `truncated` vero significa che a questa larghezza di vista i pezzi piu'
        # piccoli non sono serviti, e `piece_min_ha` dice da quale misura si parte.
        "truncated": truncated,
        "piece_min_ha": soglia_effettiva,
        "coord_decimals": config.AGREA_PIECES_COORD_DECIMALS,
        "pieces": {"type": "FeatureCollection", "features": features},
    }


def parcel_at(lat: float, lng: float) -> Dict[str, Any]:
    """L'appezzamento dichiarato che contiene il punto, per suggerirne il confine.

    Serve al disegno di un campo nuovo: invece di far tracciare il poligono a
    mano, si propone il confine vero. Il dato preparato e' dissolto per
    appezzamento (AGREA spezza i campi sulle particelle catastali), quindi qui si
    restituisce il CAMPO e non un frammento: mediana 1,37 ha contro 0,32.

    Cosa si restituisce e cosa NO. La geometria e' un confine catastale, cioe'
    informazione gia' pubblica, e la coltura e' la stessa classe che la mappa del
    paesaggio mostra al click. Non si restituisce nulla del dettaglio aziendale
    (varieta', numero di piante, anno di impianto, densita', irrigazione,
    biologico): chi registra il proprio campo quei dati li conosce, chi registra
    il campo di un altro non deve leggerli da noi.

    Limiti da dichiarare a chi usa la risposta:
      - la geometria e' semplificata a 1 m (differenza di forma 0,4% dell'area sul
        poligono mediano, fino al 7,8% nel caso peggiore);
      - il posizionamento assoluto dipende dalla trasformazione Monte Mario ->
        WGS 84, la cui migliore versione disponibile dichiara 4 m di accuratezza;
      - esiste solo dove l'azienda presenta il piano colturale, e il 36% degli
        appezzamenti sta sotto 0,5 ha.
    """
    if not available():
        raise AgreaUnavailable("dati AGREA non presenti sul volume")

    punto = Point(lng, lat)
    # Finestra minima intorno al punto: la lettura per bbox non accetta un punto.
    d = 0.002  # ~200 m, abbondante per contenere l'appezzamento piu' grande
    g = _leggi(paths.AGREA_COLTURE_PARQUET, (lng - d, lat - d, lng + d, lat + d))
    if g.empty:
        return {"found": False, "reason": "nessun appezzamento dichiarato qui"}

    dentro = g[g.geometry.contains(punto)]
    if dentro.empty:
        return {"found": False, "reason": "nessun appezzamento dichiarato qui"}

    # Se il punto cade in piu' poligoni sovrapposti si prende il piu' piccolo: e'
    # il piu' specifico, e in AGREA le sovrapposizioni esistono.
    metrico = dentro.geometry.to_crs(config.METRIC_EPSG)
    r = dentro.loc[metrico.area.idxmin()]
    geom_metrico = metrico.loc[metrico.area.idxmin()]

    specie_dichiarata = str(r["cls"])
    harvest = None
    for codice, specie_set in config.HARVEST_TO_AGREA_SPECIES.items():
        if specie_dichiarata in specie_set:
            harvest = codice
            break

    return {
        "found": True,
        "source": config.AGREA_SOURCE,
        "year": config.AGREA_YEAR,
        "geometry": json.loads(gpd.GeoSeries([r["geometry"]], crs=4326).to_json())[
            "features"
        ][0]["geometry"],
        # Superficie calcolata in UTM 32N sulla geometria servita: e' il numero
        # che il frontend deve usare, senza ricalcolarlo dal poligono ricevuto.
        "ha": round(float(geom_metrico.area / 10_000), 2),
        "crop": {
            "declared": specie_dichiarata,
            "display": display_name(specie_dichiarata),
            # Codice del registro colture di tornatura, quando la specie vi
            # corrisponde: e' cio' che il form puo' preselezionare.
            "harvest_code": harvest,
        },
        "is_crop_class": bool(r.get("is_crop_class", True)),
        "precision": {
            "simplified_m": config.AGREA_SIMPLIFY_M,
            "datum_accuracy_m": config.AGREA_DATUM_ACCURACY_M,
            "note": (
                "Confine dichiarato per la PAC e ritagliato sul catasto. La forma "
                "e' semplificata a 1 m e il posizionamento assoluto ha "
                "un'incertezza dichiarata di 4 m: da confermare guardando la foto."
            ),
        },
    }
