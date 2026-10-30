# Avviso quando il bollettino di una coltura non si aggiorna da settimane
30/10/2026 · Vito Palmisano, Claude · adottata

## Contesto
A fine ottobre 2026 la pagina del bollettino di un campo a Bologna mostrava ancora il report del
16 settembre, e chi la guardava ha pensato a un guasto (credito dell'AI finito, servizio fermo). Non
lo era: la Regione Emilia-Romagna aveva chiuso la stagione (ultimi bollettini 2026 tra il 16
settembre, Bologna e Ferrara, e il 2 ottobre, Parma e Piacenza) e il servizio continuava a
controllare ogni mattina senza trovare niente di nuovo. La pagina non diceva niente di tutto questo.

## Decisione
Se il report ha piu' di 21 giorni, la pagina mostra sopra il report un avviso: "Nessun
aggiornamento dal <data>. E' l'ultimo bollettino pubblicato dalla Regione per questa coltura in
questa zona. Quando ne uscira' uno nuovo comparira' qui da solo." Per l'Emilia-Romagna, solo da
ottobre a gennaio, si aggiunge che i bollettini si fermano in autunno e riprendono a febbraio.

## Alternative
- **Un campo "stagione chiusa" nella risposta del servizio bollettini**: il servizio dovrebbe sapere
  quando la Regione chiude, cosa che non pubblica. Avrebbe richiesto anche una nuova immagine del
  servizio per un testo di interfaccia.
- **Avviso basato sull'ultimo bollettino della provincia invece che sul report della coltura**: il
  servizio non lo espone. La data del report della coltura c'e' gia' (`report_date`), e la frase
  "per questa coltura in questa zona" resta vera in entrambi i casi.

## Cuciture
Solo `web/src/features/fields/pages/field-model-bollettini.tsx`. Ne' il core ne' i servizi modello.

## Verifica
Soglia scelta sulle pause osservate nel 2026 tra due bollettini della stessa zona: al massimo 14
giorni in Campania, 28 in Emilia-Romagna (Bologna e Ferrara, agosto). Il report di una singola
coltura puo' restare fermo di piu' (vite a Bologna e Ferrara: dal 5 agosto al 16 settembre): per
questo la frase sulla fine della stagione compare solo da ottobre a gennaio. Prova: un campo a
Bologna mostra l'avviso con la data del 16 settembre 2026; un campo in Campania con il bollettino
della settimana non lo mostra.

## Conseguenze
Solo una nuova immagine `web`. Se la Regione cambia calendario, va aggiornata la frase sulla stagione
(`MESI_PAUSA_ER`).
