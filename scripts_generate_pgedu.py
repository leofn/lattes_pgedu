#!/usr/bin/env python3
import json,re,html
from pathlib import Path
from collections import Counter,defaultdict
BASE=Path('/home/hermes/lattes_pgedu'); OUT=Path('/home/hermes/scriptLattes/output/pgedu'); DOC=Path('/home/hermes/scriptLattes/pgedu_docentes.json')
PROC=BASE/'data/processed'; DOCS=BASE/'docs'; PROC.mkdir(parents=True,exist_ok=True); DOCS.mkdir(parents=True,exist_ok=True)
docentes=json.loads(DOC.read_text(encoding='utf-8'))
all_data=[]
for jf in sorted(OUT.glob('K*.json')):
    try: all_data.append((jf,json.loads(jf.read_text(encoding='utf-8'))))
    except Exception: pass
by_lid={str(d.get('lattes_id') or d.get('id_lattes') or ''):(jf,d) for jf,d in all_data}
by_name={re.sub(r'\W+','',str(d.get('nome','')).lower()):(jf,d) for jf,d in all_data}

def norm(s): return re.sub(r'\W+','',str(s).lower())
def clean(s,n=900):
    s=re.sub(r'\s+',' ',str(s or '')).strip()
    return s[:n]+('…' if len(s)>n else '')
def numbered_count(s):
    s=str(s or '')
    return len(re.findall(r'(?:^|\n|(?<=[.!?]))\s*\d+\s*[\.)]', s)) or len(re.findall(r'(?<!\d)\d+\.', s[:50000]))
def section_between(text,start_patterns,end_patterns):
    low=text.lower(); starts=[]
    for p in start_patterns:
        i=low.find(p.lower())
        if i>=0: starts.append(i)
    if not starts: return ''
    st=min(starts); en=len(text)
    for ep in end_patterns:
        j=low.find(ep.lower(),st+20)
        if j>=0: en=min(en,j)
    return text[st:en]
def count_section(data,keys,starts,ends):
    for k in keys:
        if data.get(k): return numbered_count(data.get(k))
    return numbered_count(section_between(data.get('_full_text') or data.get('full_text') or '',starts,ends))
def years_from_section(sec):
    c=Counter()
    for m in re.finditer(r'(?:^|\n|(?<=[.!?]))\s*\d+\s*[\.)](.*?)(?=(?:\n|(?<=[.!?]))\s*\d+\s*[\.)]|$)', sec, re.S):
        yrs=[int(y) for y in re.findall(r'(?<!\d)(19\d{2}|20\d{2})(?!\d)', m.group(1))]
        yrs=[y for y in yrs if 1950<=y<=2026]
        if yrs: c[max(yrs)]+=1
    if not c:
        for y in re.findall(r'(?<!\d)(19\d{2}|20\d{2})(?!\d)', sec):
            yi=int(y)
            if 1950<=yi<=2026: c[yi]+=1
    return c

