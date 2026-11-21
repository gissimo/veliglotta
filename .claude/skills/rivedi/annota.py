#!/usr/bin/env python3
"""Legge una scheda per la revisione e la completa con il risultato.
Uso: python3 .claude/skills/rivedi/annota.py mostra ID
     python3 .claude/skills/rivedi/annota.py applica ID REVISIONE.json

applica mette ok a true sulle citazioni confermate, sposta quelle scartate in "scartate",
lascia da decidere quelle dubbie e completa voce, categoria, definizione e nota. Non aggiunge
termini che non sono già nella scheda e non scrive in voci.json. Quello che l'utente ha già
compilato resta com'è: citazioni con ok true, categoria, definizione e nota.
"""
import json
import os
import sys
from collections import Counter
from datetime import date

sys.dont_write_bytecode = True
RADICE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(RADICE, 'scripts'))
import prepara  # noqa: E402
from prepara import CATEGORIE, LINGUE, LINGUE_CON_GENERE, SLUG, carica_catalogo, chiave, cita, piega  # noqa: E402

ESITI = {'conferma', 'dubbio', 'scarta'}
CAMPI = {'citazioni', 'voce', 'categoria', 'definizione', 'nota', 'segnalazioni'}


def carica(vid):
    """Restituisce (percorso, scheda), oppure esce con un errore."""
    percorso = os.path.join(prepara.SCHEDE, vid + '.json')
    if not SLUG.match(vid) or not os.path.exists(percorso):
        raise SystemExit(f'ERRORE: nessuna scheda con id {vid!r}. Si crea con: python3 scripts/prepara.py crea TERMINE LINGUA')
    with open(percorso, encoding='utf-8') as f:
        scheda = json.load(f)
    if 'revisione' in scheda:
        raise SystemExit('ERRORE: la scheda è già stata rivista. Per rifarlo va tolto il campo "revisione".')
    if not scheda.get('citazioni'):
        raise SystemExit('ERRORE: la scheda non ha citazioni da rivedere.')
    return percorso, scheda


def materiale(scheda):
    voce = scheda.get('voce') or {}
    return {
        'voce': {l: [{'t': x.get('t'), 'g': x.get('g', '')} for x in voce.get(l) or []] for l in LINGUE},
        'categoria': voce.get('categoria', ''),
        'definizione': voce.get('definizione', ''),
        'nota': voce.get('nota', ''),
        'alternative': {l: [x.get('t') for x in lista] for l, lista in (scheda.get('alternative') or {}).items()},
        'termini_gia_in_altre_voci': scheda.get('gia_presenti') or {},
        'citazioni': [{'n': n, 'sigla': c.get('sigla'), 'termini': c.get('termini'), 'url': c.get('url', ''),
                       'ok': c.get('ok') is True, 'avviso': c.get('avviso', ''), 'brani': c.get('brani') or []}
                      for n, c in enumerate(scheda['citazioni'], 1)],
    }


def testo(x):
    return isinstance(x, str) and bool(x.strip())


def termini_ammessi(scheda, lingua):
    """{chiave: grafia} dei termini della voce e delle alternative per quella lingua."""
    m = materiale(scheda)
    forme = [x['t'] for x in m['voce'].get(lingua, [])] + m['alternative'].get(lingua, [])
    return {chiave(t): t for t in reversed(forme) if t}


def controlla_citazioni(r, scheda):
    errori = []
    citazioni = r['citazioni'] if isinstance(r['citazioni'], list) else []
    numeri = [c.get('n') for c in citazioni if isinstance(c, dict)]
    attesi = list(range(1, len(scheda['citazioni']) + 1))
    if len(numeri) != len(citazioni) or not all(isinstance(n, int) for n in numeri) or sorted(numeri) != attesi:
        errori.append(f'servono le citazioni da 1 a {len(attesi)}, una volta ciascuna')
    for c in citazioni:
        if not isinstance(c, dict) or set(c) != {'n', 'sigla', 'esito', 'motivo'}:
            errori.append(f'citazione malformata: {c!r}')
            continue
        if isinstance(c['n'], int) and 1 <= c['n'] <= len(attesi):
            originale = scheda['citazioni'][c['n'] - 1]
            if c['sigla'] != originale.get('sigla'):
                errori.append(f"citazione {c['n']}: la sigla {c['sigla']!r} non corrisponde alla scheda")
            if c['esito'] == 'scarta' and originale.get('ok') is True:
                errori.append(f"citazione {c['n']}: già confermata dall'utente, non si può scartare")
        if c['esito'] not in ESITI:
            errori.append(f"citazione {c['n']}: esito non valido {c['esito']!r}")
        if not testo(c['motivo']):
            errori.append(f"citazione {c['n']}: motivo mancante")
    return errori


