"""Aggiornamento dei dati AGREA e delle zone semi-naturali sul volume runtime.

Gemello dello `scheduler.py` di peronospora, con una differenza: peronospora
scarica ogni giorno i GRIB di ECMWF, questo scarica UNA VOLTA L'ANNO gli archivi
AGREA, perche' AGREA pubblica una campagna per anno. Per questo non c'e' nessuno
scheduler: si invoca a mano o come passo di avvio del container.

    python updater.pex --check        stato di cio' che c'e' sul volume
    python updater.pex --run-now      scarica e prepara solo se serve
    python updater.pex --run-now --force   rigenera anche se e' tutto a posto
    python updater.pex --run-now --provinces FE,RA   solo alcune province
    python updater.pex --run-now --only seminaturale   solo le zone semi-naturali

Dopo AGREA prepara le zone semi-naturali (modules/seminaturale_prepare.py): Carta forestale,
Uso del suolo e Copernicus ritagliati fuori da AGREA. Anche questo passo e' idempotente e si
rifa' da solo quando AGREA o una fonte cambiano. Picco di memoria ~4 GB, una volta l'anno.

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
from landscape.modules import agrea_prepare, config, seminaturale_prepare

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
    parser.add_argument(
        "--only",
        choices=("agrea", "seminaturale"),
        default="",
        help="esegue un solo passo (predefinito: AGREA e poi le zone semi-naturali)",
    )
    parser.add_argument(
        "--from-dir-seminaturale",
        type=str,
        default="",
        help="archivi della Carta forestale e dell'Uso del suolo gia' su disco (sviluppo)",
    )
    args = parser.parse_args()

    if args.check or not args.run_now:
        stato = agrea_prepare.stato(args.year)
        print(json.dumps(stato, indent=2, ensure_ascii=False))
        print(
            json.dumps(
                {"seminaturale": seminaturale_prepare.stato()},
                indent=2,
                ensure_ascii=False,
            )
        )
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
    codice = 0
    if args.only in ("", "agrea"):
        try:
            esito = agrea_prepare.aggiorna(
                anno=args.year,
                province=province,
                force=args.force,
                da_cartella=args.from_dir or None,
                log=logger.info,
            )
            logger.info("esito AGREA: %s", json.dumps(esito, ensure_ascii=False))
        except Exception as exc:  # pragma: no cover - dipende dalla rete
            # Un fallimento qui non deve impedire l'avvio del servizio: i dati vecchi
            # restano validi e in loro assenza si serve iColt.
            logger.error("aggiornamento AGREA fallito: %s", exc)
            codice = 1

    # Le zone semi-naturali dipendono da AGREA (il ritaglio): si provano comunque, perche' con i
    # file AGREA vecchi ancora validi il ritaglio resta coerente; senza AGREA il passo si salta.
    if args.only in ("", "seminaturale") and not province:
        try:
            esito = seminaturale_prepare.aggiorna(
                force=args.force,
                da_cartella=args.from_dir_seminaturale or None,
                log=logger.info,
            )
            logger.info(
                "esito semi-naturale: %s",
                json.dumps(
                    {k: esito.get(k) for k in ("aggiornato", "motivo", "secondi")}
                ),
            )
        except Exception as exc:  # pragma: no cover - dipende dalla rete
            # I file vecchi restano validi; in loro assenza il semi-naturale e' il solo AGREA.
            logger.error("aggiornamento zone semi-naturali fallito: %s", exc)
            codice = 1
    return codice


if __name__ == "__main__":
    sys.exit(main())
