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

Procedura seguita per landscape 2.2.0 e web 0.2.20260925 (25/09/2026), passo per passo:

1. **Il frontend ha la configurazione dentro.** Vite scrive nel bundle, a build time, i valori del
   `.env` di `src/typescript/web/` (blocco `define` in `vite.config.ts`); il target
   `src/typescript/web:artifacts` include `.env` apposta, anche se git lo ignora. Le variabili
   `REACT_APP_*` nel compose del server **non hanno effetto** (nginx serve file statici). Quindi:
   un'immagine web per ambiente, `0.2.YYYYMMDD` per staging e `0.2.YYYYMMDD-PROD` per produzione,
   ognuna costruita col `.env` del suo ambiente. **Mai** costruire un'immagine da rilasciare col
   `.env` di sviluppo (punta a localhost): si costruisce in un `git worktree` pulito del branch di
   rilascio, con il `.env` dell'ambiente copiato dentro e tolto subito dopo.
2. **I valori giusti si leggono dall'immagine che gira**, non si ricordano: dal bundle in
   `/usr/share/nginx/html/assets/*.js` del container web dell'ambiente (server core, auth, realm,
   client id, storage, server modelli, token Mapbox). Dopo la build, gli indirizzi del bundle nuovo
   devono coincidere uno per uno con quelli del bundle in uso, e il token Mapbox deve essere lo
   stesso.
3. **Prima di toccare lo staging, confrontare i testi** del bundle in uso con quelli nuovi: lo
   staging puo' contenere lavoro non ancora in `main` (il 25/09 conteneva una sezione di
   amministrazione). In quel caso lo staging web non si sovrascrive.
4. **I servizi modello** (landscape, bollettini, peronospora) sono una sola immagine per staging e
   produzione: la configurazione arriva dal volume e dal compose.
5. **Sul server**: copia datata del compose dell'ambiente, cambio delle sole righe `image:`, poi
   `docker compose config --quiet` e `docker compose up -d --no-deps <servizi>`. `--no-deps` evita di
   rilanciare gli `*_initiator` (l'updater di landscape riscarica AGREA, 1,3 GB).
6. **Verifica**: gli endpoint del servizio con i numeri attesi del CHANGELOG; una risposta che non
   doveva cambiare (es. `/composition` a 3 e 5 km) identica a prima del rilascio; il sito risponde e
   serve il bundle nuovo; nessun errore nei log.
7. **Per tornare indietro**: rimettere la copia datata del compose e rifare `up -d --no-deps`; le
   immagini precedenti restano sul server.

Se le immagini non sono state pubblicate su Docker Hub ma copiate sul server
(`docker save | ssh ... docker load`), un `docker compose pull` fallisce per quei tag finche' chi ha
l'accesso a Docker Hub non le pubblica dallo stesso commit.

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