def controlla_voce(r, scheda):
    errori = []
    voce = r['voce']
    if not isinstance(voce, dict) or set(voce) != set(LINGUE):
        return [f"voce deve avere le lingue {', '.join(LINGUE)}"]
    catalogo = carica_catalogo()
    esiti = {c['n']: c['esito'] for c in r['citazioni'] if isinstance(c, dict) and 'n' in c and 'esito' in c}
    valide = [c for n, c in enumerate(scheda['citazioni'], 1) if esiti.get(n) != 'scarta']
    for l in LINGUE:
        if not isinstance(voce[l], list):
            errori.append(f'lingua {l}: serve una lista di termini')
            continue
        ammessi = termini_ammessi(scheda, l)
        viste = set()
        for x in voce[l]:
            if not isinstance(x, dict) or not set(x) <= {'t', 'g'} or not isinstance(x.get('t'), str):
                errori.append(f'lingua {l}: termine malformato {x!r}')
                continue
            k = chiave(x['t'])
            if k not in ammessi:
                errori.append(f"lingua {l}: {x['t']!r} non è nella scheda")
                continue
            if k in viste:
                errori.append(f"lingua {l}: {x['t']!r} ripetuto")
            viste.add(k)
            g = x.get('g')
            if l in LINGUE_CON_GENERE and g not in ('m', 'f', 'loc', 'v'):
                errori.append(f"lingua {l}: genere mancante o non valido per {x['t']!r}")
            if l not in LINGUE_CON_GENERE and g not in (None, 'v'):
                errori.append(f"lingua {l}: il genere non va indicato, solo v per i verbi ({x['t']!r})")
            t = piega(ammessi[k])
            if not any(l in catalogo.get(c.get('sigla'), {}) and cita(c, t) for c in valide):
                errori.append(f"lingua {l}: {x['t']!r} non ha una citazione rimasta valida")
    return errori


def controlla(r, scheda):
    if not isinstance(r, dict) or set(r) != CAMPI:
        return [f'il file deve avere esattamente i campi: {", ".join(sorted(CAMPI))}']
    errori = controlla_citazioni(r, scheda) + controlla_voce(r, scheda)
    if not isinstance(r['segnalazioni'], list) or not all(testo(x) for x in r['segnalazioni']):
        errori.append('segnalazioni deve essere una lista di frasi')
    if r['categoria'] not in CATEGORIE:
        errori.append(f"categoria non valida: {r['categoria']!r}")
    if not testo(r['definizione']):
        errori.append('definizione mancante')
    if not isinstance(r['nota'], str):
        errori.append('nota deve essere una stringa, anche vuota')
    return errori


def applica(vid, file_revisione):
    percorso, scheda = carica(vid)
    try:
        with open(file_revisione, encoding='utf-8') as f:
            r = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise SystemExit(f'ERRORE: impossibile leggere {file_revisione}: {e}')
    errori = controlla(r, scheda)
    if errori:
        print('Revisione non valida, scheda non modificata:')
        for e in errori:
            print('  ' + e)
        return 1

    pareri = {c['n']: c for c in r['citazioni']}
    tenute, scartate = [], []
    for n, c in enumerate(scheda['citazioni'], 1):
        c['parere'] = {'esito': pareri[n]['esito'], 'motivo': pareri[n]['motivo'].strip()}
        if pareri[n]['esito'] == 'scarta':
            c['ok'] = False
            scartate.append(c)
            continue
        if pareri[n]['esito'] == 'conferma':
            c['ok'] = True
        tenute.append(c)
    scheda['citazioni'] = tenute
    scheda['scartate'] = scartate

    voce = scheda['voce']
    for l in LINGUE:
        ammessi = termini_ammessi(dict(scheda, citazioni=tenute + scartate), l)
        voce[l] = [dict({'t': ammessi[chiave(x['t'])]}, **({'g': x['g']} if x.get('g') else {})) for x in r['voce'][l]]
    tenuti = []
    for campo, valore in (('categoria', r['categoria']), ('definizione', r['definizione']), ('nota', r['nota'])):
        if testo(voce.get(campo)):
            tenuti.append(campo)
        else:
            voce[campo] = valore.strip()
    scheda['revisione'] = {'segnalazioni': r['segnalazioni'], 'data': date.today().isoformat()}

    temporaneo = percorso + '.tmp'
    with open(temporaneo, 'w', encoding='utf-8') as f:
        json.dump(scheda, f, ensure_ascii=False, indent=2)
        f.write('\n')
    os.replace(temporaneo, percorso)

    esiti = Counter(c['esito'] for c in r['citazioni'])
    print(f'Scheda completata: {percorso}')
    print(f"{esiti['conferma']} confermate, {esiti['dubbio']} dubbie, {esiti['scarta']} scartate")
    if tenuti:
        print('Già compilati e non modificati: ' + ', '.join(tenuti))
    errori = prepara.controlla_scheda(scheda, prepara.carica_voci(), carica_catalogo())
    if errori:
        print('Prima di aggiungi resta da risolvere:')
        for e in errori:
            print('  ' + e)
    else:
        print(f'Pronta per: python3 scripts/prepara.py aggiungi {vid}')
    return 0


def main():
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == 'mostra':
        print(json.dumps(materiale(carica(a[1])[1]), ensure_ascii=False, indent=2))
        return 0
    if len(a) == 3 and a[0] == 'applica':
        return applica(a[1], a[2])
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
