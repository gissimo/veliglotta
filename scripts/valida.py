#!/usr/bin/env python3
"""Valida data/voci.json e data/fonti.json.
Uso: python3 scripts/valida.py [--punteggi] [voci.json] [fonti.json]

Con --punteggi stampa anche il punteggio di verifica di ogni voce.

Esce con codice 1 se trova errori, 0 altrimenti. Gli avvisi non fanno fallire.
L'elenco CATEGORIE va tenuto allineato con quello di app.js.
"""
import json
import re
import sys
import unicodedata
from urllib.parse import urljoin, urlparse
from collections import defaultdict

CATEGORIE = {"scafo", "coperta", "attrezzatura", "vele", "manovre", "navigazione", "meteo", "equipaggio"}
LINGUE = ("eng", "esp", "fra", "ita")
LINGUE_CON_GENERE = ("esp", "fra", "ita")
PESI = {"A", "B", "C"}
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

errori, avvisi = [], []
basi = {}  # sigla -> indirizzo a cui si appoggiano gli url relativi delle citazioni


def err(voce, msg):
    errori.append(f"[{voce}] {msg}")


def avv(voce, msg):
    avvisi.append(f"[{voce}] {msg}")


def leggi_catalogo(percorso):
    """Legge il catalogo delle fonti e restituisce, per ogni sigla, i pesi per lingua."""
    try:
        with open(percorso, encoding="utf-8") as f:
            dati = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        err("fonti", f"impossibile leggere {percorso}: {e}")
        return {}
    catalogo = {}
    for c in dati.get("fonti") or []:
        s = c.get("sigla") if isinstance(c, dict) else None
        if not isinstance(s, str) or not s.strip():
            err("fonti", f"voce del catalogo senza sigla: {c!r}")
            continue
        if s in catalogo:
            err("fonti", f"sigla duplicata: {s!r}")
        catalogo[s] = {}
        pesi = c.get("pesi")
        if not isinstance(pesi, dict) or not pesi:
            err("fonti", f"{s}: pesi mancanti")
        else:
            for l, p in pesi.items():
                if l not in LINGUE or p not in PESI:
                    err("fonti", f"{s}: peso non valido {l!r}: {p!r} (lingue {', '.join(LINGUE)}, pesi A, B o C)")
            catalogo[s] = pesi
        if not isinstance(c.get("titolo"), str) or not c["titolo"].strip():
            err("fonti", f"{s}: titolo mancante")
        urls = [c["url"]] if "url" in c else [l.get("url") for l in c.get("link", []) if isinstance(l, dict)]
        for u in urls:
            if not (isinstance(u, str) and re.match(r"^https?://", u)):
                err("fonti", f"{s}: url non valido: {u!r}")
        if urls and isinstance(urls[0], str):
            basi[s] = urls[0]
    return catalogo


def controlla_url(nome, sigla, url):
    """Un url di citazione è assoluto, oppure relativo all'indirizzo dell'opera nel catalogo
    (url, o primo dei link), e si risolve come un link relativo del web."""
    if not isinstance(url, str) or not url:
        err(nome, f"url non valido: {url!r}")
        return
    if re.match(r"^https?://", url):
        return
    base = basi.get(sigla)
    if not base:
        err(nome, f"url relativo {url!r}, ma {sigla} non ha un indirizzo nel catalogo")
        return
    # Un indirizzo che non finisce con / né con un file fa perdere l'ultima parte del percorso:
    # succede se si toglie la / finale nel catalogo, per esempio .../vocabolario invece di .../vocabolario/.
    ultimo = urlparse(base).path.rsplit("/", 1)[-1]
    if not (base.endswith("/") or "." in ultimo or url.startswith("?")):
        err(nome, f"url relativo {url!r}: l'indirizzo di {sigla} nel catalogo deve finire con / ({base})")
    elif not re.match(r"^https?://", urljoin(base, url)):
        err(nome, f"url non valido: {url!r}")


