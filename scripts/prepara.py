#!/usr/bin/env python3
"""Prepara una nuova voce partendo da un termine e dalle fonti conosciute.
Uso: python3 scripts/prepara.py COMANDO ...

  cerca TERMINE LINGUA [--contesti=N]   ricerca locale: non scrive nulla e non usa la rete
  scarica TERMINE LINGUA                aggiunge le pagine delle fonti scaricabili
  crea TERMINE LINGUA                   crea una scheda nuova
  aggiungi ID                           controlla la scheda e la inserisce in voci.json

  pagina SIGLA URL                      salva una pagina indicata a mano
  prova                                 misura la qualità delle proposte sulle voci esistenti

LINGUA è eng, esp, fra o ita. "prepara.py TERMINE LINGUA" equivale a cerca. Un termine
di più parole va tra virgolette.

scarica  cerca il termine e tutti i candidati in Treccani, Larousse, AHD e DEI, rispettando
         robots.txt, e salva le pagine in fonti scaricate/ aggiornando indice.tsv.
crea     scrive schede/ID.json con la voce proposta e le citazioni da verificare, leggendo
         tutte le pagine in archivio, di qualsiasi peso, comprese quelle salvate a mano.
         Serve solo per le schede nuove: se esiste già, non la tocca.
aggiungi inserisce la voce in fondo a voci.json. Rifiuta la scheda se manca categoria,
         definizione o genere, se una citazione ha ancora "ok": false, se un termine
         resta senza fonte, se un termine è già in un'altra voce non indicata in
         "senso_diverso_da" o se valida.py trova errori.
pagina   serve per esempio per una scheda OQLF-GDT: il sito vieta ai programmi la pagina
         di ricerca, quindi va cercata dal browser.

Nella scheda ogni citazione va letta, insieme all'eventuale avviso sui limiti dell'opera:
si mette "ok": true se il brano ha il senso giusto, altrimenti si cancella. Definizione
e nota si scrivono da zero.

cerca stampa:

1. la voce di data/voci.json che contiene già il termine, se c'è;
2. gli equivalenti trovati nei glossari multilingui, ordinati per punti: ogni opera
   che li attesta vale 3 se ha peso A per quella lingua, 2 se B, 1 se C, e le copie contano
   una volta sola. Se per una lingua non c'è un riscontro diretto, passa da un equivalente
   in un'altra lingua e lo segnala;
3. i riscontri nei testi di tutte le fonti, con il contesto da leggere per capire il senso,
   e gli avvisi di FONTI.md sulle opere trovate.

Un riscontro non prova il senso: va letto prima di citare la fonte.

prova cerca il termine preferito di ogni voce esistente e misura quante volte
gli equivalenti proposti coincidono con quelli della voce. Le voci sono state scritte
usando queste stesse fonti, quindi il risultato è ottimistico.

Per leggere le colonne dei PDF serve pypdf: senza, quei glossari vengono saltati.
"""
import csv
import glob
import http.client
import json
import logging
import os
import re
import string
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date
from html import unescape
from io import BytesIO
from itertools import product

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfoltisci import COPIE, cita  # noqa: E402
from valida import CATEGORIE, LINGUE, LINGUE_CON_GENERE, SLUG, livelli, piega  # noqa: E402

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCARICATE = os.path.join(RADICE, 'fonti scaricate')
LOCALI = os.path.join(RADICE, 'fonti locali')
SCHEDE = os.path.join(RADICE, 'schede')
PUNTI = {'A': 3, 'B': 2, 'C': 1}
AGENTE = 'Mozilla/5.0 (compatible; dictionary-lookup/1.0)'
ATTESA = 1.5  # secondi tra due richieste
MASSIMO = 100_000_000  # byte: oltre, la pagina non si salva, per non archiviare un file troncato
RINVII = 5
VIETATO, TROPPO_GRANDE = -1, -2  # esiti di Rete.apri che non sono codici http
FILE_GLOSSARIO = {  # letti come tabelle: le altre pagine delle stesse opere si leggono come testo
    'FFV-ESP/dico_FRA_ESP.PDF', 'FFV-GBR/dico_FRA_GBR.PDF', 'FFV-ITA/dico_FRA_ITA.PDF', 'LF/RC8WN616716.pdf',
    'MF/inglita.htm', 'MF/itaing.htm', 'RFEV-DIC/Diccionario_Nautico_de_la_FEV.pdf', 'TC-AC/copaamerica.xml',
    'TC-NAU/esportsnautics.xml', 'UNIOVI/es-en.html', 'USCG/English-French-Glossary-Nautical-Terms.pdf',
    'USCG/English-Italian-Glossary-Nautical-Terms.pdf', 'USCG/English-Spanish-Glossary-Nautical-Terms.pdf',
    'WW/Dizionario_Italiano_inglese.pdf',
}
DIZIONARI = {'eng': 'AHD', 'esp': 'DEI', 'fra': 'LAR', 'ita': 'TRE'}
GENERI = defaultdict(Counter)  # (lingua, chiave) -> generi indicati dai glossari
MARCA_NAUTICA = re.compile(r'marin|nautic|nautiq|naval|navire|\bvel[ae]\b|voile|sail|embarcac|bateau|barca|boat|ship')
AREE_TC = {'Vela', 'Esports nàutics', 'Motonàutica'}  # le altre aree danno sensi diversi (FONTI.md)
LINGUE_TC = {'en': 'eng', 'es': 'esp', 'fr': 'fra', 'it': 'ita'}
ARTICOLI = {
    'eng': ('to ', 'the ', 'a ', 'an '),
    'esp': ('el ', 'la ', 'los ', 'las '),
    'fra': ('le ', 'la ', 'les ', "l'", 'l’'),
    'ita': ('il ', 'lo ', 'la ', 'i ', 'gli ', 'le ', "l'", 'l’'),
}
PAROLE_LEGAME = {'a', 'al', 'all', 'alla', 'au', 'aux', 'con', 'd', 'da', 'de', 'dei', 'del', 'della', 'dello',
                 'des', 'di', 'du', 'en', 'in', 'l', 'of', 'per', 'sur'}
ARTICOLI_OGGETTO = {  # già piegati: l'apostrofo diventa uno spazio
    'eng': {'a', 'an', 'the'},
    'esp': {'el', 'la', 'los', 'las', 'un', 'una'},
    'fra': {'le', 'la', 'les', 'l', 'un', 'une'},
    'ita': {'il', 'lo', 'la', 'i', 'gli', 'le', 'l', 'un', 'uno', 'una'},
}
INVARIABILI_ITA = {'boma'}
SINGOLARI_ITA = set()  # parole in -a dei glossari italiani, per riconoscere i plurali in -e


class Tabella(dict):
    """Piega un carattere in uno solo, così il testo piegato resta allineato all'originale."""

    def __missing__(self, codice):
        c = chr(codice)
        if c in "-'’‐–":
            r = ' '
        else:
            r = ''.join(x for x in unicodedata.normalize('NFD', c.lower()) if not unicodedata.combining(x))
            if len(r) != 1:
                r = c
        self[codice] = r
        return r


TABELLA = Tabella()


