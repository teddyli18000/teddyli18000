#!/usr/bin/env python3
"""Refresh truthful public GitHub activity and the date-seeded footer."""
from __future__ import annotations
import datetime as dt
import html
import json
import os
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
README=ROOT/'README.md'; DATA=ROOT/'data/content.json'; LIVE=ROOT/'data/live.json'
LOGIN=os.environ.get('PROFILE_LOGIN','teddyli18000')
TOKEN=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
SGT=dt.timezone(dt.timedelta(hours=8),name='SGT')

def api(path:str,*,graphql:dict[str,object]|None=None)->dict:
    payload=json.dumps(graphql).encode() if graphql is not None else None
    req=urllib.request.Request('https://api.github.com/graphql',data=payload,method='POST') if graphql is not None else urllib.request.Request(f'https://api.github.com/{path}')
    req.add_header('Accept','application/vnd.github+json'); req.add_header('User-Agent',f'{LOGIN}-profile-readme'); req.add_header('X-GitHub-Api-Version','2022-11-28')
    if TOKEN: req.add_header('Authorization',f'Bearer {TOKEN}')
    try:
        with urllib.request.urlopen(req,timeout=30) as r: return json.load(r)
    except Exception:
        if not shutil.which('gh'): raise
        if graphql is not None:
            proc=subprocess.run(['gh','api','graphql','--input','-'],input=payload,capture_output=True,check=True)
        else:
            proc=subprocess.run(['gh','api',path],capture_output=True,check=True)
        return json.loads(proc.stdout)

def fetch_profile()->dict:
    now=dt.datetime.now(dt.timezone.utc); start=dt.datetime(now.year,1,1,tzinfo=dt.timezone.utc)
    query='''query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){contributionsCollection(from:$from,to:$to){contributionCalendar{totalContributions}} repositories(first:100,privacy:PUBLIC,ownerAffiliations:OWNER){nodes{name isFork isArchived}}}}'''
    graph=api('',graphql={'query':query,'variables':{'login':LOGIN,'from':start.isoformat().replace('+00:00','Z'),'to':now.isoformat().replace('+00:00','Z')}})['data']['user']
    qs=urllib.parse.urlencode({'q':f'author:{LOGIN} type:pr -user:{LOGIN}','per_page':30}); pulls=api(f'search/issues?{qs}')
    external=[]
    for item in pulls['items']:
        repo=item['repository_url'].split('/repos/',1)[1]; number=item['number']; detail=api(f'repos/{repo}/pulls/{number}')
        status='merged' if detail.get('merged') else ('draft' if detail.get('draft') else item['state'])
        external.append({'repo':repo,'number':number,'title':item['title'],'url':item['html_url'],'status':status,'updated_at':item['updated_at']})
    active=sum(1 for r in graph['repositories']['nodes'] if not r['isFork'] and not r['isArchived'])
    return {'year':now.year,'contributions':graph['contributionsCollection']['contributionCalendar']['totalContributions'],'active_public_repos':active,'upstream_prs':pulls['total_count'],'external':external}

def choose_external(items:list[dict])->list[dict]:
    rank={'merged':0,'open':1,'draft':2,'closed':3}
    return sorted(items,key=lambda x:(rank.get(x['status'],4),-dt.datetime.fromisoformat(x['updated_at'].replace('Z','+00:00')).timestamp()))[:3]

def last_good()->tuple[dict,list[dict],dt.datetime]:
    snap=json.loads(LIVE.read_text(encoding='utf-8')); required=('year','contributions','active_public_repos','upstream_prs','updated_at')
    if any(k not in snap for k in required): raise ValueError('live.json missing required fields')
    chosen=snap.get('selected_external') or choose_external(snap.get('external',[]))
    if len(chosen)!=3: raise ValueError('live.json needs three upstream PRs')
    stamp=dt.datetime.fromisoformat(snap['updated_at'].replace('Z','+00:00')).astimezone(SGT)
    return snap,chosen,stamp

def collect()->tuple[dict,list[dict],dt.datetime,bool]:
    try:
        stats=fetch_profile(); chosen=choose_external(stats['external'])
        if len(chosen)!=3: raise ValueError('expected three upstream PRs')
        return stats,chosen,dt.datetime.now(SGT),True
    except Exception as e:
        stats,chosen,stamp=last_good(); print(f'GitHub refresh failed ({e}); retaining {stamp.isoformat()}'); return stats,chosen,stamp,False

