"""Build navigation preserving the source names, order and hierarchy."""
import argparse, hashlib, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--from-markdown', type=Path)
args = parser.parse_args()
source_path = ROOT/'scripts/sheet-source.json'
if args.from_markdown:
    rows, line_numbers, title = [], [], None
    for line_number, line in enumerate(args.from_markdown.read_text(encoding='utf-8-sig').splitlines(), 1):
        if not line.strip(): continue
        if not line.strip().startswith('|'): raise ValueError(f'Expected table at line {line_number}')
        cells = [re.sub(r'\*+', '', c.strip()).strip() for c in line.strip().split('|')[1:-1]]
        if len(cells) != 6: raise ValueError(f'Expected 6 columns at line {line_number}')
        if all(re.fullmatch(r':?-+:?', c.replace(' ', '')) for c in cells): continue
        if not rows:
            if cells != [f'{i} уровень' for i in range(1, 7)]: raise ValueError('Unexpected level headings')
        elif cells[0]:
            if title and cells[0] != title: raise ValueError('Multiple top-level catalogues')
            title = cells[0]
        rows.append([{'text': text, 'url': ''} for text in cells[1:]])
        line_numbers.append(line_number)
    if not title or len(rows) < 2: raise ValueError('Empty source table')
    source = {'sheet': 'Структура каталога', 'format': 'markdown-table', 'snapshot': '02.11.2026',
              'title': title, 'file': 'catalog-source.md', 'lineNumbers': line_numbers, 'rows': rows}
    source_path.write_text(json.dumps(source, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
else:
    source = json.loads(source_path.read_text(encoding='utf-8'))
def norm(s):
    s = re.sub(r'\s*\([^)]*(вирт|категорий)[^)]*\)', '', s, flags=re.I)
    return re.sub(r'[^a-zа-я0-9]', '', s.lower().replace('ё', 'е'))
links = json.loads((ROOT/'scripts/reference-links.json').read_text(encoding='utf-8'))
nodes, bypath, roots, active, placements = [], {}, [], [None]*5, []
for row_index, row in enumerate(source['rows'][1:], 1):
    filled = [(i,c['text'].strip()) for i,c in enumerate(row) if c and c['text'].strip()]
    if not filled: continue
    first = filled[0][0]
    active[first:] = [None]*(5-first)
    for index, name in filled:
        parent = next((active[i] for i in range(index-1,-1,-1) if active[i]), None)
        if index and (parent is None or parent['level'] != index+1):
            raise ValueError(f'Missing parent: source row {row_index+1}, {name}')
        parent_id = parent['id'] if parent else None
        key = (parent_id,index,name)
        cell = (f"строка {source['lineNumbers'][row_index]} · уровень {index+2}"
                if source.get('format') == 'markdown-table' else f'{chr(67+index)}{row_index+1}')
        if key not in bypath:
            ident = 'n'+hashlib.sha1(f'{parent_id}|{index}|{name}'.encode()).hexdigest()[:12]
            node = {'id':ident,'name':name,'level':index+2,'parent':parent_id,'children':[],
                    'cells':[],'virtual':bool(re.search(r'\(вирт\)',name,re.I))}
            bypath[key] = node
            nodes.append(node)
            (parent['children'] if parent else roots).append(ident)
        node = bypath[key]
        node['cells'].append(cell)
        active[index] = node
        placements.append({'cell':cell,'id':node['id'],'name':name,'level':index+2,'parent':parent_id})
        if norm(name) in links: node['url'] = links[norm(name)]
byid = {n['id']:n for n in nodes}
def leaves(n): return sum(leaves(byid[x]) for x in n['children']) if n['children'] else 1
# Bind pictures to names, not stage positions. All paths exist in the repository.
images = {
    'Инструменты':'stages/workshop-and-maintenance',
    'Оснастка и расходные материалы':'stages/tool-preparation',
    'Подбор по этапам работ':'stages/selection-by-work-stages',
    'Аккумуляторные платформы':'platform-brands/finepower',
    'Подготовка и оснащение рабочего места':'stages/worksite-organization',
    'Земляные работы и фундамент':'stages/preparation-safety-and-layout',
    'Демонтажные работы':'stages/demolition-and-clearing',
    'Возведение стен, перегородок, забора':'stages/walls-and-partitions',
    'Кровельные работы':'stages/wooden-structures',
    'Установка окон и входной двери':'stages/installation-of-structures-and-equipment',
    'Монтаж инженерных систем':'stages/engineering-utilities',
    'Черновая отделка':'stages/rough-construction-work',
    'Работа с плиткой':'stages/tile-stone-and-glass',
    'Предчистовая подготовка':'stages/surface-preparation',
    'Чистовая отделка':'stages/finish-work',
    'Уборка во время и после ремонта':'stages/cleaning-inspection-and-handover',
    'Обустройство помещений':'stages/assembly-and-fastening',
}
brands = {'FinePower':'finepower','Makita':'makita','Bosch':'bosch','DeWalt':'dewalt',
          'Metabo':'metabo','GreenWorks':'greenworks','Зубр':'zubr','Интерскол':'interskol',
          'AEG':'aeg','Karcher':'karcher','Sturm!':'sturm','Daewoo':'daewoo','DEKO':'deko','SENIX':'senix'}
images.update({'Платформы '+brand:'platform-brands/'+image for brand,image in brands.items()})
for node in nodes:
    if node['name'] in images: node['image'] = 'assets/generated/'+images[node['name']]+'.webp'
    node['leafCount'] = leaves(node)
data = {'title':source.get('title','Ремонт и строительство'),
        'source':{'label':source['sheet'],'file':source.get('file'),'snapshot':source.get('snapshot',source.get('fetchedAt'))},
        'roots':roots,'nodes':nodes,
        'stats':{'nodes':len(nodes),'leaves':sum(not n['children'] for n in nodes),
                 'placements':len(placements),'maxLevel':max(n['level'] for n in nodes)}}
(ROOT/'dist/catalog.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
(ROOT/'scripts/placement-audit.json').write_text(json.dumps(placements,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
print(json.dumps(data['stats']))
