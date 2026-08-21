import logging
import os
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from landscape.modules import agrea, config
from landscape.modules import landscape as landscape_service
from landscape.modules.landscape import DatasetUnavailable

logger = logging.getLogger("landscape_api")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

app = FastAPI(title="Landscape API", version="1.0.0")

# Le geometrie delle particelle pesano ~0,7 MB grezzi e ~0,2 MB compressi:
# la compressione qui e' quello che rende l'endpoint /parcels usabile da mobile.
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/v1/landscape/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/landscape/coverage")
def coverage() -> Dict[str, Any]:
    """Copertura e contenuto del dataset.

    Il frontend la usa per sapere se mostrare la funzione per un dato campo.
    """
    try:
        return landscape_service.coverage()
    except DatasetUnavailable as exc:
        logger.error("dataset unavailable: %s", exc)
        raise HTTPException(status_code=500, detail="Landscape dataset not available")


@app.get("/v1/landscape/composition")
def composition_by_location(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_m: int = Query(
        config.DEFAULT_RADIUS_M, ge=config.MIN_RADIUS_M, le=config.MAX_RADIUS_M
    ),
    crop: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Composizione colturale del paesaggio intorno a un punto.

    `crop` e' il codice coltura di tornatura (HarvestType.code). Quando la
    coltura non e' distinguibile nel dataset la risposta lo dichiara invece di
    restituire un valore fuorviante.
    """
    try:
        if not landscape_service.is_covered(lat, lng):
            raise HTTPException(
                status_code=404, detail="Location outside data coverage"
            )
        return landscape_service.composition_with_sources(lat, lng, radius_m, crop)
    except DatasetUnavailable as exc:
        logger.error("dataset unavailable: %s", exc)
        raise HTTPException(status_code=500, detail="Landscape dataset not available")


@app.get("/v1/landscape/parcels")
def parcels_by_location(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_m: int = Query(
        config.DEFAULT_RADIUS_M, ge=config.MIN_RADIUS_M, le=config.MAX_GEOMETRY_RADIUS_M
    ),
    crop: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Geometrie delle particelle nel buffer, per il disegno sulla mappa.

    Restituisce le particelle RITAGLIATE sul buffer (quindi la superficie
    disegnata coincide con quella dichiarata da /composition), il poligono del
    buffer stesso e l'elenco delle classi collettive, che l'interfaccia deve
    nominare come tali invece di spacciarle per una singola coltura.
    """
    try:
        if not landscape_service.is_covered(lat, lng):
            raise HTTPException(
                status_code=404, detail="Location outside data coverage"
            )
        # AGREA guida quando i file sono sul volume: copre la collina, nomina
        # le specie e contiene bosco ed elementi del paesaggio. Sopra il suo
        # raggio massimo, o se manca, si ricade su iColt senza rompersi.
        if agrea.available() and radius_m <= config.AGREA_MAX_GEOMETRY_RADIUS_M:
            try:
                geo = agrea.parcels_geojson(lat, lng, radius_m, crop)
                if geo["count"] > 0:
                    base = landscape_service.parcels_geojson(lat, lng, radius_m, crop)
                    base.update(geo)
                    base["source"] = "agrea"
                    base["dataset"] = {
                        "source": config.AGREA_SOURCE,
                        "year": config.AGREA_YEAR,
                        "region": config.COVERAGE_REGION,
                    }
                    # Con AGREA non esistono classi collettive: ogni specie ha
                    # la sua riga, quindi non c'e' nulla da dichiarare come
                    # "contiene anche altre colture".
                    base["aggregated_classes"] = {}
                    base["crop"] = agrea.resolve_crop(crop)
                    return base
            except agrea.AgreaUnavailable as exc:
                logger.warning("agrea non disponibile: %s", exc)
        out = landscape_service.parcels_geojson(lat, lng, radius_m, crop)
        out["source"] = "icolt"
        return out
    except DatasetUnavailable as exc:
        logger.error("dataset unavailable: %s", exc)
        raise HTTPException(status_code=500, detail="Landscape dataset not available")


@app.get("/v1/landscape/pieces")
def pieces_by_location(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_m: int = Query(
        config.AGREA_PIECES_MAX_RADIUS_M,
        ge=config.MIN_RADIUS_M,
        le=config.AGREA_PIECES_MAX_RADIUS_M,
    ),
) -> Dict[str, Any]:
    """I pezzi dichiarati nella vista, per disegnare un campo scegliendoli.

    E' il livello FINE: il frammento come sta nel dato, cioe' l'appezzamento
    intersecato la particella catastale, senza dissolvere e senza semplificare.
    Serve al disegno del campo, dove il bordo deve essere preciso e chi disegna
    deve poter prendere una porzione invece di tutto il campo dichiarato.
    `/parcels` resta il livello GROSSO, per la pagina del paesaggio.

    Ogni feature porta `app_id`, che dice quali pezzi formano lo stesso campo
    dichiarato, e `app_n`, quanti pezzi ha quel campo in tutto: il client puo'
    cosi' proporre i fratelli e dire quanti ne restano fuori dalla vista.

    La risposta ha un tetto sui VERTICI, non sui pezzi, perche' e' quello a
    determinarne il peso: quando scatta, `truncated` e' vero e `piece_min_ha` dice
    da quale misura si parte a questa larghezza di vista. Si tengono i pezzi piu'
    grandi, che a vista larga sono anche i soli cliccabili.

    Restituisce `count: 0` quando non c'e' nulla da proporre, che NON e' un
    errore: l'azienda potrebbe non presentare il piano colturale, i pezzi
    potrebbero stare sotto la soglia minima, il punto potrebbe cadere fuori dalla
    copertura. Il chiamante deve lasciar disegnare a mano.
    """
    try:
        return agrea.pieces_geojson(lat, lng, radius_m)
    except agrea.AgreaUnavailable as exc:
        logger.info("pezzi non disponibili: %s", exc)
        return {
            "source": config.AGREA_SOURCE,
            "year": config.AGREA_YEAR,
            "count": 0,
            "truncated": False,
            "piece_min_ha": config.AGREA_PIECE_MIN_HA,
            "coord_decimals": config.AGREA_PIECES_COORD_DECIMALS,
            "pieces": {"type": "FeatureCollection", "features": []},
        }


@app.get("/v1/landscape/parcel-at")
def parcel_at_point(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
) -> Dict[str, Any]:
    """L'appezzamento dichiarato che contiene il punto, per suggerirne il confine.

    Pensato per il disegno di un campo nuovo: si propone il confine vero invece di
    farlo tracciare a mano. Restituisce `found: false` quando non c'e' nulla da
    suggerire, che NON e' un errore: l'azienda potrebbe non presentare il piano
    colturale, l'appezzamento potrebbe essere sotto la soglia minima, o il punto
    potrebbe cadere fuori dalla copertura. Il chiamante deve trattarlo come
    "suggerimento non disponibile" e lasciar disegnare a mano.
    """
    try:
        return agrea.parcel_at(lat, lng)
    except agrea.AgreaUnavailable as exc:
        logger.info("suggerimento non disponibile: %s", exc)
        return {"found": False, "reason": "dati dichiarativi non disponibili"}
    except DatasetUnavailable as exc:
        logger.error("dataset unavailable: %s", exc)
        raise HTTPException(status_code=500, detail="Landscape dataset not available")


if __name__ == "__main__":
    host = os.getenv("LANDSCAPE_API_HOST", "0.0.0.0")
    port = int(os.getenv("LANDSCAPE_API_PORT", "8080"))
    uvicorn.run(app, host=host, port=port, log_level="info")
