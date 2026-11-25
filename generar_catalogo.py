#!/usr/bin/env python3
"""Genera catalogo.json desde un IFC de SteelX.
Uso: python generar_catalogo.py modelo.ifc [catalogo.json]
Peso del ensamble = suma de WeightNet_kg de sus subpiezas. Pernos (sin ensamble) se ignoran.
Ensambles con marca "-xxxx" van a 'ocultos' (se apagan en el visor)."""
import re, sys, json
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else 'catalogo.json'
ent = {}
for line in open(src, encoding='latin-1'):
    m = re.match(r'#(\d+)=(\w+)\((.*)\);\s*$', line)
    if m: ent[int(m.group(1))] = (m.group(2), m.group(3))
refs = lambda s: [int(x) for x in re.findall(r'#(\d+)', s)]
tail = lambda a: refs(a[a.index(',#5,') + 4:])
kids, psets = {}, {}
for t, a in ent.values():
    if t == 'IFCRELAGGREGATES':
        r = tail(a); kids[r[0]] = r[1:]
    elif t == 'IFCRELDEFINESBYPROPERTIES':
        r = tail(a)
        for o in r[:-1]: psets.setdefault(o, []).append(r[-1])
def props(el):
    d = {}
    for ps in psets.get(el, []):
        for p in tail(ent[ps][1]):
            if p in ent and ent[p][0] == 'IFCPROPERTYSINGLEVALUE':
                m = re.match(r"'([^']*)',\$,\w+\((.*)\),\$", ent[p][1])
                if m: d[m.group(1)] = m.group(2).strip("'")
    return d
guid = lambda i: ent[i][1].split(',')[0].strip("'")
cat, ocultos = {}, []
for a, (t, args) in ent.items():
    if t != 'IFCELEMENTASSEMBLY': continue
    marca = args.split(',')[2].strip("'")
    hijos = kids.get(a, [])
    if marca.startswith('-'):
        ocultos += [guid(a)] + [guid(c) for c in hijos]; continue
    peso, tipo = 0.0, ''
    for c in hijos:
        d = props(c)
        peso += float(d.get('WeightNet_kg', 0) or 0)
        if d.get('IsMainPart') == '.T.': tipo = d.get('ModelRole', '')
    cat[guid(a)] = {'m': marca, 'w': round(peso, 1), 't': tipo, 'p': [guid(c) for c in hijos]}
json.dump({'modelo': src.split('/')[-1], 'ensambles': cat, 'ocultos': ocultos}, open(out, 'w'), separators=(',', ':'))
print(f'{len(cat)} ensambles, {sum(e["w"] for e in cat.values())/1000:.1f} t, {len(ocultos)} guids ocultos -> {out}')