def opera(sigla, lingua):
    """Le copie contano come una sola opera. FFV-ITA e FFV-ESP condividono la colonna francese."""
    if lingua == 'fra' and sigla == 'FFV-ESP':
        return 'FFV-ITA'
    return dict(COPIE).get(sigla, sigla)


def legature(s):
    return s.replace('œ', 'oe').replace('Œ', 'Oe').replace('æ', 'ae').replace('Æ', 'Ae')


def chiave(s):
    return re.sub(r'[^a-z0-9]+', ' ', legature(s).translate(TABELLA)).strip()


def plurale_ita(p):
    if p in INVARIABILI_ITA:
        return [p]
    if p.endswith(('cia', 'gia')):  # poggia può dare pogge o poggie
        return [p[:-2] + 'e', p[:-1] + 'e']
    if p.endswith(('ca', 'ga')):
        return [p[:-1] + 'he']
    if p.endswith('a'):
        return [p[:-1] + 'e']
    if p.endswith(('cco', 'ggo')):
        return [p[:-1] + 'hi']
    if p.endswith(('co', 'go')):  # lasco, laschi ma tattico, tattici
        return [p[:-1] + 'hi', p[:-1] + 'i']
    if p.endswith('io'):
        return [p[:-1]]
    if p.endswith('o'):
        return [p[:-1] + 'i']
    if p.endswith('e'):  # vele è già il plurale di vela, non una parola da volgere in veli
        return [p] if p[:-1] + 'a' in SINGOLARI_ITA else [p[:-1] + 'i']
    return [p]


def plurale_parola(p, lingua):
    """Le forme plurali regolari di una parola già piegata."""
    if lingua == 'ita':
        return plurale_ita(p)
    if lingua == 'esp':
        if p.endswith('z'):
            return [p[:-1] + 'ces']
        return [p + 's' if p[-1] in 'aeiou' else p + 'es']
    if lingua == 'fra':
        if p.endswith(('s', 'x', 'z')):
            return [p]
        if p.endswith(('au', 'eu')):
            return [p + 'x']
        if p.endswith('al'):  # chenal, chenaux ma naval, navals
            return [p[:-2] + 'aux', p + 's']
        return [p + 's']
    if p.endswith('ss') or p.endswith(('x', 'z', 'ch', 'sh')):
        return [p + 'es']
    if p.endswith('s'):
        return [p]
    if len(p) > 1 and p[-1] == 'y' and p[-2] not in 'aeiou':
        return [p[:-1] + 'ies']
    return [p + 's']


def varianti(termine, lingua):
    """Il termine e i suoi plurali regolari, già piegati. In inglese cambia l'ultima parola,
    nelle altre lingue le parole prima della prima preposizione (punto di scotta, punti di scotta)."""
    k = chiave(termine)
    parole = k.split()
    if not parole:
        return set()
    if lingua == 'eng':
        scelte = [[p] for p in parole[:-1]] + [plurale_parola(parole[-1], lingua)]
    else:
        scelte, legato = [], False
        for p in parole:
            legato = legato or p in PAROLE_LEGAME
            scelte.append([p] if legato else plurale_parola(p, lingua))
    return {k} | {' '.join(x) for x in product(*scelte)}


def pulisci(cella, lingua):
    """Da una cella di glossario ai singoli termini, senza parentesi e articoli."""
    testo = re.sub(r'\([^)]*\)|\[[^]]*\]', ' ', cella or '')
    termini = []
    for t in re.split(r'\s*[,;/]\s*|\s+[-–]\s+', testo):
        t = re.sub(r'\s+', ' ', t).strip(' .:*!?"«»')
        minuscolo = t.lower()
        for a in ARTICOLI[lingua]:
            if minuscolo.startswith(a) and len(t) > len(a) + 1:
                t = t[len(a):]
                break
        k = chiave(t)
        if len(k) >= 2 and not k.isdigit() and len(k.split()) <= 6 and ':' not in t:
            termini.append(t)
    return termini


def riga(sigla, url=None, **celle):
    termini = {l: pulisci(c, l) for l, c in celle.items()}
    return (sigla, {l: x for l, x in termini.items() if x}, url)


def segna_genere(lingua, termini, categoria):
    """Da 'n m', 'n f', 's.m.', 's.f.', 'v tr' al genere dello schema."""
    c = (categoria or '').lower().replace('.', ' ').split()
    g = 'm' if c[:2] in (['n', 'm'], ['s', 'm']) else 'f' if c[:2] in (['n', 'f'], ['s', 'f']) else 'v' if c[:1] == ['v'] else None
    if g:
        for t in termini:
            GENERI[(lingua, chiave(t))][g] += 1


def percorsi(sigla, modello):
    """I file di glossario dell'opera, o il loro testo estratto."""
    return [p for p in sorted(glob.glob(os.path.join(SCARICATE, sigla, modello)))
            if os.path.relpath(p, SCARICATE).removesuffix('.txt') in FILE_GLOSSARIO]


def leggi(percorso):
    with open(percorso, encoding='utf-8', errors='replace') as f:
        return f.read()


def righe_pdf(percorso):
    """Righe del PDF con le colonne separate da almeno due spazi."""
    ris = []
    for pagina in PdfReader(percorso).pages:
        ris += [x.strip() for x in pagina.extract_text(extraction_mode='layout').split('\n') if x.strip()]
    return ris


def colonne(testo):
    return re.split(r'\s{2,}', testo.strip())


def da_termcat(sigla, nome, aree):
    ris = []
    for p in percorsi(sigla, nome):
        for fitxa in ET.parse(p).getroot().iter('fitxa'):
            if aree and not {(a.text or '').strip() for a in fitxa.findall('areatematica')} & aree:
                continue
            termini = defaultdict(list)
            for d in fitxa.findall('denominacio'):
                l = LINGUE_TC.get(d.get('llengua'))
                if l:
                    puliti = pulisci(d.text, l)
                    termini[l] += puliti
                    segna_genere(l, puliti, d.get('categoria'))
            if len(termini) >= 2:
                ris.append((sigla, dict(termini), None))
    return ris


def da_rfev():
    ris = []
    for p in percorsi('RFEV-DIC', '*.pdf'):
        for x in righe_pdf(p):
            c = colonne(x)
            if len(c) == 3 and not c[0].isupper():
                ris.append(riga('RFEV-DIC', esp=c[0], fra=c[1], eng=c[2]))
    return ris


def da_uscg():
    ris = []
    for nome, l in (('Italian', 'ita'), ('Spanish', 'esp'), ('French', 'fra')):
        for p in percorsi('USCG', f'English-{nome}-*.pdf'):
            for x in righe_pdf(p):
                c = colonne(x)
                if len(c) == 2 and c[0] != c[1]:
                    ris.append(riga('USCG', url=os.path.basename(p), **{'eng': c[0], l: c[1]}))
    return ris


def da_ffv(sigla, nome, l):
    ris = []
    for p in percorsi(sigla, nome):
        for x in righe_pdf(p):
            c = colonne(re.sub(r'^(\d+|[A-Z])\s+', '', x))
            if len(c) == 2:
                ris.append(riga(sigla, **{'fra': c[0], l: c[1]}))
    return ris