temporal={'artigos':Counter(),'livros':Counter(),'capitulos':Counter()}; dataset=[]; missing=[]
for info in docentes:
    lid=str(info['lattes_id']); item=by_lid.get(lid)
    if not item: item=by_name.get(norm(info['nome']))
    if not item:
        missing.append(info['nome'])
        dataset.append({
          'nome':info['nome'],'nome_site':info['nome'],'email':info.get('email',''),'arquivo':'',
          'id_lattes':lid,'short_id':'','lattes_url':f'http://lattes.cnpq.br/{lid}',
          'ultima_atualizacao':'','resumo':'Currículo Lattes não localizado nos arquivos K*.json disponíveis no momento da consolidação.',
          'areas':'','formacao':'','pos_doutorado_texto':'','doutorado':False,'mestrado':False,'graduacao':False,'pos_doutorado':False,
          'num_artigos':0,'num_livros':0,'num_capitulos':0,'num_projetos':0,'num_orient_total':0,'num_bancas_total':0,
          'scholar_citacoes':0,'scholar_h_index':0,'scholar_url':'','full_text_len':0})
        continue
    jf,data=item; text=data.get('_full_text') or data.get('full_text') or ''
    prod=data.get('producoes') or section_between(text,['Produção bibliográfica','Produções'],['Bancas','Eventos','Orientações'])
    artsec=section_between(prod,['Artigos completos publicados em periódicos'],['Livros publicados/organizados','Capítulos de livros publicados','Textos em jornais','Trabalhos completos publicados'])
    livsec=section_between(prod,['Livros publicados/organizados ou editados','Livros publicados/organizados'],['Capítulos de livros publicados','Textos em jornais','Trabalhos completos publicados'])
    capsec=section_between(prod,['Capítulos de livros publicados'],['Textos em jornais','Trabalhos completos publicados','Resumos publicados','Apresentações de Trabalho'])
    nart=numbered_count(artsec); nliv=numbered_count(livsec); ncap=numbered_count(capsec)
    for k,sec in [('artigos',artsec),('livros',livsec),('capitulos',capsec)]: temporal[k].update(years_from_section(sec))
    form=data.get('formacao_academica') or section_between(text,['Formação acadêmica/titulação'],['Pós-doutorado','Formação Complementar','Atuação Profissional'])
    pos=data.get('pos_doutorado') or section_between(text,['Pós-doutorado'],['Formação Complementar','Atuação Profissional'])
    projetos=count_section(data,['projetos_pesquisa'],['Projetos de pesquisa'],['Projetos de extensão','Áreas de atuação','Produções'])
    orient=count_section(data,['orientacoes'],['Orientações e supervisões'],['Bancas','Eventos','Outras informações'])
    bancas=count_section(data,['bancas'],['Participação em bancas'],['Eventos','Orientações','Outras informações'])
    rec={
      'nome':data.get('nome') or info['nome'],'nome_site':info['nome'],'email':info.get('email',''),'arquivo':jf.name,
      'id_lattes':lid,'short_id':data.get('short_id') or jf.stem,'lattes_url':f'http://lattes.cnpq.br/{lid}',
      'ultima_atualizacao':data.get('ultima_atualizacao',''),'resumo':clean(data.get('resumo') or '',1000),
      'areas':clean(data.get('areas_atuacao') or '',900),'formacao':clean(form,1200),'pos_doutorado_texto':clean(pos,700),
      'doutorado':bool(re.search('doutorado',form,re.I)),'mestrado':bool(re.search('mestrado',form,re.I)),'graduacao':bool(re.search('gradua',form,re.I)),'pos_doutorado':bool(re.search(r'p[oó]s-dout|post.?doc',form+' '+pos,re.I)),
      'num_artigos':nart,'num_livros':nliv,'num_capitulos':ncap,'num_projetos':projetos,'num_orient_total':orient,'num_bancas_total':bancas,
      'scholar_citacoes':0,'scholar_h_index':0,'scholar_url':'','full_text_len':len(text)}
    dataset.append(rec)

dataset.sort(key=lambda x: x['nome_site'])
(PROC/'pgedu_dataset.json').write_text(json.dumps(dataset,ensure_ascii=False,indent=2),encoding='utf-8')
temp_out={k:{str(y):temporal[k][y] for y in sorted(temporal[k]) if 1990<=y<=2026} for k in temporal}
(PROC/'producao_temporal.json').write_text(json.dumps(temp_out,ensure_ascii=False,indent=2),encoding='utf-8')
print('docentes',len(dataset),'missing',missing,'projetos',sum(d['num_projetos'] for d in dataset),'orient',sum(d['num_orient_total'] for d in dataset))

