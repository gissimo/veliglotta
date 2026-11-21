#!/usr/bin/env python3
"""Trova le citazioni ridondanti in data/voci.json e, a richiesta, rimuove quelle sicure.
Uso: python3 scripts/sfoltisci.py [--rimuovi] [--dettagli] [voci.json] [fonti.json]

Senza opzioni non modifica nulla e stampa quattro gruppi:

1. Doppie: stessa voce, stessa opera, stesso url (o nessuno dei due), termini già tutti
   in un'altra citazione. Sono le uniche che --rimuovi toglie.
2. Doppie su documenti diversi: come sopra, ma con url diversi o in un'opera che riunisce
   più documenti senza url (RL). Si segnalano soltanto.
3. Possibili copie: due opere che FONTI.md indica come non del tutto indipendenti citano
   gli stessi termini nella stessa voce. Si segnalano soltanto.
4. Citazioni che non contano: il punteggio le ignora, per esempio perché citano un plurale
   o un termine tolto dalla voce. Non sono doppioni, quindi si segnalano soltanto.

In coda elenca le opere che, ciascuna presa da sola, si potrebbero togliere dal catalogo
senza cambiare né i livelli né il peso migliore di alcun termine, e dice se vale anche
togliendole tutte insieme. Un'opera con una copia nota si valuta togliendo anche la copia.
Anche questa è solo un'indicazione.

Con --dettagli stampa ogni caso dei gruppi 2, 3 e 4 invece del solo conteggio per opera.
"""
import json
import os
import re
import sys
from collections import Counter

sys.dont_write_bytecode = True
from valida import LINGUE, livelli, piega  # noqa: E402

DATI = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# Coppie non indipendenti secondo FONTI.md. La prima è quella da togliere, se si decide di farlo.
COPIE = (
    ('RL', 'RFEV-DIC'),  # una delle referenze locali è una versione successiva di RFEV-DIC
    ('PER', 'RD875'),  # PER non conta accanto a RD875 quando cita solo il programma d'esame
)
# Opere con più documenti citati senza url: due citazioni possono venire da documenti diversi.
PIU_DOCUMENTI = {'RL'}
RIGA_CITAZIONE = re.compile(r'^\s*\{ "sigla":')


def cita(citazione, termine):
    """Stesso confronto di valida.livelli: termine già piegato, a parola intera."""
    testo = piega(citazione.get('termini') or '')
    return re.search(r'(?<![a-z])' + re.escape(termine) + r'(?![a-z])', testo) is not None


def insieme(citazione):
    return frozenset(x.strip() for x in piega(citazione.get('termini') or '').split(',') if x.strip())


def copertura(voce, fonti, catalogo):
    """Peso migliore di ogni termine di ogni lingua, con le citazioni date."""
    ris = {}
    for l in LINGUE:
        for x in voce.get(l) or []:
            t = piega(x['t'])
            pesi = [catalogo[f['sigla']][l] for f in fonti if l in catalogo.get(f['sigla'], {}) and cita(f, t)]
            ris[(l, t)] = min(pesi) if pesi else None
    return ris


def invariata(voce, fonti, catalogo):
    """Vero se con queste citazioni livelli e copertura restano quelli della voce."""
    ridotta = dict(voce, fonti=fonti)
    return (livelli(ridotta, catalogo) == livelli(voce, catalogo)
            and copertura(voce, fonti, catalogo) == copertura(voce, voce['fonti'], catalogo))


def trova_doppie(voce, catalogo):
    """Restituisce (da togliere, su pagine diverse), come liste di indici nella voce."""
    fonti = voce['fonti']
    togliere, pagine = [], []
    for i, f in enumerate(fonti):
        a = insieme(f)
        contenitori = [j for j, g in enumerate(fonti) if j != i and g['sigla'] == f['sigla']
                       and j not in togliere and (a < insieme(g) or (a == insieme(g) and j < i))]
        if not contenitori:
            continue
        if f['sigla'] not in PIU_DOCUMENTI and any(fonti[j].get('url') == f.get('url') for j in contenitori):
            resto = [g for k, g in enumerate(fonti) if k != i and k not in togliere]
            if invariata(voce, resto, catalogo):
                togliere.append(i)
                continue
        pagine.append(i)
    return togliere, pagine


def motivo_non_conta(voce, f, catalogo):
    """None se la citazione conta per almeno una lingua, altrimenti il motivo."""
    pesi = catalogo.get(f['sigla'], {})
    trovate = [l for l in LINGUE if any(cita(f, piega(x['t'])) for x in voce.get(l) or [])]
    if any(l in pesi for l in trovate):
        return None
    if trovate:
        return f"l'opera non ha peso per {', '.join(trovate)}"
    return 'forma diversa dai termini della voce'


def opere_superflue(voci, catalogo):
    """Un'opera di cui esiste una copia si valuta togliendo anche la copia: altrimenti
    risulterebbe superflua solo perché la copia ne ripete i termini."""
    ris = []
    for s in catalogo:
        via = {s} | {a for a, b in COPIE if b == s}
        if all(invariata(v, [f for f in v['fonti'] if f['sigla'] not in via], catalogo) for v in voci):
            ris.append(s)
    return ris