def replace_block(text:str,name:str,body:str)->str:
    start=f'<!-- profile-{name}:start -->'; end=f'<!-- profile-{name}:end -->'
    if text.count(start)!=1 or text.count(end)!=1: raise ValueError(f'invalid {name} markers')
    before,rest=text.split(start,1); _,after=rest.split(end,1); return f'{before}{start}\n{body.rstrip()}\n{end}{after}'

def live_markdown(stats:dict,chosen:list[dict],updated:dt.datetime)->str:
    notes=json.loads(DATA.read_text(encoding='utf-8')).get('external_notes',{})
    lines=['<picture>','  <source media="(prefers-color-scheme: dark)" srcset="./assets/live-dark.svg">','  <img width="100%" alt="Public GitHub activity with contributions, active public repositories, and upstream pull requests." src="./assets/live-light.svg">','</picture>','','**Outside my repos**','']
    for item in chosen:
        key=f"{item['repo']}#{item['number']}"; note=notes.get(key,item['title']); lines.append(f"- {item['status']} → [{item['repo']} #{item['number']}]({item['url']}) · {note}")
    stamp=updated.strftime('%d %b · %H:%M SGT').lstrip('0'); lines += ['',f'<sub>generated from public GitHub activity · updated {stamp}</sub>']
    return '\n'.join(lines)

def svg(stats:dict,updated:dt.datetime,dark:bool)->str:
    bg='#121315' if dark else '#f9f7f2'; ink='#f2eee7' if dark else '#1e1d1b'; muted='#aaa69f' if dark else '#777169'; rule='#3a3937' if dark else '#d8d1c7'; accent='#d89276' if dark else '#bd654e'
    stamp=updated.strftime('%d %b %Y · %H:%M SGT').lstrip('0')
    vals=[(str(stats['contributions']),f"CONTRIBUTIONS / {stats['year']}"),(str(stats['active_public_repos']),'ACTIVE PUBLIC REPOS'),(str(stats['upstream_prs']),'UPSTREAM PRS')]
    xs=(58,375,665); nodes=''.join(f'<text x="{x}" y="102" class="value">{html.escape(v)}</text><text x="{x}" y="128" class="label">{html.escape(l)}</text>' for x,(v,l) in zip(xs,vals))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="180" viewBox="0 0 960 180" role="img" aria-label="Public GitHub activity">
  <rect width="960" height="180" fill="{bg}"/>
  <path d="M58 34 H902" stroke="{rule}" stroke-opacity=".72"/>
  <path d="M58 148 H902" stroke="{rule}" stroke-opacity=".72"/>
  <path d="M58 34 H142" stroke="{accent}" stroke-width="2" stroke-opacity=".75"/>
  <path d="M335 58 V133 M625 58 V133" stroke="{rule}" stroke-opacity=".62"/>
  <text x="902" y="27" text-anchor="end" class="stamp">updated {html.escape(stamp)}</text>
  {nodes}
  <style>
    .value{{font-family:Georgia,ui-serif,serif;font-size:40px;fill:{ink};letter-spacing:-1px}}
    .label,.stamp{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:11px;letter-spacing:1.45px;fill:{muted}}}
  </style>
</svg>'''

def main()->None:
    stats,chosen,updated,fresh=collect(); text=README.read_text(encoding='utf-8'); text=replace_block(text,'live',live_markdown(stats,chosen,updated))
    content=json.loads(DATA.read_text(encoding='utf-8')); footer=content['footer_lines'][int(dt.datetime.now(SGT).strftime('%Y%j'))%len(content['footer_lines'])]; text=replace_block(text,'footer',f'<sub>{footer}</sub>'); README.write_text(text,encoding='utf-8',newline='\n')
    if fresh:
        (ROOT/'assets/live-light.svg').write_text(svg(stats,updated,False),encoding='utf-8'); (ROOT/'assets/live-dark.svg').write_text(svg(stats,updated,True),encoding='utf-8')
        LIVE.write_text(json.dumps({**stats,'selected_external':chosen,'updated_at':updated.isoformat()},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"{'Updated' if fresh else 'Retained'} {stats['contributions']} contributions, {stats['active_public_repos']} active public repos, {stats['upstream_prs']} upstream PRs at {updated.isoformat()}")
if __name__=='__main__': main()