def da_rl():
    """Il glossario locale ha le pagine ruotate: le colonne si leggono dalle coordinate."""
    ris = []
    for p in glob.glob(os.path.join(LOCALI, 'Diccionario*.pdf')):
        for pagina in PdfReader(p).pages:
            pezzi = []

            def visita(testo, cm, tm, _font, _corpo):
                if testo.strip():
                    x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
                    y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
                    pezzi.append((x, y, testo.strip()))

            pagina.extract_text(visitor_text=visita)
            pezzi.sort()
            gruppi, ultimo = [], None
            for x, y, t in pezzi:
                if ultimo is None or x - ultimo > 2:
                    gruppi.append({})
                ultimo = x
                n = min(range(4), key=lambda i: abs(y - (29 + 197 * i)))
                gruppi[-1][n] = (gruppi[-1].get(n, '') + ' ' + t).strip()
            for g in gruppi:
                if len(g) >= 2:
                    ris.append(riga('RL', esp=g.get(0), fra=g.get(1), eng=g.get(2), ita=g.get(3)))
    return ris


def da_due_punti(sigla, modello, a, b, separatore=r'\s*:\s*'):
    ris = []
    for p in percorsi(sigla, modello):
        for x in leggi(p).split('\n'):
            c = re.split(separatore, x.strip(), maxsplit=1)
            if len(c) == 2 and c[0] and c[1]:
                url = os.path.basename(p)[:-4] if sigla == 'MF' else None
                ris.append(riga(sigla, url=url, **{a: c[0], b: c[1]}))
    return ris


def da_gln():
    ris = []
    for p in sorted(glob.glob(os.path.join(LOCALI, 'glenans*.txt'))):
        for x in leggi(p).split('\n'):
            c = x.strip().split(':', 1)
            if len(c) == 2 and c[0] and c[1]:
                ris.append(riga('GLN', fra=c[0], ita=c[1]))
    return ris


def da_uniovi():
    ris = []
    for p in percorsi('UNIOVI', '*.txt'):
        for x in leggi(p).split('\n'):
            c = x.strip().split(' - ')
            if len(c) == 2:
                ris.append(riga('UNIOVI', esp=c[0], eng=c[1]))
    return ris


def da_lf():
    ris = []
    for p in percorsi('LF', '*.txt'):
        for m in re.finditer(r"^\s*([A-ZÀ-Ü][A-ZÀ-Ü' ]+?)\s*\(([^)]+)\)\s*:", leggi(p), re.M):
            ris.append(riga('LF', ita=m.group(1), eng=m.group(2)))
    return ris


def da_ww():
    """Lemma: (categoria) (ambito) equivalente inglese, poi la definizione con la maiuscola."""
    ris = []
    schema = re.compile(r'^([^:\n]{2,40}):\s*\(([^)]*)\)\s*(?:\[A\]\.\s*)?\([^)]*\)\s*([a-z][^A-Z\n]*?)\s+[A-ZÀ-Ü]', re.M)
    for p in percorsi('WW', '*.txt'):
        for m in schema.finditer(leggi(p)):
            ris.append(riga('WW', ita=m.group(1), eng=m.group(3)))
            segna_genere('ita', pulisci(m.group(1), 'ita'), m.group(2))
    return ris


def carica_righe():
    """Tutte le righe dei glossari: (sigla, {lingua: [termini]})."""
    logging.disable(logging.WARNING)
    ris = da_termcat('TC-NAU', 'esportsnautics.xml', AREE_TC) + da_termcat('TC-AC', 'copaamerica.xml', None)
    ris += da_gln() + da_uniovi() + da_lf() + da_ww()
    ris += da_due_punti('FFV-GBR', '*.txt', 'fra', 'eng', r'\s*[:;]\s*')
    ris += da_due_punti('MF', 'itaing.htm.txt', 'ita', 'eng') + da_due_punti('MF', 'inglita.htm.txt', 'eng', 'ita')
    if PdfReader:
        ris += da_rfev() + da_uscg() + da_rl()
        ris += da_ffv('FFV-ITA', '*.PDF', 'ita') + da_ffv('FFV-ESP', '*.PDF', 'esp')
    else:
        print('AVVISO: pypdf non installato, salto RFEV-DIC, USCG, RL, FFV-ITA e FFV-ESP')
    return [r for r in ris if len(r[1]) >= 2]


class Indice:
    def __init__(self, righe, catalogo):
        self.righe = righe
        self.catalogo = catalogo
        self.mappa = defaultdict(set)
        self.composti = defaultdict(set)  # inglese senza spazi -> grafie attestate (mainsheet, main sheet)
        for n, r in enumerate(righe):
            for l, lista in r[1].items():
                for t in lista:
                    k = chiave(t)
                    self.mappa[(l, k)].add(n)
                    if l == 'eng':
                        self.composti[k.replace(' ', '')].add(k)
                    elif l == 'ita':
                        SINGOLARI_ITA.update(p for p in k.split() if p.endswith('a'))

    def forme(self, termine, lingua):
        """Le varianti del termine e, in inglese, le grafie unite o staccate dei glossari."""
        ris = set(varianti(termine, lingua))
        if lingua == 'eng':
            for k in list(ris):
                ris |= self.composti.get(k.replace(' ', ''), set())
        return ris

    def trova(self, termine, lingua):
        return {n for k in self.forme(termine, lingua) for n in self.mappa.get((lingua, k), ())}

    def raccogli(self, numeri, escluse):
        """Per ogni lingua, i termini delle righe date con le opere che li attestano."""
        ris = {l: defaultdict(lambda: {'sigle': set(), 'forme': Counter()}) for l in LINGUE if l not in escluse}
        for n in numeri:
            sigla, termini, _ = self.righe[n]
            for l, lista in termini.items():
                if l in ris and l in self.catalogo.get(sigla, {}):
                    for t in lista:
                        ris[l][chiave(t)]['sigle'].add(sigla)
                        ris[l][chiave(t)]['forme'][t] += 1
        return ris

    def ordina(self, gruppo, lingua, via=None):
        """Unisce singolare, plurale e grafie dello stesso composto e ordina per punti."""
        for k in sorted(gruppo, key=len):
            if k not in gruppo:
                continue
            for v in self.forme(k, lingua) - {k}:
                if v in gruppo:
                    gruppo[k]['sigle'] |= gruppo[v]['sigle']
                    gruppo[k]['forme'] += gruppo.pop(v)['forme']
        lista = []
        for k, g in gruppo.items():
            sigle = sorted(g['sigle'], key=lambda s: (self.catalogo[s][lingua], s))
            migliori = {}
            for s in sigle:
                o = opera(s, lingua)
                migliori[o] = max(migliori.get(o, 0), PUNTI[self.catalogo[s][lingua]])
            lista.append({'chiave': k, 'termine': g['forme'].most_common(1)[0][0].lower(), 'sigle': sigle, 'via': via,
                          'punti': sum(migliori.values()), 'opere': len(migliori)})
        return sorted(lista, key=lambda c: (-c['punti'], -c['opere'], c['chiave']))

    def candidati(self, termine, lingua):
        diretti = self.raccogli(self.trova(termine, lingua), {lingua})
        ris = {l: self.ordina(g, l) for l, g in diretti.items()}
        solo_diretti = {l: list(c) for l, c in ris.items()}
        for l, lista in solo_diretti.items():
            indiretti = self.indiretti(solo_diretti, l)
            if not lista:
                ris[l] = indiretti
                continue
            # hisser une voile è diretto, hisser arriva da hoist: il verbo senza complemento entra solo
            # se dopo viene un articolo, perché lunghezza non vale lunghezza fuori tutto
            noti = {c['chiave'] for c in lista}
            basi = [c for c in indiretti if c['chiave'] not in noti and any(
                d.startswith(c['chiave'] + ' ') and d[len(c['chiave']) + 1:].split()[0] in ARTICOLI_OGGETTO[l]
                for d in noti)]
            ris[l] = sorted(lista + basi, key=lambda c: (-c['punti'], -c['opere'], c['chiave']))
        return ris

    def indiretti(self, diretti, l):
        """I termini della lingua l raggiunti dai primi equivalenti diretti delle altre lingue."""
        passaggi = defaultdict(lambda: {'sigle': set(), 'forme': Counter()})
        origine = {}
        for p, lista in diretti.items():
            if p == l:
                continue
            for c in lista[:2]:
                for k, g in self.raccogli(self.trova(c['termine'], p), {p})[l].items():
                    passaggi[k]['sigle'] |= g['sigle']
                    passaggi[k]['forme'] += g['forme']
                    origine.setdefault(k, c['termine'])
        ordinati = self.ordina(passaggi, l)
        for c in ordinati:
            c['via'] = origine.get(c['chiave'])
        return ordinati