stats={'docentes':len(dataset),'projetos':sum(d['num_projetos'] for d in dataset),'orientacoes':sum(d['num_orient_total'] for d in dataset),'citacoes':0,'artigos':sum(d['num_artigos'] for d in dataset),'livros':sum(d['num_livros'] for d in dataset),'capitulos':sum(d['num_capitulos'] for d in dataset)}
DATA=json.dumps(dataset,ensure_ascii=False); TEMP=json.dumps(temp_out,ensure_ascii=False); ST=json.dumps(stats,ensure_ascii=False)
html_doc=f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>PGEDU-UFBA · Corpo Docente Permanente — Análise de Currículos Lattes</title><meta name="description" content="Análise dos currículos Lattes dos docentes permanentes do PGEDU-UFBA"><script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script><style>
:root{{--primary:#1a237e;--primary-light:#283593;--bg:#f5f6fa;--card:#fff;--text:#263238;--muted:#6b7280;--border:#e5e7eb;--shadow:0 2px 16px rgba(26,35,126,.10);--hover:0 10px 32px rgba(26,35,126,.18);--r:16px}}*{{box-sizing:border-box}}body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}}header{{background:linear-gradient(135deg,#0d1446,var(--primary),var(--primary-light));color:#fff;text-align:center;padding:54px 20px 46px;position:relative;overflow:hidden}}header:before{{content:'';position:absolute;inset:-80px -120px auto auto;width:360px;height:360px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.12),transparent 70%)}}h1{{margin:0;font-size:clamp(2rem,5vw,3.3rem);letter-spacing:-1px}}.subtitle{{font-size:1.2rem;opacity:.9;margin-top:6px}}.stats-bar{{max-width:1120px;margin:-28px auto 0;display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:var(--border);border-radius:var(--r);overflow:hidden;box-shadow:var(--shadow);position:relative;z-index:2}}.stat{{background:#fff;text-align:center;padding:18px 10px;transition:.25s}}.stat:hover{{background:#eef2ff}}.num{{font-size:2rem;font-weight:800;color:var(--primary)}}.label{{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}}.container{{max-width:1220px;margin:auto;padding:38px 20px}}section{{margin-bottom:34px}}h2{{color:var(--primary);font-size:1.45rem;display:flex;gap:10px;align-items:center}}h2:before{{content:'';width:5px;height:25px;border-radius:4px;background:var(--primary)}}.charts,.rankings{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}}.panel,.card{{background:var(--card);border-radius:var(--r);box-shadow:var(--shadow);padding:22px;transition:.25s}}.panel:hover,.card:hover{{transform:translateY(-3px);box-shadow:var(--hover)}}.rank-item{{display:flex;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid var(--border)}}.rank-item:last-child{{border-bottom:0}}.pos{{background:var(--primary);color:#fff;width:30px;height:30px;border-radius:50%;display:grid;place-items:center;font-weight:700}}.grow{{flex:1}}.value{{font-weight:800;color:var(--primary)}}.controls{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}}input{{flex:1;min-width:260px;border:1px solid var(--border);border-radius:999px;padding:13px 18px;font-size:1rem}}button{{border:0;border-radius:999px;background:#fff;color:var(--primary);padding:12px 18px;font-weight:700;box-shadow:var(--shadow);cursor:pointer;transition:.2s}}button.active,button:hover{{background:var(--primary);color:#fff}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:20px}}.card h3{{margin:.2rem 0;color:var(--primary);font-size:1.22rem}}.links a{{color:var(--primary-light);font-weight:700;text-decoration:none;margin-right:12px}}.badges{{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}}.badge{{background:#e8eaf6;color:var(--primary);border-radius:999px;padding:4px 9px;font-size:.78rem;font-weight:700}}.mini{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:14px 0}}.mini div{{background:#f7f8ff;border-radius:10px;text-align:center;padding:8px}}.mini b{{display:block;color:var(--primary);font-size:1.25rem}}.prod{{font-size:.9rem;color:var(--muted);margin-bottom:10px}}.text{{font-size:.92rem;color:#374151}}.areas{{margin-top:10px;font-size:.85rem;color:var(--muted)}}footer{{background:#10173f;color:#fff;text-align:center;padding:34px 20px;margin-top:30px}}footer img{{max-width:170px;display:block;margin:0 auto 16px}}footer a{{color:#c7d2fe}}@media(max-width:760px){{.stats-bar{{grid-template-columns:repeat(2,1fr);margin-left:12px;margin-right:12px}}.grid{{grid-template-columns:1fr}}.mini{{grid-template-columns:repeat(2,1fr)}}}}
</style></head><body><header><h1>PGEDU · Educação — UFBA</h1><div class="subtitle">Corpo Docente Permanente — Análise de Currículos Lattes</div></header><div class="stats-bar"><div class="stat"><div class="num">{stats['docentes']}</div><div class="label">Docentes</div></div><div class="stat"><div class="num">{stats['projetos']}</div><div class="label">Projetos</div></div><div class="stat"><div class="num">{stats['orientacoes']}</div><div class="label">Orientações</div></div><div class="stat"><div class="num">{stats['citacoes']}</div><div class="label">Citações</div></div><div class="stat"><div class="num">05/07/2026</div><div class="label">Coleta</div></div></div><main class="container"><section><h2>Produção temporal</h2><div class="charts"><div class="panel"><h3>Artigos/ano</h3><canvas id="artigosChart"></canvas></div><div class="panel"><h3>Livros/ano</h3><canvas id="livrosChart"></canvas></div><div class="panel"><h3>Capítulos/ano</h3><canvas id="capitulosChart"></canvas></div></div></section><section><h2>Rankings Top 5</h2><div class="rankings" id="rankings"></div></section><section><h2>Docentes</h2><div class="controls"><input id="search" placeholder="Buscar por nome ou área de atuação..."><button data-sort="nome" class="active">Nome</button><button data-sort="num_projetos">Projetos</button><button data-sort="scholar_citacoes">Citações</button><button data-sort="num_orient_total">Orientações</button></div><div id="count"></div><div class="grid" id="cards"></div></section></main><footer><img src="https://labhdufba.github.io/images/labhd_hu_f740b91ea7236ce2.webp" alt="LABHD-UFBA"><p>Desenvolvido por Leonardo Fernandes Nascimento (LABHD-UFBA)</p><p>Data da coleta: 05/07/2026 · <a href="https://github.com/leofn/lattes_pgedu">github.com/leofn/lattes_pgedu</a></p></footer><script>
const docentes={DATA}; const temporal={TEMP}; const stats={ST}; let sortKey='nome';
function esc(s){{return String(s||'').replace(/[&<>"']/g,m=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[m]))}}
function chart(id,label,obj,color){{const years=Object.keys(obj).sort(); new Chart(document.getElementById(id),{{type:'bar',data:{{labels:years,datasets:[{{label,data:years.map(y=>obj[y]),backgroundColor:color,borderRadius:6}}]}},options:{{responsive:true,plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true,ticks:{{precision:0}}}}}}}})}}
chart('artigosChart','Artigos',temporal.artigos,'#1a237e'); chart('livrosChart','Livros',temporal.livros,'#283593'); chart('capitulosChart','Capítulos',temporal.capitulos,'#5c6bc0');
function rank(title,key){{let arr=[...docentes].sort((a,b)=>(b[key]||0)-(a[key]||0)).slice(0,5); return `<div class="panel"><h3>${{title}}</h3>${{arr.map((d,i)=>`<div class="rank-item"><span class="pos">${{i+1}}</span><span class="grow">${{esc(d.nome_site||d.nome)}}</span><span class="value">${{d[key]||0}}</span></div>`).join('')}}</div>`}}
document.getElementById('rankings').innerHTML=rank('Citações','scholar_citacoes')+rank('Projetos','num_projetos')+rank('Orientações','num_orient_total');
function render(){{let q=document.getElementById('search').value.toLowerCase(); let arr=docentes.filter(d=>`${{d.nome}} ${{d.nome_site}} ${{d.areas}} ${{d.resumo}}`.toLowerCase().includes(q)); arr.sort((a,b)=>sortKey==='nome'?String(a.nome_site).localeCompare(String(b.nome_site),'pt-BR'):(b[sortKey]||0)-(a[sortKey]||0)); document.getElementById('count').textContent=`${{arr.length}} docentes encontrados`; document.getElementById('cards').innerHTML=arr.map(d=>`<article class="card"><h3>${{esc(d.nome_site||d.nome)}}</h3><div class="links"><a href="${{d.lattes_url}}" target="_blank" rel="noopener">Lattes</a>${{d.email?`<a href="mailto:${{esc(d.email)}}">E-mail</a>`:''}}</div><div class="badges">${{d.doutorado?'<span class="badge">Doutorado</span>':''}}${{d.pos_doutorado?'<span class="badge">Pós-doc</span>':''}}${{d.mestrado?'<span class="badge">Mestrado</span>':''}}</div><div class="mini"><div><b>${{d.num_projetos}}</b>Projetos</div><div><b>${{d.num_orient_total}}</b>Orient.</div><div><b>${{d.num_bancas_total}}</b>Bancas</div><div><b>${{d.scholar_citacoes}}</b>Citações</div></div><div class="prod"><strong>Produção:</strong> ${{d.num_artigos}} artigos · ${{d.num_livros}} livros · ${{d.num_capitulos}} capítulos</div><p class="text">${{esc(d.resumo||'Resumo não disponível.')}}</p><div class="areas"><strong>Áreas:</strong> ${{esc(d.areas||'Não informadas')}}</div><div class="areas">Atualização Lattes: ${{esc(d.ultima_atualizacao||'N/I')}}</div></article>`).join('')}}
document.getElementById('search').addEventListener('input',render); document.querySelectorAll('button[data-sort]').forEach(b=>b.onclick=()=>{{document.querySelectorAll('button[data-sort]').forEach(x=>x.classList.remove('active')); b.classList.add('active'); sortKey=b.dataset.sort; render();}}); render();
</script></body></html>'''
(DOCS/'index.html').write_text(html_doc,encoding='utf-8')
print('wrote',DOCS/'index.html')
