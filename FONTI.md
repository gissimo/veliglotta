# Fonti per Veliglotta

Questo file raccoglie le fonti già usate nelle voci e quelle consigliate per verificarne di nuove. Serve a chi lavora sul progetto, in qualsiasi sessione, per non ripartire da zero.

Ogni fonte ha un peso per ciascuna lingua che copre. I pesi stanno in `data/fonti.json` e valgono per il punteggio di verifica; se una fonte non ha peso per una lingua, per quella lingua non conta.

- **A**: opera autorevole e monolingue per quella lingua, con definizioni e marca di dominio, oppure testo originale di un regolamento ufficiale. È la prova principale per portare una lingua al livello 3 del punteggio.
- **B**: fonte attendibile ma con un limite: equivalenti dati da un ente di terminologia o da una federazione, traduzione ufficiale, dizionario generale senza marca nautica, glossario di un ente pubblico con qualche imprecisione. Vale come secondo riscontro.
- **C**: elenco senza definizioni, autore privato o commerciale, lessico datato o errori documentati. Serve solo come spunto per cercare altrove, mai come prova.

Due fonti che riproducono lo stesso testo non sono riscontri indipendenti: in quel caso una delle due non ha peso per la lingua in comune (vedi RFEV-REV per l'inglese).

Ogni indirizzo ha uno stato:

- **letto**: la pagina o il documento è stato aperto e letto, almeno per le voci indicate.
- **visto**: l'indirizzo è comparso in una ricerca web fatta il 14 novembre 2026.
- **da confermare**: la fonte è nota ma in quella ricerca non ho trovato l'indirizzo, quindi va controllato prima di registrarlo in `fonti`.

Le regole del punteggio di verifica sono in `README.md`.

## Fonti già usate nelle voci

Quali voci usano ciascuna fonte si ricava dal campo `fonti` di `data/voci.json`.

| Sigla | Fonte | ENG | ESP | FRA | ITA | Note |
|---|---|---|---|---|---|---|
| WS-ERS | World Sailing, Equipment Rules of Sailing 2025-2028 | A |  |  |  | Testo originale con le definizioni ufficiali di scafo, appendici, attrezzatura e vele. Copia non ospitata da World Sailing. |
| TRE | Treccani, Vocabolario |  |  |  | A | Non sempre usa una marca abbreviata: l'ambito nautico può comparire solo dentro la definizione. Controllare gli omonimi numerati. |
| OQLF-GDT | Office québécois de la langue française, Grand dictionnaire terminologique | B |  | A |  | Banca terminologica del Québec: per l'inglese dà solo equivalenti, e alcuni termini francesi possono differire dall'uso di Francia. |
| DLE | Real Academia Española, Diccionario de la lengua española |  | A |  |  | Monolingue con marca Marina. Molte accezioni descrivono la nave a vele quadre. |
| DPD | Real Academia Española, Diccionario panhispánico de dudas |  | A |  |  | Normativo sui dubbi d'uso, non nautico. |
| DEI | Real Academia de Ingeniería, Diccionario español de ingeniería | B | A |  |  | Monolingue con marca "Ingeniería naval", equivalente inglese e definizione. Prospettiva della nave. |
| RFEV-RRV | Real Federación Española de Vela, Reglamento de Regatas a Vela 2025-2028 |  | B |  |  | Traduzione ufficiale del regolamento di regata: in caso di conflitto prevale l'inglese. |
| RFEV-REV | Real Federación Española de Vela, Reglas de Equipamiento a Vela 2021-2024 |  | B |  |  | Traduzione ufficiale delle Equipment Rules 2021-2024, con refusi. Il testo inglese che riporta è quello delle ERS: per l'inglese non è un riscontro indipendente da WS-ERS, quindi non ha peso. |
| INCUAL | Instituto Nacional de las Cualificaciones, Ministerio de Educación, glosario de la cualificación TMV553_2 (2011) |  | B |  |  | Glossario monolingue di un ente pubblico, con definizioni. Alcune sono imprecise. |
| DIMAR | Dirección General Marítima de Colombia, Glosario marítimo |  | B |  |  | Autorità marittima colombiana: spagnolo d'America. |
| TC | TERMCAT, Centre de Terminologia de Catalunya, Diccionari d'esports nàutics (2008) | C | B | C |  | Ente pubblico di terminologia, definizioni in catalano. Circa l'80% degli equivalenti inglesi e francesi coincide con le voci. |
| TC-AC | TERMCAT, Centre de Terminologia de Catalunya, Terminologia de la Copa Amèrica (2024) | B | B | B |  | Stesso ente, 2024, 81 termini rivisti da specialisti. Il 95% degli equivalenti coincide con le voci. Non è indipendente da TC. |
| LAR | Larousse, Dictionnaire de français |  |  | B |  | Dizionario generale, senza marca di dominio. |
| WW | Waterwind, Dizionario di terminologia nautica italiano-inglese (2002) | C |  |  | B | Definizioni in italiano con la categoria, autore non indicato. Per l'inglese mescola sensi antichi. |
| MSB | Mers & Bateaux, Vocabulaire marin, lexique de la voile et des bateaux |  |  | B |  | Lessico monolingue di una rivista di nautica, con definizioni brevi e lessico d'uso in Francia. Autore e data non indicati, qualche refuso. |
| UNIOVI | Universidad de Oviedo, Escuela Superior de la Marina Civil, Diccionario náutico | B | B |  |  | Scuola di marina mercantile, senza definizioni. |
| FFV-GBR | Fédération Française de Voile, dictionnaire français-anglais (1999) | B |  | B |  | Elenco alfabetico senza definizioni, con lessico corrente. |
| UNITS | Università di Trieste, Glossario nautico |  |  |  | C | Glossario di un corso universitario, autore non indicato. Non è un dizionario. |
| AEMET | Agencia Estatal de Meteorología, blog |  | B |  |  | Agenzia meteorologica nazionale, testo divulgativo. |
| RFEV-DIC | Real Federación Española de Vela, Diccionario de términos náuticos español-francés-inglés (2002) | C | C | C |  | Elenco trilingue senza definizioni, ospitato da terzi, con errori evidenti ("Proa: Bow, stern"). |
| RL | Referenze locali (documenti non pubblicati) | C | C | C | C | Documenti non pubblicati in `fonti locali/`. Uno dei due è una versione successiva di RFEV-DIC, con gli stessi errori. |
| USCG | US Coast Guard Auxiliary, Interpreter Corps, Glossary of Nautical Terms (2012) | C | C | C | C | Tre elenchi bilingui senza definizioni. Errori sulle parole polisemiche, spagnolo americano. |
| FFV-ITA | Fédération Française de Voile, dictionnaire français-italien (2001) |  |  | C | C | Elenco per temi senza definizioni, lessico anteriore al 1996, errori. Stessa base di FFV-ESP. |
| FFV-ESP | Fédération Française de Voile, dictionnaire français-espagnol (2001) |  | C | C |  | Elenco per temi senza definizioni, lessico anteriore al 1996, errori. Stessa base di FFV-ITA. |
| MF | Mauro Fornasari e Andrea Patelli, Vocabolario nautico | C |  |  | C | Elenchi senza definizioni né data, di un istruttore di vela. Qualche errore. |
| LF | Luca Ferrua, Terminologia nautica, traduzione ITA-ING (2009), su Lexicool | C |  |  | C | Glossario personale con definizioni brevi, errori evidenti. |
| MAIF | Mutuelle d'assurance des instituteurs de France, Lexique de la navigation |  |  | C |  | Lessico di una compagnia assicurativa, senza fonti. |
| SPANISHDICT | SpanishDict, navigation vs sailing | C | C |  |  | Dizionario bilingue commerciale. |
| EFD | EFDeportes, Revista Digital |  | C |  |  | Articoli divulgativi di una rivista di scienze motorie. |

## Fonti valide solo per una parte del vocabolario

Il peso per lingua non dice in quale ambito una fonte è affidabile. Prima di citarla, controllare:

- **DEI**: citare solo le accezioni con marca "Ingeniería naval y aprovechamiento de los recursos oceánicos", e solo per scafo, appendici e attrezzatura. Per andature e regolazioni è debole, e alcune accezioni navali hanno un altro senso: *bulbo* è il bulbo di prua, *largo* un cavo d'ormeggio, *pinzote* l'agugliotto del timone.
- **DLE**: molte accezioni con marca Marina descrivono la nave a vele quadre. Non citarle per l'attrezzatura moderna: *burda*, *cruceta*, *tangón*, *tormentín*, *estay*, *orza* (2), *eslora* e *pinzote* hanno sensi diversi da quelli della vela di oggi. Le locuzioni vanno cercate dentro la voce della parola principale.
- **DPD**: solo per distinguere parole vicine, come *tiempo* e *clima*.
- **OQLF-GDT**: controllare il dominio della scheda (marina, sport nautici) e, per il francese, se il termine è d'uso anche in Francia.
- **WS-ERS e RFEV-REV**: definiscono scafo, appendici, attrezzatura e vele, non manovre né andature.
- **RFEV-RRV**: terminologia di regata e andature, nel senso del regolamento.
- **UNIOVI**: solo scafo e nave (casco, quilla, calado, eslora, manga, obra viva). Per l'attrezzatura dà sensi navali: *burda* backstay, *tangón* outrigger boom, *cruceta* crosshead.
- **TC**: solo schede delle aree Vela, Esports nàutics e Motonàutica. Nelle aree Rem e Piragüisme *cruceta*, *proel* e *caña* hanno un altro senso.
- **AEMET**: solo meteorologia.
- **LAR**: senza marca di dominio, quindi controllare che l'accezione citata sia quella nautica.

## Fonti consigliate per lingua

### ITA

- **Treccani, Vocabolario**: https://www.treccani.it/vocabolario/, stato letto per *drizza* (https://www.treccani.it/vocabolario/drizza/): la voce non porta una marca abbreviata ma colloca il termine "nell'attrezzatura navale". Peso A. Attenzione agli omonimi numerati: https://www.treccani.it/vocabolario/scotta2/ è il siero del formaggio, non la manovra, quindi l'indirizzo giusto di ogni voce va controllato aprendolo.
- **Garzanti Linguistica**: https://www.garzantilinguistica.it, stato visto. Peso A. La pagina di ricerca non restituisce il testo delle voci a uno strumento automatico, quindi l'indirizzo delle singole voci resta da confermare.
- **Federazione Italiana Vela (FIV)**: https://www.federvela.it, stato visto. Pubblica il Regolamento di Regata in italiano, per esempio l'edizione 2017-2020: https://www.federvela.it/images/fiv/rrs_2017-2020_-_ita_con_rev_ws_-_agg_13_feb_sito_fiv.pdf. Peso B: è una traduzione, e in caso di conflitto prevale il testo inglese. Non ho individuato l'edizione 2025-2028 in italiano.
- **Davis, Dizionario navale italiano-inglese e inglese-italiano**: https://archive.org/download/navaldictionaryi00davirich/navaldictionaryi00davirich_bw.pdf, stato visto. Peso B: è un'opera storica, di cui non ho verificato l'anno, quindi i termini moderni di diporto potrebbero mancare.
- ***Dizionario di terminologia nautica italiano-inglese*** (Milano, giugno 2002, I edizione): https://www.waterwind.it/new/images/pdf/Dizionario_Italiano_inglese.pdf, stato letto. Per ogni lemma dà la marca di categoria (Andature, Alberatura e vele, Di coperta), l'equivalente inglese e una definizione in italiano. Autore non indicato. Peso B per l'italiano, C per l'inglese. Copre bene vele e coperta, mancano il gergo di regata e il genoa.
- **Mauro Fornasari e Andrea Patelli, Vocabolario nautico**: italiano-inglese http://www.maurofornasari.com/itaing.htm e inglese-italiano http://www.maurofornasari.com/inglita.htm, stato letto. Elenchi senza definizioni né data, sul sito di un istruttore di vela. Peso C. Errori: prua resa con "bow, heading, stern", bulbo con "hull, bulb", inferitura con "head-rope, hoist, luff".
- **Luca Ferrua, *Terminologia nautica (traduzione ITA-ING)*** (2009): https://static.lexicool.com/dictionary/RC8WN616716.pdf, stato letto. Glossario personale caricato su Lexicool, con l'inglese tra parentesi e una definizione breve in italiano. Peso C. Errori: alare reso con firedog, abbrivio con spring, abbattuta definita come una strambata, vento reale con real wind. Colloca il lasco intorno ai 120 gradi e il gran lasco intorno ai 150.

### FRA

- **OQLF, Grand dictionnaire terminologique**: https://vitrinelinguistique.oqlf.gouv.qc.ca, stato visto. Le schede indicano i domini d'uso e gli equivalenti in altre lingue. Peso A.
- **CNRTL, Trésor de la langue française informatisé (TLFi)**: dizionario con marca "Marine". Peso A. Indirizzo da confermare: https://www.cnrtl.fr/definition/écoute risponde, ma mostra per prima un'altra accezione (l'ascolto, con marca "ART MILIT."), e gli indirizzi https://www.cnrtl.fr/definition/écoute//1 e https://www.cnrtl.fr/lexicographie/drisse danno errore 404. Serve trovare come puntare all'omonimo giusto.
- **Larousse**: https://www.larousse.fr/dictionnaires/francais/, stato letto per *drisse* (https://www.larousse.fr/dictionnaires/francais/drisse): definizione nautica chiara, senza marca di dominio, ed etimologia dall'italiano *drizza*. Peso B.
- **Fédération Française de Voile (FFVoile)**: https://www.ffvoile.org, stato visto. Peso B per la terminologia di regata. Lo spazio arbitrato https://arbitrage.ffvoile.fr ospita le prescrizioni nazionali alle regole 2025-2028 e la traduzione delle *Règles d'Équipement des Voiliers 2025-2028* (gruppo di traduzione FFVoile, gennaio 2025): https://arbitrage.ffvoile.fr/media/2pvfwybg/rev-2025-2028-mars-2025.pdf, stato visto, ma all'apertura ha dato errore 404. Le regole di equipaggiamento definiscono scafo, appendici, alberi e vele, quindi sarebbero utili per le voci di attrezzatura. Non ho trovato il testo integrale delle *Règles de Course à la Voile 2025-2028* in francese.
- **Soé, Dupont, Roussin, Vocabulaire des termes de marine (yachting)**, nella biblioteca digitale della Difesa francese: https://bibliotheques-numeriques.defense.gouv.fr/impression/document/e41c34c8-072f-45a2-8239-b34fb413250a, stato visto. Peso B: opera storica sul diporto.
- **Mers & Bateaux, *Vocabulaire marin*** (rivista di nautica): https://mersetbateaux.com/lexique-de-voile-bateaux/, stato letto il 15 novembre 2026. Circa 300 voci con definizioni in francese, corrette nei casi controllati (*vit-de-mulet*, *safran*, *hale-bas*, *génois*, *ligne de flottaison*), con refusi e qualche semplificazione (*bastaque* messa nel gréement dormant). Peso B per il francese: completa l'OQLF con l'uso di Francia. Attenzione a *dérive*, che qui è solo l'appendice, e a *piano*, che è l'attrezzatura e non il ruolo. La tabella in cinque lingue dello stesso sito (https://mersetbateaux.com/es/lexico-internacional-de-nautica/, stato letto) non va usata: è una traduzione con errori gravi, per esempio *abattre* reso in spagnolo con *orzar*, *balancine* in italiano con *balumina*, *bordure* con *inferitura*.
- **FFVoile, dizionari del servizio internazionale**, senza definizioni:
  - francese-italiano e francese-spagnolo (ottobre 2001): http://www.ffvoile.fr/ffv/web/services/international/documents/dico_FRA_ITA.PDF e http://www.ffvoile.fr/ffv/web/services/international/documents/dico_FRA_ESP.PDF, stato letto. Organizzati per temi con voci numerate, come le tavole di un dizionario illustrato, da cui sembrano ricavati; citano le regole IYRU, quindi il lessico risale a prima del 1996. Peso C. Errori e termini datati: point de drisse reso con antennale, au près bon plein con di bolina stretta, il vang con ostino e trapa, la draglia con battagliola e pasamano, il paterazzo con poparrás.
  - francese-inglese (luglio 1999): http://www.ffvoile.fr/ffv/web/services/international/documents/dico_FRA_GBR.PDF, stato letto. Elenco alfabetico di un altro autore, con lessico corrente. Peso B per la coppia francese-inglese.

### ESP

- **Real Academia Española, Diccionario de la lengua española (DLE)**: https://dle.rae.es, stato visto. Molte voci portano la marca "Mar.", per esempio *marinar* e *marcación*. Peso A. Il 15 novembre 2026 rispondeva 403 agli strumenti automatici (curl e lettura web), ma si legge dal browser: stato letto, il 15 novembre 2026 tramite Chrome, per circa 90 lemmi. Le locuzioni (*vela mayor*, *línea de flotación*, *viento a un largo*, *viento en popa*, *jarcia de labor*) stanno dentro la voce della parola principale. Molte accezioni con marca Marina descrivono la nave a vele quadre e non vanno usate per il diporto: *burda* è un brandal dei masteleros, *cruceta* la piattaforma in testa ai masteleros, *tangón* il buttafuori laterale per ormeggiare le lance, *tormentín* un piccolo albero sul bompresso, *estay* il cavo tra due alberi, *orza* (2) un'appendice aggiunta alla chiglia dei balandros, *pinzote* l'agugliotto del timone. Non registra *trasluchar*, *trasluchada*, *winche*, *génova* come vela, *guardamancebos*, *obenquillo* né *spinnaker*.
- **Real Federación Española de Vela (RFEV), Reglamento de Regatas a Vela 2025-2028**: https://rfev.es/wp-content/uploads/2024/12/WS-RRS-2025-2028-ESP-Web-WS-Ene-2025_publicada.pdf, stato letto. È la traduzione ufficiale spagnola, in vigore dal 1° gennaio 2025. Peso B: in caso di conflitto prevale il testo inglese. Usa *escota*, *botavara*, *driza*, *vela mayor*, *rumbo de ceñida*, il verbo *virar por avante* e i sostantivi *virada por avante* e *trasluchada*. Sullo stesso dominio, olimpicos.rfev.es, ci sono anche bozze provvisorie del 10 ottobre 2024: non usarle.
- **RFEV, Reglas de Equipamiento a Vela 2021-2024**: https://rfev.es/wp-content/uploads/2024/11/Document_9116_20230320101809_es.pdf, stato letto (la copia su olimpicos.rfev.es non risponde). Testo spagnolo e inglese in sequenza, con il termine inglese tra parentesi in ogni definizione. Peso B: è la traduzione dell'edizione precedente alle ERS 2025-2028, con refusi ("spinaker pole") e intestazioni rimaste dal ciclo 2017-2020. Chiama la randa solo *mayor*, riserva *orza* alla deriva che ruota su un perno (centreboard) e *orza de sable* a quella che scorre (daggerboard), distingue *burda alta* (running backstay) e *burda baja* (checkstay), e nella sezione sugli angoli chiama *escota*, *driza* e *amura* i tre puños. Non ho trovato l'edizione 2025-2028 in spagnolo.
- **Real Academia de Ingeniería, Diccionario español de ingeniería (DEI)**: https://diccionario.raing.es, stato letto. Le voci si aprono con l'indirizzo https://diccionario.raing.es/es/lema/ seguito dal termine, per esempio https://diccionario.raing.es/es/lema/escota; i termini di più parole spesso mancano. Ogni accezione ha marca, equivalente inglese e definizione. Peso A per scafo e attrezzatura, con la marca "Ingeniería naval y aprovechamiento de los recursos oceánicos". Le definizioni sono pensate per la nave: il foque è la vela tra trinquete e bauprés, il bulbo è il bulbo di prua e non quello della chiglia, e l'unica accezione navale di *largo* è un cavo d'ormeggio (backspring). Per *navegación* dà come equivalenti sia sailing sia navigation.
- **TERMCAT, Centre de Terminologia, Diccionari d'esports nàutics** (2ª ed., 2008): https://www.termcat.cat/ca/diccionaris-en-linia/10, stato letto, scaricato in XML da Terminologia Oberta (https://www.termcat.cat/Thor/files/diccionaris/esportsnautics.xml). Circa 965 schede, quasi tutte di vela, con definizione in catalano ed equivalenti in spagnolo, francese e inglese. Peso B per lo spagnolo. Le schede di remo e canoa vanno escluse: *cruceta* e *proel* hanno lì un altro senso. Dà *largo* come "reaching leg" ed *empopada* come "dead run".
- **TERMCAT, Terminologia de la Copa Amèrica** (2024): https://www.termcat.cat/ca/diccionaris-en-linia/323, stato letto in XML (https://www.termcat.cat/Thor/files/diccionaris/copaamerica.xml). 81 termini rivisti da specialisti, stessa struttura del dizionario precedente. Peso B per spagnolo, inglese e francese, perché il 95% degli equivalenti coincide con le voci; non è indipendente dal dizionario TERMCAT.
- **ORC, Reglamento IMS 2023, traducción al castellano**: https://orc2.orc.org/rules/IMS%202023%20ESP.pdf, stato letto ma non usato nelle voci. Regolamento di stazza con definizioni tecniche di grátil, baluma, pujamen, botavara, burda, tangón e francobordo. Peso B per vele e attrezzatura.
- **INCUAL, Ministerio de Educación**: glossari delle qualifiche professionali nautiche, per esempio quello sulla manutenzione dell'attrezzatura delle imbarcazioni da diporto: https://incual.educacion.gob.es/documents/20195/1873855/TMV553_2+-+A_GL_Documento+publicado/a59938a4-e643-489b-ab02-d1869780a7fe, stato letto (scaricato con curl: con lo strumento di lettura web la connessione si interrompe). Pubblicato nel 2011, è un glossario monolingue con definizioni di circa 90 termini, tra cui *amantillo*, *baluma*, *cruceta*, *grátil*, *jarcia de labor*, *matafión*, *mordaza*, *obenque*, *obenquillo*, *pujamen*, *rizo*, *tangón*, *tormentín* e *trapa*. Peso B: è un ente pubblico, ma alcune definizioni sono imprecise, per esempio quella di *genova*, scritto senza accento.
- **Fundación MAPFRE**: manuale sulle imbarcazioni da diporto con un glossario delle parti della barca: https://documentacion.fundacionmapfre.org/documentacion/pt/media/group/1062767.do, stato visto, non letto. Peso B provvisorio.
- **RFEV, *Diccionario de términos náuticos español-francés-inglés. Terminología específica*** (2002): https://www.estudiasonavegas.com/images/Archivos/Miscelanea/Misce_Libros/Diccionario%20Nautico%20de%20la%20FEV.pdf, stato letto. Elenco trilingue di circa 660 righe, senza definizioni. Peso C. Una delle referenze locali ne è una versione successiva che aggiunge l'italiano, con gli stessi errori: le due vanno contate come un solo riscontro.
- **Dimar, Dirección General Marítima (Colombia), Glosario**: https://www.dimar.mil.co/glosario, stato letto per *abatimiento* (pagina della lettera A: https://www.dimar.mil.co/glosario?name=1). Glossario marittimo di un'autorità pubblica, con definizioni. Peso B: è spagnolo d'America, e va confrontato con l'uso spagnolo.
- **Dizionari storici**: un articolo accademico (https://hispadoc.es/descarga/articulo/10412617.pdf, stato visto) cita il *Diccionario marítimo español* di O'Scanlan (1831) e quello di Guardia (1921). Utili per l'etimologia, non per l'uso moderno.
- **Universidad de Oviedo, Escuela Superior de la Marina Civil, Diccionario náutico**: https://marina.uniovi.es/diccionario/es-en, stato letto (c'è anche la direzione inglese-spagnolo). Circa 2.800 righe, senza definizioni, per la marina mercantile. Peso B per i termini di scafo e nave (casco, quilla, calado, eslora, manga, obra viva). Quasi nulla sulle vele, e alcuni termini dell'attrezzatura hanno sensi navali: Burda - Backstay, Tangón - Outrigger boom, Cruceta - Crosshead.
- Lo spagnolo resta la lingua meno coperta per il diporto. Con le Reglas de Equipamiento, il DEI e TERMCAT scafo, attrezzatura e vele sono coperti; mancano ancora fonti per ruoli dell'equipaggio, attrezzatura di coperta (winch, stopper, carrelli, gancio dei terzaroli) e regolazioni (vang, cunningham, caricabasso).

### ENG

- **Oxford English Dictionary e Merriam-Webster**: dizionari con etichetta nautica. Peso A. Gli indirizzi https://www.merriam-webster.com/dictionary/halyard e https://www.oxfordlearnersdictionaries.com/definition/english/halyard compaiono nelle ricerche, ma rispondono con errore 403 agli strumenti automatici: vanno aperti a mano. L'Oxford Learner's Dictionary non è l'OED, che è in abbonamento: peso B.
- **World Sailing, Equipment Rules of Sailing 2025-2028**: copia su https://regattanetwork.com/clubmgmt/regatta_uploads/27815/EquipmentRulesofSailing20252028v.2.pdf, stato letto. Definisce scafo, attrezzatura (*forestay*, *backstay*, *shroud*, *running backstay*, *spreader*, *spinnaker pole*, *outhaul*, *vang*) e parti della vela (*luff*, *leech*, *foot*, *head*, *clew*, *tack*). Peso A per la terminologia dell'attrezzatura. La copia non è sul sito di World Sailing: va confrontata con l'originale.
- **World Sailing, The Racing Rules of Sailing**: https://www.sailing.org, stato visto. Le definizioni del regolamento sono un glossario ufficiale. Peso A per la terminologia di regata, non per quella di diporto.
- **RYA**: non ho trovato il glossario ufficiale. Il glossario del sito https://nauticalknowhow.mysailingcourse.com/glossary/ appartiene a un sito commerciale di corsi, non alla RYA: peso C.

## Fonti trasversali

- **IATE**, la banca dati terminologica dell'Unione europea: https://iate.europa.eu/home, stato visto. È multilingue, ma non specifica della nautica, quindi i termini velici possono mancare. Peso B.
- **IHO S-32, Hydrographic Dictionary**, inglese e francese: https://portal.iho.int/iho-ohi/S32/engFreView.php?page=157, stato visto. Utile per i termini di navigazione e idrografia. Peso A per quel settore.
- **Traduzioni del Regolamento di Regata**: sono pubblicate dalle autorità nazionali, e il testo inglese prevale in caso di conflitto. Il sito https://rrs.sh raccoglie versioni in più lingue, comprese italiano, francese e spagnolo, ma non è affiliato a World Sailing: peso C.
- **US Coast Guard Auxiliary, Interpreter Corps, Glossary of Nautical Terms** (giugno 2012), tre elenchi bilingui in due direzioni: inglese-italiano https://icdept.cgaux.org/pdf_files/English-Italian-Glossary-Nautical-Terms.pdf, inglese-spagnolo https://icdept.cgaux.org/pdf_files/English-Spanish-Glossary-Nautical-Terms.pdf, inglese-francese https://icdept.cgaux.org/pdf_files/English-French-Glossary-Nautical-Terms.pdf, stato letto. Peso C: utile come secondo riscontro sulle coppie di base. Il traduttore sceglie spesso il senso sbagliato delle parole polisemiche (reef come arrecife e tête de roche, tack solo come bordada o point d'amure, beam reach come bord de largue). Lo spagnolo ha tratti americani (güinche, gansera, espí, osta) e traduce close-hauled con navegar de bolina.

## Fonti deboli, solo come spunto

- Blog di noleggio e cantieri: https://www.samboat.fr/blog/glossaire-de-la-navigation, https://blog.clickandboat.com, https://vvanat.fr/blog/. Nei risultati letti non c'era indicazione di fonti.
- EFDeportes, rivista digitale argentina di educazione fisica: articoli divulgativi sulla vela, per esempio https://efdeportes.com/efd37/vela.htm e https://efdeportes.com/efd150/iniciacion-a-la-vela-ligera.htm, stato letto per i nomi spagnoli delle andature (ceñida, descuartelar, través, largo, aleta, empopada) con gli angoli. Gli angoli variano tra un articolo e l'altro. Peso C: utile per l'uso spagnolo corrente, non come prova.
- Glossari di tipo wiki, come https://franco.wiki/fr/Glossaire_maritime.html e https://areq.net/lang/fr/Glossaire_maritime.html.
- Wikipedia, Glossary of nautical terms: la pagina stessa segnala che servono ulteriori citazioni.
- Forum e discussioni di appassionati.

## Lacune da colmare

- Confermare a mano gli indirizzi delle singole voci di Garzanti, CNRTL, Oxford e Merriam-Webster.
- Leggere il glossario INCUAL e il manuale della Fundación MAPFRE per il lessico del diporto in spagnolo. Per l'inglese manca ancora una fonte autorevole sul diporto.
- Regolamento di Regata 2025-2028: trovata la versione spagnola. Mancano la traduzione italiana (sul sito FIV c'è solo la normativa nazionale 2026 che la richiama) e il testo francese integrale.