def carica_catalogo():
    with open(os.path.join(RADICE, 'data', 'fonti.json'), encoding='utf-8') as f:
        return {c['sigla']: c.get('pesi', {}) for c in json.load(f)['fonti']}


def carica_voci():
    with open(os.path.join(RADICE, 'data', 'voci.json'), encoding='utf-8') as f:
        return json.load(f)['voci']


def testi_fonti(catalogo):
    ris = defaultdict(list)
    for s in catalogo:
        if s == 'RL':
            file = [p for p in glob.glob(os.path.join(LOCALI, '*.txt')) if 'glenans' not in os.path.basename(p)]
        elif s == 'GLN':
            file = glob.glob(os.path.join(LOCALI, 'glenans*.txt'))
        else:
            file = glob.glob(os.path.join(SCARICATE, s, '**', '*.txt'), recursive=True)
        for p in sorted(file):
            t = legature(leggi(p))
            ris[s].append((t, t.translate(TABELLA)))
    return ris


def contesti(testi, forme):
    forme = sorted(forme, key=len, reverse=True)
    schema = re.compile(r'(?<![a-z0-9])(?:' + '|'.join(r'\s+'.join(map(re.escape, f.split())) for f in forme)
                        + r')(?![a-z0-9])')
    n, esempi = 0, []
    for originale, piegato in testi:
        for m in schema.finditer(piegato):
            n += 1
            if len(esempi) < 12:
                brano = re.sub(r'\s+', ' ', originale[max(0, m.start() - 60):m.end() + 60]).strip()
                esempi.append(brano)
    return n, esempi


def avvisi_fonti():
    """Dalla sezione di FONTI.md sui limiti: {sigla: testo dell'avviso}."""
    with open(os.path.join(RADICE, 'FONTI.md'), encoding='utf-8') as f:
        testo = f.read()
    sezione = testo.split('## Fonti valide solo per una parte del vocabolario')[-1].split('\n## ')[0]
    ris = {}
    for m in re.finditer(r'^- \*\*(.+?)\*\*:\s*(.+)$', sezione, re.M):
        for s in re.findall(r'[A-Z][A-Z0-9-]+', m.group(1)):
            ris[s] = m.group(2)
    return ris


