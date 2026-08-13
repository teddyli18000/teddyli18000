#!/usr/bin/env python3
from __future__ import annotations
import json,re,struct,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; README=ROOT/'README.md'; ASSETS=ROOT/'assets'; GENERATOR=ROOT/'scripts/generate_profile.py'; LIVE=ROOT/'data/live.json'
def fail(m): raise SystemExit(f'FAIL: {m}')
def gif_frames(data,name):
    packed=data[10]; off=13+(3*(2**((packed&7)+1)) if packed&0x80 else 0); frames=0
    while off<len(data):
        b=data[off]
        if b==0x3B:return frames
        if b==0x21: off+=2
        elif b==0x2C:
            local=data[off+9]; off+=10+(3*(2**((local&7)+1)) if local&0x80 else 0)+1; frames+=1
        else: fail(f'{name}: invalid GIF block')
        while True:
            n=data[off]; off+=1
            if n==0: break
            off+=n
    fail(f'{name}: truncated GIF')
def raster(name,expected,min_frames=1):
    p=ASSETS/name; data=p.read_bytes()
    if name.endswith('.png') and data[:8]==b'\x89PNG\r\n\x1a\n': w,h=struct.unpack('>II',data[16:24]); frames=1
    elif name.endswith('.gif') and data[:6] in {b'GIF87a',b'GIF89a'}: w,h=struct.unpack('<HH',data[6:10]); frames=gif_frames(data,name)
    else: fail(f'{name}: unreadable raster')
    if (w,h)!=expected: fail(f'{name}: {(w,h)} != {expected}')
    if name.endswith('.gif') and frames<min_frames: fail(f'{name}: too few frames')
    if p.stat().st_size>6*1024*1024: fail(f'{name}: too large')
def main():
    readme=README.read_text(encoding='utf-8'); lower=readme.lower()
    for marker in ('profile-live:start','profile-live:end','profile-footer:start','profile-footer:end'):
        if readme.count(marker)!=1: fail(f'invalid {marker}')
    for bad in ('live-signal-','the repository is the proof surface','motion and system references'):
        if bad in lower: fail(f'forbidden public-surface token: {bad}')
    sections=('## Selected work','### Current lines of work','## Open source / live','## Side quests'); pos=[readme.find(x) for x in sections]
    if min(pos)<0 or pos!=sorted(pos): fail('section order')
    if '<img width="280"' not in readme or '<img width="220"' not in readme: fail('micro motion must render at native scale')
    live=readme.split('<!-- profile-live:start -->',1)[1].split('<!-- profile-live:end -->',1)[0]
    if len(re.findall(r'https://github\.com/[^)\s]+/pull/\d+',live))!=3: fail('live block needs three upstream PRs')
    if not re.search(r'updated \d{1,2} [A-Z][a-z]{2} · \d{2}:\d{2} SGT',live): fail('live timestamp')
    refs=re.findall(r'(?:src|srcset)="\./([^" ]+)"',readme)
    for ref in refs:
        if not (ROOT/ref).is_file(): fail(f'missing {ref}')
    for n in ('hero-light.gif','hero-dark.gif'): raster(n,(960,300),16)
    for n in ('hero-light.png','hero-dark.png'): raster(n,(960,300))
    for n in ('hero-narrow-light.gif','hero-narrow-dark.gif'): raster(n,(420,180),16)
    for n in ('hero-narrow-light.png','hero-narrow-dark.png'): raster(n,(420,180))
    for n in ('millikan-mark-light.gif','millikan-mark-dark.gif'): raster(n,(280,96),16)
    for n in ('millikan-mark-light.png','millikan-mark-dark.png'): raster(n,(280,96))
    for n in ('sidequest-light.gif','sidequest-dark.gif'): raster(n,(220,96),16)
    for n in ('sidequest-light.png','sidequest-dark.png'): raster(n,(220,96))
    for n in ('live-light.svg','live-dark.svg'):
        text=(ASSETS/n).read_text(encoding='utf-8'); root=ET.fromstring(text)
        if root.attrib.get('width') not in {'960','960px'} or root.attrib.get('height') not in {'180','180px'}: fail(f'{n}: wrong SVG size')
        if '<circle' in text or 'LIVE SIGNAL' in text or 'FIELD 01' in text: fail(f'{n}: decorative status motif returned')
        if len(re.findall(r'class="value"',text))!=3 or len(re.findall(r'class="label"',text))!=3: fail(f'{n}: metric count')
    data=json.loads(LIVE.read_text(encoding='utf-8'))
    for k in ('year','contributions','active_public_repos','upstream_prs','updated_at'):
        if k not in data: fail(f'live.json missing {k}')
    gen=GENERATOR.read_text(encoding='utf-8')
    for token in ('live_markdown','live-light.svg','live-dark.svg','height="180"'):
        if token not in gen: fail(f'generator missing {token}')
    total=sum(p.stat().st_size for p in ASSETS.iterdir() if p.is_file())
    if total>20*1024*1024: fail('asset budget')
    print(f'PASS: {len(refs)} local refs; assets {total/1024/1024:.2f} MiB')
if __name__=='__main__': main()
