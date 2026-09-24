# Web — frontend

React 19 + Vite 6 + TypeScript strict, Redux Toolkit (slice per area, **niente RTK Query**),
react-router 7, `keycloak-js`, Bootstrap 5 + react-bootstrap, mapbox-gl + turf, Formik + Yup.
Solo italiano, dichiarato in `index.html` (`lang="it"`, `translate="no"`, meta `notranslate`): senza,
Chrome traduceva l'italiano in italiano storpiandolo agli utenti con la traduzione automatica.

## Comandi

- `npm run dev` (Vite su :5173), `npm run lint`, **`npm run build`** = `tsc -b && vite build`.
- ⚠️ `npx tsc --noEmit -p .` **non controlla nessun file**: il `tsconfig.json` radice ha `include: []`
  e rimanda a `tsconfig.app.json`. Il controllo dei tipi e' `npm run build` (o `npx tsc -b --noEmit`).
  `tsconfig.app.json` ha `noUnusedLocals`: un import inutilizzato rompe il build.
- Il lint non e' in CI; su `main` restano alcuni `no-explicit-any` storici nei file del paesaggio.
  Non aggiungerne.
- Configurazione in `.env` (non committato) da `.env.example`: URL del core, di Keycloak (realm
  `tornatura`, client `dashboard`), dei servizi modello (`REACT_APP_MODELAPIS_SERVER_URL`: **un solo
  origin** per bollettini, peronospora e landscape, in produzione un proxy per path), token Mapbox.
  Se in locale la porta del core risulta occupata da altro, usare `127.0.0.1` invece di `localhost`
  nell'URL: il browser preferisce IPv6 e puo' finire su un altro processo in ascolto su `[::1]`.

## Stili: lo SCSS si compila a mano

L'app importa `src/index.css`, **non** `src/style/index.scss`. `index.css` e' generato dallo scss e
committato. Una regola aggiunta allo scss non arriva al browser finche' non si ricompila. Ricompilare
tutto il file con una versione diversa di Sass produce migliaia di righe di sole differenze di
formattazione: conviene compilare il solo blocco nuovo (`npx sass --no-source-map --style=expanded
blocco.scss`) e appenderlo in coda a `index.css` con un commento, committando entrambi i file.
Classi di casa: `trnt_btn` (+ `primary|secondary`, `slim-y`, `narrow-x`, `type-rounded`), `font-s/m/l`,
`iiinfo-label/value`, `section.soft`, `dot[data-size]`, `TableCozy` per le tabelle.

## Struttura

- `src/routes.tsx`: **tutte** le rotte. I blocchi `/admin`, `/m`, `/m/companies/:companyId`,
  `/m/companies/:companyId/fields/:fieldId` sono layout-route **fratelli**, ognuna popola la sidebar
  via `sidebar-slice`. Una pagina nuova = una `path` nel blocco giusto + una voce di menu
  (`features/fields/pages/field-detail.tsx` per il menu del campo, `company-detail.tsx` per l'azienda,
  `App.tsx` per il resto).
- `src/features/<area>/{pages,state}`: pagine e slice. Pattern di caricamento nelle pagine dei
  modelli: `useParams` + `fieldsSelectors.selectFieldbyId`, tre state `data/loading/error`,
  `useEffect` con `.then/.catch/.finally`, `headerbarActions.setTitle`.
- `src/services/model-api.ts`: le chiamate ai servizi modello (`fetchJson` + `MODEL_API_ERROR_MAP`
  che traduce i `detail` stabili in inglese dei servizi in messaggi italiani). Un servizio nuovo
  aggiunge qui le sue funzioni e i suoi errori.
- `src/components/`: componenti condivisi (`Map*`, `TableCozy`, `Modal*`, `InfoPopover`, `Icon`).

## SDK del core: `@tornatura/coreapis`

Generato dall'OpenAPI del core (swagger-codegen, typescript-axios) in `src/typescript/coreapis-sdk`,
impacchettato con `npm pack` e **committato come tarball** in `src/typescript/libs/`; il web lo
dipende come `file:../libs/tornatura-coreapis-<versione>.tgz`. Cambiare un endpoint del core
significa: rigenerare, alzare la versione, `npm pack`, sostituire il tarball, aggiornare
`package.json` del web. Processo manuale: l'`openapi.yaml` puo' essere indietro rispetto al core.

## Trappole di Redux

`createAsyncThunk` con `rejectWithValue` **non lancia**: un `try/catch` intorno al `dispatch` non si
attiva mai. Dopo `const result = await dispatch(azione(...))` controllare
`result.meta.requestStatus === "rejected"` e restare sulla pagina con l'errore, altrimenti si
naviga via come se il salvataggio fosse riuscito.

## Mappe

mapbox-gl 3; i layer si accendono con `setLayoutProperty(id, "visibility", …)` e si filtrano con
`setFilter` (tipo `FilterSpecification` da `mapbox-gl`). I dati dei servizi si disegnano da GeoJSON
in sorgenti dedicate; i popup al click usano `esc()` per non interpolare stringhe del backend in HTML.

## Immagine

`src/docker/web/Dockerfile`: `npm run build` in `node:20-alpine`, poi nginx con `try_files … /index.html`
(SPA). Tag `0.2.YYYYMMDD` in `src/docker/web/BUILD`. Il `.env` di produzione viene letto al build:
va preparato prima di `pants package`.