def opere_parziali(catalogo):
    """Opere a schede di cui l'archivio ha solo le pagine già consultate: almeno 5 pagine
    distinte, escluse quelle con la numerazione ?page=, che sono glossari scaricati per intero."""
    pagine = defaultdict(set)
    with open(os.path.join(SCARICATE, 'indice.tsv'), encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            pagine[r['sigla']].add(r['url'])
    schede = {s for s, u in pagine.items() if s in catalogo and len(u) >= 5 and not any('page=' in x for x in u)}
    return schede | set(DIZIONARI.values())


def stampa(termine, lingua, indice, voci, n_contesti):
    k = indice.forme(termine, lingua)
    presenti =[v['id'] for v in voci if any(chiave(x['t']) in k for x in v.get(lingua) or [])]
    print(f'{termine} ({lingua})')
    print('Già in voci.json: ' + (', '.join(presenti) if presenti else 'no'))

    print('\nEquivalenti nei glossari')
    for l, lista in indice.candidati(termine, lingua).items():
        print(f'  {l}')
        if not lista:
            print('    nessuno')
        for c in lista[:8]:
            via = f"  [indiretto, via {c['via']}]" if c['via'] else ''
            print(f"    {c['termine']:32} {c['punti']:2}  {', '.join(c['sigle'])}{via}")

    catalogo = indice.catalogo
    testi = testi_fonti(catalogo)
    avvisi = avvisi_fonti()
    trovate = []
    for s, pesi in catalogo.items():
        if lingua in pesi and s in testi:
            n, esempi = contesti(testi[s], k)
            if n:
                trovate.append((pesi[lingua], s, n, esempi))
    print('\nRiscontri nei testi (da leggere: il senso può essere diverso)')
    if not trovate:
        print('  nessuno')
    for peso, s, n, esempi in sorted(trovate, key=lambda x: (x[0], -x[2], x[1])):
        print(f'  {peso} {s}: {n}')
        for e in esempi[:n_contesti]:
            print(f'      ... {e} ...')

    nomi = sorted({s for _, s, _, _ in trovate} & set(avvisi))
    falsi = [s for s in nomi if any(chiave(x) in k for x in re.findall(r'\*([^*]+)\*', avvisi[s]))]
    if falsi:
        print('\nATTENZIONE, FONTI.md segnala questo termine per:')
        for s in falsi:
            print(f'  {s}: {avvisi[s]}')
    altre = [s for s in nomi if s not in falsi]
    if altre:
        print('\nOpere con limiti di ambito in FONTI.md: ' + ', '.join(altre))
    assenti = sorted(s for s, p in catalogo.items() if lingua in p and s not in testi and s not in ('TC-NAU', 'TC-AC'))
    if assenti:
        print('Non consultabili in locale per questa lingua: ' + ', '.join(assenti))
    parziali = sorted(s for s in opere_parziali(catalogo) if lingua in catalogo[s])
    if parziali:
        print('Consultabili solo nelle pagine già scaricate, un mancato riscontro non vale: ' + ', '.join(parziali))


def prova(indice, voci):
    """Per ogni voce cerca il termine preferito e confronta gli equivalenti con quelli della voce."""
    conta = defaultdict(Counter)
    for v in voci:
        for da in LINGUE:
            risultato = indice.candidati(v[da][0]['t'], da)
            for a, lista in risultato.items():
                giusti = set()
                for x in v[a]:
                    giusti |= indice.forme(x['t'], a)
                for chi in ('tutte', f'{da}>{a}'):
                    conta[chi]['casi'] += 1
                    if not lista:
                        conta[chi]['vuoti'] += 1
                        continue
                    chiavi = [c['chiave'] for c in lista]
                    conta[chi]['primo'] += chiavi[0] in giusti
                    conta[chi]['primi3'] += any(k in giusti for k in chiavi[:3])
                    conta[chi]['tutti'] += any(k in giusti for k in chiavi)
                    conta[chi]['indiretti'] += bool(lista[0]['via'])
    print(f"{'':10}{'casi':>6}{'primo':>8}{'primi 3':>9}{'in lista':>10}{'nessuno':>9}{'indiretti':>11}")
    for chi in ['tutte'] + sorted(k for k in conta if k != 'tutte'):
        c = conta[chi]
        perc = lambda x: f'{round(100 * c[x] / c["casi"])}%'
        print(f"{chi:10}{c['casi']:>6}{perc('primo'):>8}{perc('primi3'):>9}{perc('tutti'):>10}"
              f"{perc('vuoti'):>9}{perc('indiretti'):>11}")


class NonSeguire(urllib.request.HTTPRedirectHandler):
    """I rinvii si seguono a mano, per controllare robots.txt prima di ogni richiesta."""

    def redirect_request(self, *_):
        return None


def esito(codice):
    if codice == VIETATO:
        return 'vietato da robots.txt'
    if codice == TROPPO_GRANDE:
        return f'file oltre {MASSIMO // 1_000_000} MB, non salvato'
    return f'il sito risponde {codice or "con un errore"}'


class Rete:
    """Richieste lente, con un agente generico e nel rispetto di robots.txt."""

    def __init__(self):
        self.robots = {}
        self.ultima = 0
        self.client = urllib.request.build_opener(NonSeguire)

    def richiesta(self, url):
        """Una sola richiesta: restituisce (codice, indirizzo del rinvio, contenuto)."""
        attesa = self.ultima + ATTESA - time.time()
        if attesa > 0:
            time.sleep(attesa)
        self.ultima = time.time()
        try:
            richiesta = urllib.request.Request(url, headers={'User-Agent': AGENTE})
            with self.client.open(richiesta, timeout=25) as r:
                corpo = r.read(MASSIMO + 1)
                if len(corpo) > MASSIMO:
                    return TROPPO_GRANDE, None, b''
                return r.status, None, corpo
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get('Location'), b''
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError, ValueError):
            return 0, None, b''

    def apri(self, url, controlla=True):
        """Restituisce (codice, indirizzo finale, contenuto). Con controlla, nessuna
        richiesta parte verso un indirizzo vietato, nemmeno dopo un rinvio."""
        for _ in range(RINVII + 1):
            if controlla and not self.permesso(url):
                return VIETATO, url, b''
            codice, rinvio, corpo = self.richiesta(url)
            if codice not in (301, 302, 303, 307, 308) or not rinvio:
                return codice, url, corpo
            url = urllib.parse.quote(urllib.parse.urljoin(url, rinvio), safe=string.punctuation)
            if urllib.parse.urlparse(url).scheme not in ('http', 'https'):
                return 0, url, b''
        return 0, url, b''

    def permesso(self, url):
        p = urllib.parse.urlparse(url)
        sito = f'{p.scheme}://{p.netloc}'
        if sito not in self.robots:
            codice, _, corpo = self.apri(sito + '/robots.txt', controlla=False)
            if codice == 200:
                regole = urllib.robotparser.RobotFileParser()
                regole.parse(corpo.decode('utf-8', 'replace').splitlines())
            else:
                regole = codice == 404  # senza robots.txt si può leggere, se il sito non risponde no
            self.robots[sito] = regole
        regole = self.robots[sito]
        return regole if isinstance(regole, bool) else regole.can_fetch(AGENTE, url)


def decodifica(corpo):
    """UTF-8 se è valido, altrimenti la codifica dichiarata nella pagina, altrimenti Windows-1252."""
    try:
        return corpo.decode('utf-8-sig')
    except UnicodeDecodeError:
        pass
    m = re.search(rb'charset\s*=\s*["\']?([\w.:-]+)', corpo[:4096], re.I)
    nome = m.group(1).decode('ascii', 'ignore').lower() if m else ''
    if nome in ('utf-8', 'utf8'):
        return corpo.decode('utf-8', 'replace')
    if nome and nome not in ('iso-8859-1', 'latin1', 'latin-1'):  # i browser leggono latin1 come 1252
        try:
            return corpo.decode(nome)
        except (LookupError, UnicodeDecodeError):
            pass
    return corpo.decode('cp1252', 'replace')


def titolo(corpo):
    m = re.search(rb'<title[^>]*>(.*?)</title>', corpo, re.S | re.I)
    return unescape(decodifica(m.group(1))).strip() if m else ''


def testo_html(corpo):
    t = decodifica(corpo)
    t = re.sub(r'(?s)<!--.*?-->', '', t)
    t = re.sub(r'(?is)<(script|style|noscript)\b.*?</\1>', '', t)
    t = re.sub(r'(?is)<br\s*/?>|</(p|div|li|h\d|tr)>', '\n', t)
    t = unescape(re.sub(r'<[^>]+>', ' ', t))
    return re.sub(r'\n\s*\n+', '\n\n', re.sub(r'[ \t]+', ' ', t))


def testo_pdf(corpo):
    """Il testo del PDF, vuoto se manca pypdf o se il file non si legge."""
    if not PdfReader:
        return ''
    try:
        return '\n'.join(x.extract_text() or '' for x in PdfReader(BytesIO(corpo)).pages)
    except Exception:
        return ''