def piega(s):
    """Minuscolo, senza accenti, con trattini e apostrofi come spazi (come fold in app.js)."""
    s = unicodedata.normalize("NFD", s.replace("-", " ").replace("'", " ").replace("’", " "))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def livelli(voce, catalogo):
    """Livello da 0 a 3 per ogni lingua: 0 nessuna fonte, 1 solo fonti C,
    2 almeno una fonte B o una A senza secondo riscontro, 3 una A più una A o B.
    Una citazione conta per una lingua se la fonte la copre e tra i suoi termini c'è uno della lingua."""
    ris = {}
    for l in LINGUE:
        voci_l = [piega(t["t"]) for t in voce.get(l) or [] if isinstance(t, dict) and isinstance(t.get("t"), str)]
        migliori = {}
        for f in voce.get("fonti") or []:
            if not isinstance(f, dict):
                continue
            peso = catalogo.get(f.get("sigla"), {}).get(l)
            citati = piega(f.get("termini") or "")
            if peso and any(re.search(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", citati) for t in voci_l):
                migliori[f["sigla"]] = min(migliori.get(f["sigla"], "C"), peso)
        pesi = list(migliori.values())
        if "A" in pesi and sum(p in "AB" for p in pesi) >= 2:
            ris[l] = 3
        elif "A" in pesi or "B" in pesi:
            ris[l] = 2
        else:
            ris[l] = 1 if pesi else 0
    return ris


def stampa_punteggi(voci, catalogo):
    righe = []
    for v in voci:
        if not isinstance(v, dict):
            continue
        lv = livelli(v, catalogo)
        righe.append((round(100 * sum(lv.values()) / (3 * len(LINGUE))), v.get("id"), lv))
    righe.sort(key=lambda r: (r[0], str(r[1])))
    for perc, vid, lv in righe:
        pallini = "  ".join(f"{l} {'●' * n}{'○' * (3 - n)}" for l, n in lv.items())
        segno = "completa" if min(lv.values()) == 3 else ""
        print(f"{perc:3d}%  {vid:26} {pallini}  {segno}")
    print(f"media {round(sum(r[0] for r in righe) / max(len(righe), 1))}%")


def main(percorso, percorso_fonti, punteggi=False):
    try:
        with open(percorso, encoding="utf-8") as f:
            dati = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERRORE: impossibile leggere {percorso}: {e}")
        return 1

    if dati.get("schema") != 1:
        err("file", "schema deve valere 1")
    voci = dati.get("voci")
    if not isinstance(voci, list) or not voci:
        err("file", "voci deve essere una lista non vuota")
        voci = []

    catalogo = leggi_catalogo(percorso_fonti)
    usate = set()
    visti = set()
    termini = defaultdict(list)

    for i, v in enumerate(voci):
        vid = v.get("id") if isinstance(v, dict) else None
        nome = vid if isinstance(vid, str) and vid else f"voce #{i + 1}"
        if not isinstance(v, dict):
            err(nome, "la voce deve essere un oggetto")
            continue
        if not isinstance(vid, str) or not SLUG.match(vid):
            err(nome, "id mancante o non valido (minuscolo, cifre e trattini)")
        elif vid in visti:
            err(nome, "id duplicato")
        visti.add(vid)

        if v.get("categoria") not in CATEGORIE:
            err(nome, f"categoria non valida: {v.get('categoria')!r}")

        ordine = [k for k in v if k in LINGUE]
        if ordine != [l for l in LINGUE if l in v]:
            avv(nome, f"le lingue andrebbero in ordine alfabetico del codice: {', '.join(LINGUE)} (trovato: {', '.join(ordine)})")

        for l in LINGUE:
            lista = v.get(l)
            if not isinstance(lista, list) or not lista:
                err(nome, f"lingua {l}: serve almeno un termine")
                continue
            for t in lista:
                if not isinstance(t, dict) or not isinstance(t.get("t"), str) or not t["t"].strip():
                    err(nome, f"lingua {l}: termine vuoto o malformato")
                    continue
                if t["t"] != t["t"].strip():
                    err(nome, f"lingua {l}: spazi superflui in {t['t']!r}")
                g = t.get("g")
                if l in LINGUE_CON_GENERE and g not in ("m", "f", "loc", "v"):
                    err(nome, f"lingua {l}: genere mancante o non valido per {t['t']!r}")
                if l not in LINGUE_CON_GENERE and g not in (None, "v"):
                    err(nome, f"lingua {l}: il genere non va indicato, solo v per i verbi ({t['t']!r})")
                termini[(l, t["t"].strip().lower())].append(nome)

        if not isinstance(v.get("definizione"), str) or not v["definizione"].strip():
            err(nome, "definizione mancante")
        if "nota" in v and not isinstance(v["nota"], str):
            err(nome, "nota deve essere una stringa")

        fonti = v.get("fonti")
        if not isinstance(fonti, list):
            err(nome, "fonti deve essere una lista, anche vuota")
            fonti = []
        for f in fonti:
            if isinstance(f, dict):
                if not isinstance(f.get("termini"), str) or not f["termini"].strip():
                    err(nome, "fonte senza termini citati")
                sigla = f.get("sigla")
                if sigla not in catalogo:
                    err(nome, f"sigla mancante o assente da data/fonti.json: {sigla!r}")
                usate.add(sigla)
                if "url" in f:
                    controlla_url(nome, sigla, f["url"])
            else:
                err(nome, "fonte malformata: serve { sigla, termini, url }")

    for s in catalogo:
        if s not in usate:
            avv("fonti", f"la sigla {s!r} non è citata da nessuna voce")

    for (l, t), dove in termini.items():
        if len(set(dove)) > 1:
            avv("duplicati", f"il termine {t!r} ({l}) compare in più voci: {', '.join(sorted(set(dove)))}")

    if punteggi:
        stampa_punteggi(voci, catalogo)
        print()

    for a in avvisi:
        print("AVVISO", a)
    for e in errori:
        print("ERRORE", e)
    print(f"{len(voci)} voci, {len(errori)} errori, {len(avvisi)} avvisi")
    return 1 if errori else 0


if __name__ == "__main__":
    argomenti = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(main(argomenti[0] if len(argomenti) > 0 else "data/voci.json",
                  argomenti[1] if len(argomenti) > 1 else "data/fonti.json",
                  "--punteggi" in sys.argv))
