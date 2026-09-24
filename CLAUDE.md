# Tornatura — monorepo

Applicazione web per il monitoraggio fitosanitario in campo (iFAB Foundation): campi
georeferenziati, rilevamenti standardizzati per coltura e avversita', bollettini regionali
riassunti dall'AI, previsione del rischio peronospora, paesaggio agricolo intorno al campo.
Il repository e' **pubblico**: niente credenziali, niente dati di clienti, niente indirizzi
di macchine. La lingua del codice e dei commenti e' l'italiano; i commenti dicono il *perche'*.

## Mappa

| Percorso | Cos'e' | Dettagli |
|---|---|---|
| `src/python/core/` | API di business (FastAPI + MongoEngine + Keycloak + MinIO) | `src/python/core/CLAUDE.md` |
| `src/typescript/web/` | frontend React/Vite | `src/typescript/web/CLAUDE.md` |
| `src/typescript/coreapis-sdk/`, `src/typescript/libs/` | SDK TypeScript generato dall'OpenAPI del core, impacchettato come tarball versionato | vedi sezione SDK nel CLAUDE.md del web |
| `src/python/bollettini/` | servizio modello: report per coltura dai bollettini fitosanitari (RAG deterministico + LLM) | `src/python/bollettini/CLAUDE.md`, `CHANGELOG.md` |
| `src/python/peronospora/` | servizio modello: rischio settimanale peronospora della vite (octoPus riadattato + XGBoost su ECMWF) | `README.md`, `CHANGELOG.md` |
| `src/python/landscape/` | servizio modello: paesaggio agricolo intorno al campo (AGREA + iColt) e pezzi dichiarati per disegnare i campi | `src/python/landscape/CLAUDE.md`, `CHANGELOG.md` |
| `src/docker/<servizio>/` | Dockerfile e `BUILD` con `repository` e `image_tags` di ogni immagine (`darkform/tornatura.*`) | |
| `src/deployment/` | `docker-compose-dev.yml`: Postgres+Keycloak, Mongo, MinIO per lo sviluppo locale | |
| `3rdparty/python/` | requirements e lockfile Pants, **un resolve per servizio** (`default`, `bollettini`, `peronospora`, `landscape`) | |
| `docs/decisioni/` | una nota per ogni scelta di architettura, con il perche' | `docs/decisioni/README.md` |

I tre servizi modello sono gemelli: FastAPI **senza autenticazione**, chiamati dal frontend sotto lo
stesso origin (`/v1/<servizio>/*`, in produzione un proxy per path li unifica), stato su volume,
immagine propria. `landscape` e' il template piu' recente e completo: un servizio nuovo si fa
copiando quello (struttura del package, `BUILD`, `src/docker/landscape/`, le funzioni in
`web/src/services/model-api.ts` e la pagina `field-landscape.tsx`).

## Build: Pants

- Versione in `pants.toml` (`get-pants.sh` la installa). Se nella shell e' attivo un ambiente conda
  che imposta `LD_LIBRARY_PATH`, lanciare **`env -u LD_LIBRARY_PATH pants …`**, altrimenti i pex
  falliscono in modi oscuri.
- Comandi tipici: `pants tailor --check ::`, `pants lint ::` (black, isort, hadolint),
  `pants package src/python/<servizio>:api` (pex `layout="packed"`: e' una **directory**, si lancia
  con `python …/api.pex`), `pants package src/docker/<servizio>:docker`, `pants run src/python/core:app`.
- Aggiungere una dipendenza: nel `…-requirements.txt` del resolve giusto, poi
  `pants generate-lockfiles --resolve=<nome>` e **committare il lock**. Senza lock nessun `package` parte.
- Nel `COPY` dei Dockerfile il pex si chiama `src.python.<servizio>/api.pex` (Pants sostituisce `/` con `.`).
- I `.env` (core, bollettini, web) sono ignorati da git e **non devono entrare nei pex**
  (`src/python/core/BUILD` spiega perche': contengono segreti).

## Cosa NON c'e', e come si verifica allora

Non ci sono CI ne' test automatici. Prima di aprire una PR:
- **web**: `npm run build` in `src/typescript/web` (= `tsc -b && vite build`). Attenzione: `tsc -p .`
  da solo **non controlla nulla**, il tsconfig radice e' vuoto e rimanda a `tsconfig.app.json`.
- **python**: `pants lint`, `python -m py_compile` sui file toccati, e l'app avviata in locale
  (compose di `src/deployment` + servizi a mano) provando il percorso modificato dal browser.
- **bollettini**: i grader di qualita' vivono fuori dal repo (progetto standalone); una modifica ai
  prompt va valutata li' prima della PR.

## Rilascio

Branch `release/x.y.z`; il commit di rilascio aggiorna solo `image_tags` in `src/docker/<servizio>/BUILD`
(web `0.2.YYYYMMDD`, core semver patch, servizi modello semver). Poi `pants package` / `publish` delle
sole immagini toccate e deploy manuale. Una PR che cambia `core` e `web` richiede **due** immagini;
una che cambia solo il frontend, una. Scriverlo nella descrizione della PR.

## Regole di lavoro

1. Mai commit diretti su `main`: branch `feat/…`, `fix/…`, `docs/…` e PR. Mai push senza l'accordo
   di chi coordina il repo.
2. Il **core** e' la parte condivisa da tutto: si tocca il meno possibile e mai per comodita' di un
   solo servizio. La configurazione del database non si cambia.
3. Prima di una funzionalita' nuova, una pagina in `docs/decisioni/`: cosa fa, cosa non fa, quali
   cuciture usa, come si verifica. Il percorso completo core→web e' descritto nel CLAUDE.md del core.
4. Ogni pacchetto tiene il proprio `CHANGELOG.md` (per il team backend) e, dove serve, il proprio
   `CLAUDE.md`. Una trappola scoperta si scrive nel CLAUDE.md giusto **nella stessa PR**.
5. Dati reali di produzione (aziende, utenti, rilevamenti) non entrano mai nel repo, nemmeno in un
   esempio: sono dati personali di clienti.