def righe_indice():
    with open(os.path.join(SCARICATE, 'indice.tsv'), encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def salva_pagina(sigla, url, corpo):
    """Salva la pagina e il suo testo, e la registra nell'indice se è nuova."""
    url = url.split('#')[0]
    if any(r['url'] == url and r['file'] for r in righe_indice()):
        return False
    p = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qs(p.query).get('q')
    parti = [x for x in p.path.split('/') if x] or ['pagina']
    nome = urllib.parse.unquote(q[0] if q else '_'.join(parti[-2:]) if parti[-1].isdigit() else parti[-1])
    estensione = '.pdf' if corpo.startswith(b'%PDF') else '.html'
    nome = re.sub(r'\.(pdf|html?)$', '', nome, flags=re.I)
    nome = re.sub(r'[^\w.-]+', '_', nome)[:100] or 'pagina'
    cartella = os.path.join(SCARICATE, sigla)
    os.makedirs(cartella, exist_ok=True)
    destinazione, n = os.path.join(cartella, nome + estensione), 2
    while os.path.exists(destinazione):
        destinazione, n = os.path.join(cartella, f'{nome}_{n}{estensione}'), n + 1
    testo = testo_pdf(corpo) if estensione == '.pdf' else testo_html(corpo)
    with open(destinazione, 'wb') as f:
        f.write(corpo)
    if testo.strip():
        with open(destinazione + '.txt', 'w', encoding='utf-8') as f:
            f.write(testo)
    else:
        print(f'AVVISO: nessun testo estratto da {os.path.relpath(destinazione, SCARICATE)}')
    with open(os.path.join(SCARICATE, 'indice.tsv'), 'a', encoding='utf-8') as f:
        f.write(f'{sigla}\t{url}\t{os.path.relpath(destinazione, SCARICATE)}\t200\t{date.today().isoformat()}\n')
    return True


def indirizzi(sigla, termine):
    """Gli indirizzi da provare in ordine, e se basta il primo che risponde."""
    basso = termine.lower()
    testa = chiave(termine).split()[0]
    q = urllib.parse.quote
    if sigla == 'TRE':
        return [f'https://www.treccani.it/vocabolario/{q(testa + s)}/' for s in ('', '1', '2', '3', '4', '5')]
    if sigla == 'LAR':
        return ['https://www.larousse.fr/dictionnaires/francais/' + q(basso)]
    if sigla == 'AHD':
        return ['https://ahdictionary.com/word/search.html?q=' + q(basso)]
    return [f'https://diccionario.raing.es/es/lema/{q(x)}' for x in dict.fromkeys((basso, basso.split()[0]))]


def pagina_valida(sigla, finale, corpo):
    if sigla == 'TRE':
        return '/vocabolario/' in finale
    if sigla == 'LAR':
        return titolo(corpo).startswith('Définitions')
    if sigla == 'AHD':
        return 'Entry:' in titolo(corpo)
    return True


def scarica_termine(rete, sigla, termine):
    noti = {r['url'] for r in righe_indice() if r['file']}
    trovate = 0
    for i, u in enumerate(indirizzi(sigla, termine)):
        # Treccani numera gli omonimi e il senso nautico può essere il secondo o il terzo,
        # anche quando esiste la pagina senza numero: si prosegue fino al primo numero che manca
        omonimi = sigla == 'TRE'
        if u in noti:
            trovate += 1
            print(f'  {sigla} {termine}: già presente ({u})')
            if omonimi:
                continue
            break
        codice, finale, corpo = rete.apri(u)
        if codice == 200 and pagina_valida(sigla, finale, corpo):
            trovate += 1
            nuova = salva_pagina(sigla, finale, corpo)
            print(f"  {sigla} {termine}: {'salvata' if nuova else 'già presente'} ({finale.split('#')[0]})")
            if omonimi:
                continue
            break
        if codice not in (200, 404):
            print(f'  {sigla} {termine}: {esito(codice)}')
            return
        if omonimi and i > 0:
            break
    if not trovate:
        print(f'  {sigla} {termine}: non trovato')


def scarica_candidati(termine, lingua, indice):
    rete = Rete()
    print('Dizionari online')
    risultato = indice.candidati(termine, lingua)
    scarica_termine(rete, DIZIONARI[lingua], termine)
    for l, lista in risultato.items():
        for c in lista:
            scarica_termine(rete, DIZIONARI[l], c['termine'])
    print('  OQLF-GDT: si cerca dal browser, poi si salva la pagina con: prepara.py pagina OQLF-GDT URL')


def relativo(sigla, url):
    """Indirizzo della citazione, relativo a quello dell'opera nel catalogo."""
    with open(os.path.join(RADICE, 'data', 'fonti.json'), encoding='utf-8') as f:
        c = next(x for x in json.load(f)['fonti'] if x['sigla'] == sigla)
    base = c.get('url') or (c.get('link') or [{}])[0].get('url') or ''
    if url == base:
        return None
    if url.startswith(base + '?'):
        return url[len(base):]
    if base.endswith('/') and url.startswith(base):
        return url[len(base):]
    return url


def forma_citata(forma, lemma, lingua):
    """Come la scrive la fonte; se è un plurale, con il termine della voce tra parentesi."""
    forma = forma.lower()
    return lemma.lower() if chiave(forma) == chiave(lemma) else f'{forma} ({lemma})'


def genere_noto(voci, lingua, termine):
    k = chiave(termine)
    for v in voci:
        for x in v.get(lingua) or []:
            if chiave(x['t']) == k and x.get('g'):
                return x['g']
    generi = GENERI.get((lingua, k))
    return generi.most_common(1)[0][0] if generi else ''


def termini_gia_presenti(voce, voci):
    """{id di una voce esistente: termini che ha in comune con questa}."""
    nuovi = {(l, chiave(x.get('t') or '')) for l in LINGUE for x in voce.get(l) or []}
    ris = {}
    for v in voci:
        comuni = [f"{l}: {x['t']}" for l in LINGUE for x in v.get(l) or [] if (l, chiave(x['t'])) in nuovi]
        if comuni:
            ris[v['id']] = comuni
    return ris


def costruisci_scheda(termine, lingua, indice, voci):
    catalogo = indice.catalogo
    risultato = indice.candidati(termine, lingua)
    da_cercare = {lingua: [(termine, None)]}
    for l, lista in risultato.items():
        da_cercare[l] = [(c['termine'], c['via']) for c in lista]
    base = indice.trova(termine, lingua)
    citazioni = {}

    def registra(sigla, url, l, forma, lemma, brano):
        c = citazioni.setdefault((sigla, url), {'sigla': sigla, 'termini': [], 'url': url, 'ok': False, 'pesi': {}, 'brani': []})
        scritta = forma_citata(forma, lemma, l)
        nuovo = scritta not in c['termini']  # ogni termine citato deve avere almeno un brano da leggere
        if nuovo:
            c['termini'].append(scritta)
        c['pesi'][l] = catalogo[sigla][l]
        if brano not in c['brani'] and (nuovo or len(c['brani']) < 4):
            c['brani'].append(brano)

    for l, lista in da_cercare.items():
        for t, via in lista:
            numeri = indice.trova(t, l)
            if l != lingua:
                ponte = indice.trova(via, next(p for p in LINGUE if p != l and any(
                    chiave(x[0]) == chiave(via) for x in da_cercare.get(p, [])))) if via else set()
                numeri = numeri & (base | ponte)
            for n in numeri:
                sigla, celle, url = indice.righe[n]
                brano = ' = '.join(f"{x}: {', '.join(y)}" for x, y in celle.items())
                # una riga può attestare anche i candidati delle altre lingue
                for l2, valori in celle.items():
                    if l2 not in catalogo.get(sigla, {}):
                        continue
                    for t2, _ in da_cercare.get(l2, []):
                        forme = indice.forme(t2, l2)
                        for f in valori:
                            if chiave(f) in forme:
                                registra(sigla, url, l2, f, t2, brano)

    pagine = [r for r in righe_indice() if r['file'] and r['file'].split('/')[0] in catalogo]
    parziali = opere_parziali(catalogo)
    impaginate = {r['sigla'] for r in pagine if 'page=' in r['url']}  # un glossario diviso in tante pagine
    fatti = set()
    for r in pagine:
        s = r['sigla']
        file_testo = os.path.join(SCARICATE, r['file'] + '.txt')
        if r['file'] in FILE_GLOSSARIO or not os.path.exists(file_testo):
            continue
        originale = None
        for l, lista in da_cercare.items():
            if l not in catalogo[s]:
                continue
            for i, (t, _) in enumerate(lista):
                k = chiave(t)
                if originale is None:
                    originale = legature(leggi(file_testo))
                    piegato = originale.translate(TABELLA)
                # un composto può stare nella scheda di una sua parola: punto di scotta sotto punto
                intestazione = chiave(r['url']) + ' ' + chiave(originale[:300])
                parole = [p for p in k.split() if p not in PAROLE_LEGAME] or [k]
                if s in parziali and not any(p in intestazione for p in parole):
                    continue
                dedicata = any((set(f.split()) - PAROLE_LEGAME or {f}) <= set(intestazione.split())
                               for f in indice.forme(t, l))
                # nelle altre opere un sinonimo conta solo se la pagina è dedicata a lui, altrimenti è rumore
                if i and s not in parziali and not dedicata:
                    continue
                # ogni pagina è una citazione, ma nelle opere a schede o impaginate una pagina
                # successiva conta solo se è dedicata al termine
                if (s, l, k) in fatti and (s in parziali or s in impaginate) and not dedicata:
                    continue
                schema = r'(?<![a-z0-9])(?:' + '|'.join(r'\s+'.join(map(re.escape, f.split())) for f in indice.forme(t, l)) + r')(?![a-z0-9])'
                trovati = list(re.finditer(schema, piegato))
                if not trovati:
                    continue
                # il brano deve mostrare il senso: si salta il titolo e si preferisce il contesto nautico
                corpo = [m for m in trovati if m.start() >= 300] or trovati
                nautici = [m for m in corpo if MARCA_NAUTICA.search(piegato[max(0, m.start() - 90):m.end() + 90])]
                for m in (nautici + [x for x in corpo if x not in nautici])[:3]:
                    forma = re.sub(r'\s+', ' ', originale[m.start():m.end()])
                    brano = re.sub(r'\s+', ' ', originale[max(0, m.start() - 90):m.end() + 90]).strip()
                    registra(s, relativo(s, r['url']), l, forma, t, brano)
                fatti.add((s, l, k))

    voce = {'id': '', 'categoria': ''}
    for l in LINGUE:
        scelto = termine if l == lingua else (risultato[l][0]['termine'] if risultato[l] else '')
        voce[l] = []
        if scelto:
            x = {'t': scelto}
            if l in LINGUE_CON_GENERE:
                x['g'] = genere_noto(voci, l, scelto)
            voce[l].append(x)
    principale = (voce['ita'] or voce[lingua])[0]['t']
    voce['id'] = '-'.join(chiave(principale).split())
    voce['definizione'] = ''
    voce['nota'] = ''
    ordinate = sorted(citazioni.values(), key=lambda c: (min(c['pesi'].values()), c['sigla']))
    avvisi = avvisi_fonti()
    uscita = []
    for c in ordinate:
        u = {'sigla': c['sigla'], 'termini': ', '.join(c['termini'])}
        if c['url']:
            u['url'] = c['url']
        u['ok'] = False
        if c['sigla'] in avvisi:
            u['avviso'] = avvisi[c['sigla']]
        u.update({'pesi': c['pesi'], 'brani': c['brani']})
        uscita.append(u)
    return {
        'istruzioni': 'Leggi ogni brano e l\'eventuale avviso sui limiti dell\'opera: metti ok a true se il senso è '
                      'giusto, altrimenti cancella la citazione. Completa categoria, generi, definizione e nota. '
                      'Se un termine è già in un\'altra voce e qui ha un senso diverso, metti l\'id di quella voce '
                      'in senso_diverso_da. Poi usa il comando aggiungi.',
        'gia_presenti': termini_gia_presenti(voce, voci),
        'senso_diverso_da': [],
        'voce': voce,
        'citazioni': uscita,
        'alternative': {l: [{'t': c['termine'], 'punti': c['punti'], 'sigle': c['sigle'], 'via': c['via']}
                            for c in lista[1:]] for l, lista in risultato.items()},
    }


def fonti_della_scheda(scheda):
    fonti = []
    for c in scheda.get('citazioni') or []:
        f = {'sigla': c.get('sigla'), 'termini': c.get('termini')}
        if c.get('url'):
            f['url'] = c['url']
        fonti.append(f)
    return fonti


def scrivi_scheda(termine, lingua, indice, voci):
    scheda = costruisci_scheda(termine, lingua, indice, voci)
    os.makedirs(SCHEDE, exist_ok=True)
    percorso = os.path.join(SCHEDE, scheda['voce']['id'] + '.json')
    if os.path.exists(percorso):
        print(f'ERRORE: la scheda esiste già, non la sovrascrivo: {percorso}')
        return 1
    with open(percorso, 'w', encoding='utf-8') as f:
        json.dump(scheda, f, ensure_ascii=False, indent=2)
        f.write('\n')
    prova_voce = dict(scheda['voce'], fonti=fonti_della_scheda(scheda))
    print(f"Scheda: {percorso}\n{len(scheda['citazioni'])} citazioni da verificare")
    print('Punteggio se tutte fossero confermate: ' + pallini(livelli(prova_voce, indice.catalogo)))
    for vid, comuni in scheda['gia_presenti'].items():
        print(f"ATTENZIONE, già nella voce {vid}: {'; '.join(comuni)}")
    print(f"Dopo averla completata: python3 scripts/prepara.py aggiungi {scheda['voce']['id']}")
    return 0


def pallini(lv):
    """Lo stesso formato di valida.py --punteggi, con la percentuale della voce."""
    perc = round(100 * sum(lv.values()) / (3 * len(LINGUE)))
    return f'{perc}%  ' + '  '.join(f"{l} {'●' * n}{'○' * (3 - n)}" for l, n in lv.items())


def riga_termini(lista):
    pezzi = []
    for x in lista:
        campi = [f'"t": {json.dumps(x["t"], ensure_ascii=False)}']
        if x.get('g'):
            campi.append(f'"g": {json.dumps(x["g"])}')
        pezzi.append('{ ' + ', '.join(campi) + ' }')
    return '[' + ', '.join(pezzi) + ']'


def blocco_voce(v):
    d = lambda x: json.dumps(x, ensure_ascii=False)
    righe = ['    {', f'      "id": {d(v["id"])},', f'      "categoria": {d(v["categoria"])},']
    righe += [f'      "{l}": {riga_termini(v[l])},' for l in LINGUE]
    righe.append(f'      "definizione": {d(v["definizione"])},')
    if v.get('nota'):
        righe.append(f'      "nota": {d(v["nota"])},')
    righe.append('      "fonti": [')
    citazioni = []
    for f in v['fonti']:
        campi = ', '.join(f'"{k}": {d(f[k])}' for k in ('sigla', 'termini', 'url') if k in f)
        citazioni.append('        { ' + campi + ' }')
    righe.append(',\n'.join(citazioni))
    righe += ['      ]', '    }']
    return '\n'.join(righe)


def controlla_scheda(scheda, voci, catalogo):
    v = scheda.get('voce') or {}
    errori = []
    if not isinstance(v.get('id'), str) or not SLUG.match(v['id']):
        errori.append(f"id non valido: {v.get('id')!r}")
    if v.get('id') in {x['id'] for x in voci}:
        errori.append(f"id già usato: {v['id']}")
    if v.get('categoria') not in CATEGORIE:
        errori.append('categoria mancante o non valida: ' + ', '.join(sorted(CATEGORIE)))
    if not (v.get('definizione') or '').strip():
        errori.append('definizione mancante')
    citazioni = scheda.get('citazioni') or []
    if not citazioni:
        errori.append('nessuna citazione')
    for c in citazioni:
        if c.get('ok') is not True:
            errori.append(f"citazione da verificare: {c.get('sigla')} ({c.get('termini')})")
        if c.get('sigla') not in catalogo:
            errori.append(f"sigla assente dal catalogo: {c.get('sigla')}")
    fonti = fonti_della_scheda(scheda)
    for l in LINGUE:
        if not v.get(l):
            errori.append(f'lingua {l}: serve almeno un termine')
        for x in v.get(l) or []:
            if l in LINGUE_CON_GENERE and x.get('g') not in ('m', 'f', 'loc', 'v'):
                errori.append(f"lingua {l}: genere mancante per {x.get('t')!r}")
            t = piega(x.get('t') or '')
            if not any(l in catalogo.get(f['sigla'], {}) and cita(f, t) for f in fonti):
                errori.append(f"lingua {l}: {x.get('t')!r} non ha una citazione che lo riporti")
    diversi = scheda.get('senso_diverso_da') or []
    for vid, comuni in termini_gia_presenti(v, voci).items():
        if vid not in diversi:
            errori.append(f"termini già nella voce {vid} ({'; '.join(comuni)}): "
                          'se il senso è diverso, metti quell\'id in senso_diverso_da')
    return errori


def aggiungi(percorso_scheda, percorso_voci):
    with open(percorso_scheda, encoding='utf-8') as f:
        scheda = json.load(f)
    with open(percorso_voci, encoding='utf-8') as f:
        testo = f.read()
    dati = json.loads(testo)
    catalogo = carica_catalogo()
    errori = controlla_scheda(scheda, dati['voci'], catalogo)
    if errori:
        print('Scheda non pronta, voci.json non modificato:')
        for e in errori:
            print('  ' + e)
        confermate = dict(scheda, citazioni=[c for c in scheda.get('citazioni') or [] if c.get('ok') is True])
        parziale = dict(scheda.get('voce') or {}, fonti=fonti_della_scheda(confermate))
        print('Punteggio con le citazioni già confermate: ' + pallini(livelli(parziale, catalogo)))
        return 1

    v = scheda['voce']
    voce = {'id': v['id'], 'categoria': v['categoria']}
    for l in LINGUE:
        voce[l] = [{k: x[k] for k in ('t', 'g') if x.get(k)} for x in v[l]]
    voce['definizione'] = v['definizione'].strip()
    if (v.get('nota') or '').strip():
        voce['nota'] = v['nota'].strip()
    voce['fonti'] = fonti_della_scheda(scheda)

    coda = re.search(r'\n    \}\n  \]\n\}\s*$', testo)
    if not coda:
        print('ERRORE: fine di voci.json inattesa, file non modificato')
        return 1
    nuovo = testo[:coda.start()] + '\n    },\n' + blocco_voce(voce) + testo[coda.start() + len('\n    }'):]
    if json.loads(nuovo)['voci'] != dati['voci'] + [voce]:
        print('ERRORE: il risultato non coincide con quello atteso, file non modificato')
        return 1

    with tempfile.TemporaryDirectory() as cartella:
        prova_file = os.path.join(cartella, 'voci.json')
        with open(prova_file, 'w', encoding='utf-8') as f:
            f.write(nuovo)
        controllo = subprocess.run([sys.executable, os.path.join(RADICE, 'scripts', 'valida.py'), prova_file,
                                    os.path.join(RADICE, 'data', 'fonti.json')], capture_output=True, text=True)
    if controllo.returncode != 0:
        print('valida.py ha trovato errori, voci.json non modificato:')
        print('\n'.join(x for x in controllo.stdout.splitlines() if x.startswith('ERRORE')))
        return 1
    with open(percorso_voci, 'w', encoding='utf-8') as f:
        f.write(nuovo)
    print(f"Aggiunta la voce {voce['id']} a {percorso_voci}")
    print('Punteggio: ' + pallini(livelli(voce, catalogo)))
    print(controllo.stdout.strip().splitlines()[-1])
    for x in controllo.stdout.splitlines():
        if x.startswith('AVVISO') and f"{voce['id']}" in x:
            print(x)
    return 0


def salva_da_url(sigla, url):
    codice, finale, corpo = Rete().apri(url)
    if codice != 200:
        print(f'Pagina non salvata: {esito(codice)}')
        return 1
    print('Salvata' if salva_pagina(sigla, finale, corpo) else 'Già presente')
    return 0


def aggiungi_scheda(vid):
    percorso = os.path.join(SCHEDE, vid + '.json')
    if not SLUG.match(vid) or not os.path.exists(percorso):
        print(f'ERRORE: nessuna scheda con id {vid!r} in {SCHEDE}')
        return 1
    return aggiungi(percorso, os.path.join(RADICE, 'data', 'voci.json'))


def main():
    argomenti = [a for a in sys.argv[1:] if not a.startswith('--')]
    opzioni = [a for a in sys.argv[1:] if a.startswith('--')]
    if not argomenti:
        print(__doc__)
        return 2
    # con due argomenti e una lingua è sempre una ricerca, anche per un termine come "prova"
    if len(argomenti) == 2 and argomenti[1] in LINGUE:
        comando, resto = 'cerca', argomenti
    else:
        comando, resto = argomenti[0], argomenti[1:]
    contesti_validi = comando == 'cerca' and all(re.fullmatch(r'--contesti=\d+', a) for a in opzioni) and len(opzioni) <= 1
    if opzioni and not contesti_validi:
        print(__doc__)
        return 2

    catalogo = carica_catalogo()
    if comando == 'prova' and not resto:
        righe = carica_righe()
        print(f'{len(righe)} righe di glossario da {len({r[0] for r in righe})} opere\n')
        prova(Indice(righe, catalogo), carica_voci())
        return 0
    if comando == 'aggiungi' and len(resto) == 1:
        return aggiungi_scheda(resto[0])
    if comando == 'pagina' and len(resto) == 2 and resto[0] in catalogo and resto[1].startswith('https://'):
        return salva_da_url(resto[0], resto[1])
    if comando not in ('cerca', 'scarica', 'crea') or len(resto) != 2 or resto[1] not in LINGUE:
        print(__doc__)
        return 2

    termine, lingua = resto
    if not chiave(termine):
        print(f'ERRORE: il termine {termine!r} non contiene lettere o cifre')
        return 2
    indice, voci = Indice(carica_righe(), catalogo), carica_voci()
    if comando == 'scarica':
        scarica_candidati(termine, lingua, indice)
        return 0
    if comando == 'crea':
        return scrivi_scheda(termine, lingua, indice, voci)
    stampa(termine, lingua, indice, voci, int(opzioni[0].split('=')[1]) if opzioni else 2)
    return 0


if __name__ == '__main__':
    sys.exit(main())
