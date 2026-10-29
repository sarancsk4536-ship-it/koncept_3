"""Check every source cell against the delivered hierarchy and local resources."""
import json, re, collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'dist/catalog.json').read_text())
source=json.loads((ROOT/'scripts/sheet-source.json').read_text())
nodes={n['id']:n for n in data['nodes']}
cells={}
for node in nodes.values():
    for cell in node['cells']:
        assert cell not in cells, f'Duplicate provenance: {cell}'
        cells[cell]=node
    assert node['level'] in range(2,7)
    if node.get('url'): assert node['url'].startswith('https://www.dns-shop.ru/')
    if node.get('image'): assert (ROOT/'dist'/node['image']).is_file()
    for child in node['children']:
        assert nodes[child]['parent']==node['id']
        assert nodes[child]['level']>node['level']
expected=0
active=[None]*5
for rownum,row in enumerate(source['rows'][1:],2):
    populated=[i for i,c in enumerate(row) if c and c['text'].strip()]
    if not populated: continue
    active[min(populated):]=[None]*(5-min(populated))
    for i in populated:
        cell=f'{chr(67+i)}{rownum}'; expected+=1
        n=cells[cell]
        assert n['name']==row[i]['text'].strip(), cell
        assert n['level']==i+2, cell
        parent=next((active[j] for j in range(i-1,-1,-1) if active[j]),None)
        assert n['parent']==parent, cell
        active[i]=n['id']
assert len(cells)==expected
visited=set()
def walk(ident):
    assert ident not in visited, f'Cycle or duplicate parent: {ident}'
    visited.add(ident)
    for child in nodes[ident]['children']: walk(child)
for ident in data['roots']:
    assert nodes[ident]['parent'] is None
    walk(ident)
assert len(visited)==len(nodes)
assert [nodes[x]['name'] for x in data['roots']]==['Инструменты','Оснастка и расходные материалы','Подбор по этапам работ','Аккумуляторные платформы']
html=(ROOT/'dist/index.html').read_text()
for local in re.findall(r'(?:src|href)="([^"#]+)"',html):
    if not local.startswith('http'):assert (ROOT/'dist'/local).is_file(),local
levels=dict(collections.Counter(n['level'] for n in nodes.values()))
print(json.dumps({'source_cells_checked':expected,'nodes':len(nodes),'leaves':sum(not n['children'] for n in nodes.values()),'levels':levels,'linked_nodes':sum(bool(n.get('url')) for n in nodes.values()),'status':'PASS'},ensure_ascii=False))
