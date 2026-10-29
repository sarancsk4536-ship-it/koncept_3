"""Build navigation from the exact C:G cells. Never add or rename categories."""
import json, re, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / 'scripts/sheet-source.json').read_text())

def norm(s):
    s = re.sub(r'\s*\([^)]*(вирт|категорий)[^)]*\)', '', s, flags=re.I)
    return re.sub(r'[^a-zа-я0-9]', '', s.lower().replace('ё', 'е'))

# URLs enrich existing names only; no reference categories enter the hierarchy.
links = json.loads((ROOT / 'scripts/reference-links.json').read_text())

nodes, bypath, roots, active, placements = [], {}, [], [None]*5, []
for rownum, row in enumerate(source['rows'][1:],2):
    filled = [(i,c['text'].strip()) for i,c in enumerate(row) if c and c['text'].strip()]
    if not filled: continue
    first=filled[0][0]
    for i in range(first,5): active[i]=None
    for index, name in filled:
        parent = next((active[i] for i in range(index-1,-1,-1) if active[i]),None)
        parent_id = parent['id'] if parent else None
        key=(parent_id,index,name)
        cell=f'{chr(67+index)}{rownum}'
        if key not in bypath:
            ident='n'+hashlib.sha1(f'{parent_id}|{index}|{name}'.encode()).hexdigest()[:12]
            node={'id':ident,'name':name,'level':index+2,'parent':parent_id,'children':[],
                  'cells':[], 'virtual':bool(re.search(r'\(вирт\)',name,re.I))}
            bypath[key]=node; nodes.append(node)
            (parent['children'] if parent else roots).append(ident)
        node=bypath[key]; node['cells'].append(cell);active[index]=node
        placements.append({'cell':cell,'id':node['id'],'name':name,'level':index+2,'parent':parent_id})
        if norm(name) in links: node['url']=links[norm(name)]

byid={n['id']:n for n in nodes}
def leaves(n): return sum(leaves(byid[x]) for x in n['children']) if n['children'] else 1
def assign_image(n, image):
    p='assets/generated/'+image+'.webp'
    if (ROOT/'dist'/p).is_file(): n['image']=p

root_images=['phase-01/entry-03-tool-types','stages/tool-preparation','stages/selection-by-work-stages','phase-01/entry-01-accumulator-platforms']
for rid,img in zip(roots,root_images): assign_image(byid[rid],img)
stages=byid[roots[2]]
stage_images=['preparation-safety-and-layout','demolition-and-clearing','walls-and-partitions','wooden-structures','engineering-utilities','rough-construction-work','surface-preparation','finish-work','assembly-and-fastening']
for rid,img in zip(stages['children'],stage_images): assign_image(byid[rid],'stages/'+img)
brand_images={'FinePower':'finepower','Makita':'makita','Bosch':'bosch','DeWalt':'dewalt','Metabo':'metabo','GreenWorks':'greenworks','Зубр':'zubr','Интерскол':'interskol','AEG':'aeg','Karcher':'karcher','Sturm!':'sturm','Daewoo':'daewoo','DEKO':'deko','SENIX':'senix'}
for rid in byid[roots[3]]['children']:
    n=byid[rid]
    for brand,img in brand_images.items():
        if n['name']=='Платформы '+brand:assign_image(n,'platform-brands/'+img)
for node in nodes:
    node['leafCount']=leaves(node)

data={'title':'Ремонт и строительство','source':{'sheet':'Лист1','columns':'C:G','snapshot':'28.10.2026'},'roots':roots,'nodes':nodes,
      'stats':{'nodes':len(nodes),'leaves':sum(not n['children'] for n in nodes),'placements':len(placements),'maxLevel':max(n['level'] for n in nodes)}}
(ROOT/'dist/catalog.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
(ROOT/'scripts/placement-audit.json').write_text(json.dumps(placements,ensure_ascii=False,separators=(',',':')))
print(json.dumps(data['stats']))
