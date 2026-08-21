"""Aggiornamento dei dati AGREA sul volume runtime.

Gemello dello `scheduler.py` di peronospora, con una differenza: peronospora
scarica ogni giorno i GRIB di ECMWF, questo scarica UNA VOLTA L'ANNO gli archivi
AGREA, perche' AGREA pubblica una campagna per anno. Per questo non c'e' nessuno
scheduler: si invoca a mano o come passo di avvio del container.

    python updater.pex --check        stato di cio' che c'e' sul volume
    python updater.pex --run-now      scarica e prepara solo se serve
    python updater.pex --run-now --force   rigenera anche se e' tutto a posto
    python updater.pex --run-now --provinces FE,RA   solo alcune province

E' IDEMPOTENTE: se i file ci sono e gli ETag remoti combaciano con quelli
registrati, non fa nulla. Si puo' quindi invocare a ogni avvio senza costo.

Se non gira mai, il servizio funziona sul solo iColt: nessuna pagina si rompe.
Serve pero' spazio temporaneo sul volume durante l'esecuzione, perche' gli
archivi si scaricano una provincia alla volta e si buttano subito dopo averla
convertita.
"""

import argparse
import json
import logging
import sys

from landscape import paths
from landscape.modules import agrea_prepare, config

logger = logging.getLogger("landscape_updater")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggiorna i dati AGREA nel volume runtime di landscape."
    )
    parser.add_argument("--run-now", action="store_true", help="esegue l'aggiornamento")
    parser.add_argument("--check", action="store_true", help="mostra soltanto lo stato")
    parser.add_argument(
        "--force", action="store_true", help="rigenera anche se non serve"
    )
    parser.add_argument("--year", type=int, default=config.AGREA_YEAR)
    parser.add_argument(
        "--from-dir",
        type=str,
        default="",
        help="usa archivi zip gia' su disco invece di scaricarli (sviluppo)",
    )
    parser.add_argument(
        "--provinces",
        type=str,
        default="",
        help="elenco separato da virgole, per prove (es. FE,RA)",
    )
    args = parser.parse_args()

    if args.check or not args.run_now:
        stato = agrea_prepare.stato(args.year)
        print(json.dumps(stato, indent=2, ensure_ascii=False))
        print(f"\nvolume: {paths.AGREA_DIR}")
        if not (stato["colture"] and stato["parcelle"] and stato["elementi"]):
            print(
                "i dati AGREA non sono presenti: il servizio funziona sul solo iColt.\n"
                "per prepararli: updater.pex --run-now"
            )
        return 0

    province = [
        p.strip().upper() for p in args.provinces.split(",") if p.strip()
    ] or None
    try:
        esito = agrea_prepare.aggiorna(
            anno=args.year,
            province=province,
            force=args.force,
            da_cartella=args.from_dir or None,
            log=logger.info,
        )
    except Exception as exc:  # pragma: no cover - dipende dalla rete
        # Un fallimento qui non deve impedire l'avvio del servizio: i dati vecchi
        # restano validi e in loro assenza si serve iColt.
        logger.error("aggiornamento AGREA fallito: %s", exc)
        return 1

    logger.info("esito: %s", json.dumps(esito, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
