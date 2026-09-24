# Decisioni di architettura

Una nota per ogni scelta che qualcuno potrebbe voler capire o rimettere in discussione fra un anno.
Si scrive **prima** di iniziare una funzionalita', si aggiorna quando la decisione cambia, non si
cancella quando viene superata (si aggiunge "Superata da …").

Nome del file: `AAAA-MM_argomento.md`. Struttura:

```
# Titolo
Data · autori · stato (proposta | adottata | superata da …)

## Contesto      — il problema, e perche' ora
## Decisione     — cosa facciamo, in tre frasi
## Alternative   — cosa abbiamo scartato e perche'
## Cuciture      — quali parti del monorepo tocca, quali no (il core?)
## Verifica      — come si prova che funziona, con i numeri attesi
## Conseguenze   — cosa cambia per deploy, dati, utenti
```

Decisioni gia' documentate altrove, da non duplicare:
- servizio `landscape` (paesaggio agricolo): `src/python/landscape/CLAUDE.md` e il suo `CHANGELOG.md`;
- storia e motivazioni dei servizi modello: i `CHANGELOG.md` di `bollettini`, `peronospora`, `landscape`.