def rimuovi(percorso, testo, dati, togliere):
    """Toglie le righe delle citazioni senza riformattare il file, poi verifica il risultato."""
    righe = testo.split('\n')
    posizioni = [n for n, r in enumerate(righe) if RIGA_CITAZIONE.match(r)]
    citazioni = [(v['id'], i, f) for v in dati['voci'] for i, f in enumerate(v['fonti'])]
    if len(posizioni) != len(citazioni):
        raise SystemExit('ERRORE: non tutte le citazioni stanno su una riga propria, file non modificato')

    via = set()
    for n, (vid, i, f) in zip(posizioni, citazioni):
        if json.loads(righe[n].strip().rstrip(',')) != f:
            raise SystemExit(f'ERRORE: riga {n + 1} diversa dalla citazione attesa in {vid}, file non modificato')
        if i in togliere.get(vid, ()):
            via.add(n)

    nuove = [r for n, r in enumerate(righe) if n not in via]
    for n in range(len(nuove) - 1):
        if RIGA_CITAZIONE.match(nuove[n]) and nuove[n + 1].strip().startswith(']'):
            nuove[n] = nuove[n].rstrip(',')
    nuovo = '\n'.join(nuove)

    attesi = json.loads(testo)
    for v in attesi['voci']:
        v['fonti'] = [f for i, f in enumerate(v['fonti']) if i not in togliere.get(v['id'], ())]
    if json.loads(nuovo) != attesi:
        raise SystemExit('ERRORE: il risultato non coincide con quello atteso, file non modificato')
    with open(percorso, 'w', encoding='utf-8') as f:
        f.write(nuovo)
    return len(via)


def stampa_gruppo(titolo, casi, dettagli):
    """casi: lista di (voce, sigla, descrizione)."""
    print(f'\n{titolo}: {len(casi)}')
    if dettagli:
        for vid, sigla, testo in casi:
            print(f'  {vid:26} {sigla:12} {testo}')
    elif casi:
        conta = Counter(c[1] for c in casi)
        print('  ' + ', '.join(f'{s} {n}' for s, n in conta.most_common()))


def main(percorso, percorso_fonti, applica, dettagli):
    with open(percorso, encoding='utf-8') as f:
        testo = f.read()
    dati = json.loads(testo)
    with open(percorso_fonti, encoding='utf-8') as f:
        catalogo = {c['sigla']: c.get('pesi', {}) for c in json.load(f)['fonti']}
    voci = dati['voci']

    togliere, pagine, copie, non_contano = {}, [], [], []
    doppie = []
    for v in voci:
        fonti = v.get('fonti') or []
        v['fonti'] = fonti
        via, diverse = trova_doppie(v, catalogo)
        if via:
            togliere[v['id']] = set(via)
        doppie += [(v['id'], fonti[i]['sigla'], fonti[i]['termini']) for i in via]
        pagine += [(v['id'], fonti[i]['sigla'], f"{fonti[i]['termini']} ({fonti[i].get('url', 'senza url')})")
                   for i in diverse]
        for a, b in COPIE:
            for f in fonti:
                if f['sigla'] == a and any(g['sigla'] == b and insieme(g) == insieme(f) for g in fonti):
                    copie.append((v['id'], a, f"stessi termini di {b}: {f['termini']}"))
        for f in fonti:
            motivo = motivo_non_conta(v, f, catalogo)
            if motivo:
                non_contano.append((v['id'], f['sigla'], f"{f['termini']} ({motivo})"))

    print(f"{len(voci)} voci, {sum(len(v['fonti']) for v in voci)} citazioni, {len(catalogo)} opere")
    stampa_gruppo('1. Doppie, rimovibili', doppie, True)
    stampa_gruppo('2. Doppie su documenti diversi, da valutare', pagine, dettagli)
    stampa_gruppo('3. Possibili copie, da valutare', copie, dettagli)
    stampa_gruppo('4. Citazioni che non contano, da controllare', non_contano, dettagli)
    superflue = opere_superflue(voci, catalogo)
    print(f'\nOpere senza effetti sul punteggio, ciascuna presa da sola: {len(superflue)}')
    if superflue:
        print('  ' + ', '.join(superflue))
        insieme_ok = all(invariata(v, [f for f in v['fonti'] if f['sigla'] not in superflue], catalogo) for v in voci)
        print('  Togliendole tutte insieme il punteggio ' + ('non cambia' if insieme_ok else 'cambia'))

    if applica:
        n = rimuovi(percorso, testo, json.loads(testo), togliere) if togliere else 0
        print(f'\nRimosse {n} citazioni da {percorso}')
    elif doppie:
        print('\nPer togliere le doppie del gruppo 1: python3 scripts/sfoltisci.py --rimuovi')
    return 0


if __name__ == '__main__':
    argomenti = [a for a in sys.argv[1:] if not a.startswith('--')]
    sys.exit(main(argomenti[0] if len(argomenti) > 0 else os.path.join(DATI, 'voci.json'),
                  argomenti[1] if len(argomenti) > 1 else os.path.join(DATI, 'fonti.json'),
                  '--rimuovi' in sys.argv, '--dettagli' in sys.argv))
