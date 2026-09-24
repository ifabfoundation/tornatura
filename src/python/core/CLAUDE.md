# Core — API di business

FastAPI su porta **8080** (fissa in `main.py`, `uvicorn.run`), CORS aperto a `*`, tutte le rotte
sotto `/api/v1` (`api/v1/__init__.py` registra i router: i nested vanno **prima** di `organizations`).
Nessun test automatico: la verifica e' `pants run src/python/core:app` con il compose di
`src/deployment` acceso, poi `/docs` e la funzionalita' provata dal frontend.

## Stack

- **MongoDB via MongoEngine**, non SQL. La connessione e' un **effetto collaterale dell'import** di
  `services/__init__.py` (`connect(host=APIConfig.MONGO_DATABASE_HOST, port=27017)`): importare un
  service significa connettersi.
- **Keycloak (estensione Phase Two)**: le organizzazioni sono i tenant; gli **utenti vivono solo in
  Keycloak**, non c'e' una collection User. `OrganizationModel` e' lo specchio Mongo dell'organizzazione
  Keycloak (stesso `orgId`). Il token e' validato in `security.py` (`SecurityChecker(HTTPBearer)` con
  `python-keycloak`); i ruoli di organizzazione arrivano nel claim `organizations`.
  Phase Two crea per ogni organizzazione un utente tecnico `org-admin-…@noreply.phasetwo.io`: **non e'
  una persona**, va escluso da qualunque conteggio di utenti.
- **MinIO** per foto e file (URL presigned), **SMTP sincrono** per le email (template in `templates/`),
  **LibreOffice** per generare i PDF dei moduli.
- Configurazione con `python-decouple` in `config.py` da un `.env` **mai committato** e mai
  impacchettato nel pex (vedi `BUILD`).

## Catena rigida

`api/v1/<risorsa>.py` → `services/<risorsa>_services.py` → `models.py`, con `serializers.py` (Pydantic)
per payload e risposte. Niente scorciatoie dal router al modello.

Entita' in `models.py`: `HarvestType` (registro colture, chiave `code`), `AgriFieldModel` (`orgId`,
`harvest`, `map: Point[]`, `area`, `description`), `OrganizationModel`, `OrganizationQuestionnaireModel`,
`ObservationType` (catalogo globale delle schede di rilevamento: `typology`, `method`,
`observationType ∈ range|counters`, `supportedHarvestCodes`), `DetectionType` (associa un campo a una
scheda), `DetectionModel` (il rilevamento: `detectionTime`, `detectionData.points[]`, `sessionId` per
i rilevamenti fatti nella stessa uscita; **nessun `orgId` diretto**, si risale dal campo),
`FeedbackModel`, `InvitationModel`.

## Convenzioni che sorprendono

- Campi Mongo **camelCase**, path param snake_case, timestamp **interi in millisecondi UTC**
  (`creationTime`, `detectionTime`), soft delete con `deleted`.
- Le relazioni sono **stringhe**, non `ReferenceField`: `DetectionModel.agrifieldId` e' la stringa
  dell'`_id` (ObjectId) del campo. Nelle query si converte sempre (`str(campo.id)`), altrimenti il join
  restituisce zero righe in silenzio.
- La catena rilevamento → scheda passa da `DetectionType`: `detection.detectionTypeId` →
  `DetectionType.observationTypeId` → `ObservationType`.
- Validazioni: la lunghezza massima va dichiarata **nel serializzatore** (`Field(max_length=…)`) oltre
  che nel modello, perche' `errors.handle_api_exceptions` mappa tutto cio' che non e' `DoesNotExist`
  a **500**; solo il serializzatore produce un 422 leggibile. (Descrizione del campo: 500 caratteri,
  `DESCRIPTION_MAX_LENGTH`.)
- Un ObjectId malformato solleva `bson.errors.InvalidId`, non l'eccezione di MongoEngine.
- `@catch_api_exception` (`decorators.py`) **non funziona sugli handler async**.
- La paginazione e' slicing in memoria.

## Permessi

Due livelli in `permissions.py`. Ruoli client (`IsAdmin`, `IsAgronomist`, `IsAuthenticated`) e ruoli
di organizzazione (`CanView…`/`CanManage…` su Organization, Members, Agrifields, Detections,
DataFiles, Invitations), combinabili in `SecurityChecker(IsAdmin, IsAgronomist, mutually_exclusive=True)`.
Il controllo **sull'oggetto** (l'azienda proprietaria del campo e' quella dell'URL?) va fatto a mano
nell'handler: ⚠️ diversi endpoint nested non verificano `agrifield.orgId == org_id`. Un handler nuovo
lo fa (esempio: `PUT /detections/{id}` per la correzione della data).

## Email

Il core scrive email in quattro casi: benvenuto alla creazione di un account
(`users_services`), invito a un'organizzazione e accettazione dell'invito (`invitations_services`),
avviso allo staff alla registrazione di un'azienda (`send_notification_to_staff`), feedback.
Un'azienda creata da un tecnico dal proprio profilo **non riceve nulla**: riceve un'email solo se
viene invitata.

## Migrazioni e manutenzione

`scripts/` contiene gli script di migrazione e pulizia, ognuno `pex_binary` nel `BUILD`, con
`--dry-run` / `--apply`. Si usano quelli, non query a mano sul database.

## Percorso di una funzionalita' nuova (core → web)

`models.py` → `serializers.py` → `services/<x>_services.py` → `api/v1/<x>.py` (+ registrazione in
`api/v1/__init__.py`) → `permissions.py` se serve un ruolo nuovo (enum + script di backfill +
assegnazione in onboarding e inviti) → **rigenerare l'SDK** (vedi CLAUDE.md del web) → slice Redux →
`routes.tsx` → voce di menu. Se la funzionalita' e' un modello o un calcolo su dati esterni, **non
passa dal core**: e' un servizio gemello di `landscape`.
