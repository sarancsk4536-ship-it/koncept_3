"""Check the generated hierarchy against the Markdown and local resources."""
import collections, json, re
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'dist/catalog.json').read_text(encoding='utf-8'))
source=json.loads((ROOT/'scripts/sheet-source.json').read_text(encoding='utf-8'))
audit=json.loads((ROOT/'scripts/placement-audit.json').read_text(encoding='utf-8'))
nodes={n['id']:n for n in data['nodes']}
assert len(nodes)==len(data['nodes']), 'Duplicate IDs'
cells={}
for n in nodes.values():
    assert n['level'] in range(2,7)
    for cell in n['cells']:
        assert cell not in cells, f'Duplicate provenance: {cell}'
        cells[cell]=n
    if n.get('url'): assert n['url'].startswith('https://www.dns-shop.ru/')
    if n.get('image'): assert (ROOT/'dist'/n['image']).is_file(), n['image']
    assert len(n['children'])==len(set(n['children']))
    for child in n['children']:
        assert nodes[child]['parent']==n['id']
        assert nodes[child]['level']==n['level']+1
visited=set()
def walk(ident):
    assert ident not in visited, f'Cycle or duplicate parent: {ident}'
    visited.add(ident)
    n=nodes[ident]
    count=sum(walk(c) for c in n['children']) if n['children'] else 1
    assert count==n['leafCount'], ident
    return count
for ident in data['roots']:
    assert nodes[ident]['parent'] is None
    walk(ident)
assert visited==set(nodes), 'Unreachable nodes'
assert [nodes[x]['name'] for x in data['roots']]==['Инструменты','Оснастка и расходные материалы','Подбор по этапам работ','Аккумуляторные платформы']
# Independent full-path comparison from all six original Markdown columns.
expected=[]; expected_cells=[]; active=['']*6; md_rows=[]; md_lines=[]
for line_number,line in enumerate((ROOT/'scripts/catalog-source.md').read_text(encoding='utf-8-sig').splitlines(),1):
    if not line.strip(): continue
    row=[c.strip().replace('*','').strip() for c in line.strip().split('|')[1:-1]]
    assert len(row)==6
    if all(re.fullmatch(r':?-+:?',c.replace(' ','')) for c in row): continue
    md_rows.append([{'text':c,'url':''} for c in row[1:]])
    md_lines.append(line_number)
    if row==[f'{i} уровень' for i in range(1,7)]: continue
    for level,name in enumerate(row):
        if not name: continue
        active[level]=name
        active[level+1:]=['']*(5-level)
        if level:
            assert all(active[:level+1]), f'Missing parent at line {line_number}'
            expected.append(tuple(active[1:level+1]))
            expected_cells.append(f'строка {line_number} · уровень {level+1}')
assert md_rows==source['rows'], 'Source JSON differs from Markdown'
assert md_lines==source['lineNumbers']
actual=[]
for cell in expected_cells:
    n=cells[cell]; path=[]
    while n:
        path.insert(0,n['name'])
        n=nodes[n['parent']] if n['parent'] else None
    actual.append(tuple(path))
assert actual==expected, 'Source order, names or hierarchy mismatch'
assert set(cells)==set(expected_cells)
assert [x['cell'] for x in audit]==expected_cells
for item in audit:
    n=cells[item['cell']]
    assert all(item[k]==n[k] for k in ['id','name','level','parent'])
assert data['stats']=={'nodes':len(nodes),'leaves':sum(not n['children'] for n in nodes.values()),'placements':len(expected),'maxLevel':max(n['level'] for n in nodes.values())}
html=(ROOT/'dist/index.html').read_text(encoding='utf-8')
for local in re.findall(r'(?:src|href)="([^"#]+)"',html):
    if not local.startswith('http'): assert (ROOT/'dist'/urlsplit(local).path).is_file(),local
stage=next(n for n in nodes.values() if n['name']=='Подбор по этапам работ')
print(json.dumps({'status':'PASS','source_cells_checked':len(expected),'nodes':len(nodes),
    'leaves':data['stats']['leaves'],'stages':len(stage['children']),
    'levels':dict(collections.Counter(n['level'] for n in nodes.values())),
    'linked_nodes':sum(bool(n.get('url')) for n in nodes.values())},ensure_ascii=False))
