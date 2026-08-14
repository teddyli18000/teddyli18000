#!/usr/bin/env python3
from __future__ import annotations
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
ASSETS.mkdir(parents=True, exist_ok=True)
FRAME_COUNT = 64
FRAME_MS = 180
LIGHT=(248,246,241)
DARK=(18,19,20)
INK_L=(32,30,27,255)
INK_D=(244,239,231,255)
CORAL=(192,96,73)
SAGE=(112,135,116)
SAND=(181,150,110)

SERIF_CANDS=[
 '/usr/share/fonts/opentype/ebgaramond/EBGaramond-Regular.otf',
 '/usr/share/fonts/truetype/ebgaramond/EBGaramond12-Regular.ttf',
 'C:/Windows/Fonts/georgia.ttf',
 '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
]
SANS_CANDS=[
 '/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf',
 '/usr/share/fonts/opentype/inter/Inter-Regular.otf',
 'C:/Windows/Fonts/SegUIVar.ttf',
 '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
]

def get_font(size:int, serif=False):
    for p in (SERIF_CANDS if serif else SANS_CANDS):
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default(size=size)

def phase(i:int,total:int=FRAME_COUNT):
    return math.tau*i/(total-1)

def paper(size,dark=False):
    w,h=size
    img=Image.new('RGB',size,DARK if dark else LIGHT)
    d=ImageDraw.Draw(img,'RGBA')
    fibre=(236,230,218,15) if dark else (83,72,58,9)
    for y in range(16,h,11):
        drift=((y*13)%17)-8
        d.line((0,y,w,y+drift*0.035),fill=fibre,width=1)
    short=(238,232,220,13) if dark else (94,82,68,7)
    for k in range(42):
        y=(k*37+19)%h; x=(k*97+41)%w; ln=35+(k*29)%110
        d.line((x,y,min(w,x+ln),y),fill=short,width=1)
    return img

def cubic(p0,p1,p2,p3,n=160):
    pts=[]
    for i in range(n+1):
        t=i/n; u=1-t
        pts.append((u**3*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t**3*p3[0],
                    u**3*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t**3*p3[1]))
    return pts

def ribbon_field(size, p, dark=False, compact=False):
    w,h=size
    layer=Image.new('RGBA',size,(0,0,0,0))
    if compact:
        specs=[
            (SAGE, 25, ((w*.55,h*.18),(w*.70,h*.06),(w*.78,h*.46),(w*1.05,h*.28))),
            (CORAL,20, ((w*.62,h*.72),(w*.77,h*.53),(w*.86,h*.95),(w*1.08,h*.70))),
        ]
    else:
        specs=[
            (SAND,34, ((w*.57,h*.12),(w*.73,h*-.03),(w*.77,h*.45),(w*1.05,h*.21))),
            (SAGE,42, ((w*.61,h*.42),(w*.72,h*.18),(w*.88,h*.62),(w*1.08,h*.39))),
            (CORAL,28, ((w*.66,h*.80),(w*.80,h*.58),(w*.86,h*1.04),(w*1.08,h*.73))),
        ]
    for idx,(col,width,ctrl) in enumerate(specs):
        dx=3.2*math.sin(p+idx*.8)
        dy=4.0*math.sin(p+idx*1.1)
        p0,p1,p2,p3=ctrl
        pts=cubic((p0[0],p0[1]+dy*.25),(p1[0]+dx,p1[1]+dy),(p2[0]-dx*.6,p2[1]-dy*.5),(p3[0],p3[1]+dy*.2))
        shadow=Image.new('RGBA',size,(0,0,0,0)); sd=ImageDraw.Draw(shadow,'RGBA')
        sd.line([(x+4,y+6) for x,y in pts],fill=(0,0,0,18 if not dark else 40),width=width+4,joint='curve')
        shadow=shadow.filter(ImageFilter.GaussianBlur(10 if not compact else 7))
        layer=Image.alpha_composite(layer,shadow)
        body=Image.new('RGBA',size,(0,0,0,0)); bd=ImageDraw.Draw(body,'RGBA')
        bd.line(pts,fill=(*col,42 if dark else 38),width=width,joint='curve')
        bd.line(pts,fill=(255,249,238,48 if dark else 70),width=2,joint='curve')
        body=body.filter(ImageFilter.GaussianBlur(.7))
        layer=Image.alpha_composite(layer,body)
    sweep=(1-math.cos(p))/2
    x=int(w*(.63+.24*sweep))
    sheen=Image.new('RGBA',size,(0,0,0,0)); sd=ImageDraw.Draw(sheen,'RGBA')
    sd.line((x,int(h*.08),x+12,int(h*.89)),fill=(255,252,244,42 if dark else 76),width=2)
    sheen=sheen.filter(ImageFilter.GaussianBlur(7))
    return Image.alpha_composite(layer,sheen)

def draw_type(img,dark=False,narrow=False):
    d=ImageDraw.Draw(img,'RGBA'); ink=INK_D if dark else INK_L
    if narrow:
        d.text((27,28),'Xinchen Lee',font=get_font(42,True),fill=ink)
        d.text((29,92),'AI, systems, and',font=get_font(18),fill=ink)
        d.text((29,120),'things I felt like building.',font=get_font(18),fill=ink)
    else:
        d.text((63,52),'Xinchen Lee',font=get_font(72,True),fill=ink)
        d.text((68,157),'AI, systems, and things I felt like building.',font=get_font(25),fill=ink)
        d.line((68,207,388,207),fill=(235,229,219,60) if dark else (68,60,53,38),width=1)

def hero_frame(i,dark=False,narrow=False):
    size=(420,180) if narrow else (960,300)
    p=phase(i)
    base=paper(size,dark).convert('RGBA')
    base=Image.alpha_composite(base,ribbon_field(size,p,dark,compact=narrow))
    img=base.convert('RGB'); draw_type(img,dark,narrow)
    return img

def millikan_frame(i,dark=False):
    size=(520,96); p=phase(i)
    img=paper(size,dark); d=ImageDraw.Draw(img,'RGBA')
    ink=(231,224,213,125) if dark else (62,57,51,98)
    soft=(*ink[:3],42)
    accent=(222,126,99) if dark else CORAL
    x0,x1=34,486; yt,yb=24,72
    d.line((x0,yt,x1,yt),fill=ink,width=1); d.line((x0,yb,x1,yb),fill=ink,width=1)
    for x in range(60,470,48): d.line((x,yb-3,x,yb+3),fill=soft,width=1)
    travel=(1-math.cos(p))/2
    x=252+7*math.sin(p*2); y=62-27*travel; span=17
    d.line((x-span,y,x-7,y),fill=soft,width=1); d.line((x+7,y,x+span,y),fill=soft,width=1)
    d.line((x-span,y-3,x-span,y+3),fill=soft,width=1); d.line((x+span,y-3,x+span,y+3),fill=soft,width=1)
    r=4.2
    d.ellipse((x-r,y-r,x+r,y+r),fill=(*accent,215))
    d.ellipse((x-1.7,y-2.5,x+.2,y-.6),fill=(255,247,236,155))
    return img

def window_tile(dark=False):
    tile=Image.new('RGBA',(56,42),(0,0,0,0)); d=ImageDraw.Draw(tile,'RGBA')
    outline=(235,229,219,150) if dark else (64,59,53,108)
    fill=(31,33,34,236) if dark else (251,248,242,244)
    d.rounded_rectangle((3,4,52,38),radius=5,fill=fill,outline=outline,width=1)
    d.line((4,13,51,13),fill=outline,width=1)
    for j,c in enumerate((CORAL,SAND,SAGE)): d.ellipse((8+j*7,8,11+j*7,11),fill=(*c,170))
    d.line((11,22,37,22),fill=(*outline[:3],54),width=1)
    d.line((11,27,31,27),fill=(*outline[:3],38),width=1)
    return tile

def sidequest_frame(i,dark=False):
    size=(360,92); p=phase(i)
    img=paper(size,dark); d=ImageDraw.Draw(img,'RGBA')
    neutral=(231,224,213,85) if dark else (68,62,55,56)
    accent=(222,126,99) if dark else CORAL
    ground=68
    d.line((24,ground,334,ground),fill=neutral,width=1)
    d.rounded_rectangle((174,55,194,68),radius=2,fill=(*neutral[:3],30),outline=neutral,width=1)
    d.rounded_rectangle((194,49,213,68),radius=2,fill=(*neutral[:3],24),outline=neutral,width=1)
    progress=(1-math.cos(p))/2; x=62+216*progress; hop=29*(math.sin(math.pi*progress)**2); y=ground-20-hop
    tile=window_tile(dark).rotate(3.0*math.sin(p),resample=Image.Resampling.BICUBIC,expand=True)
    img.paste(tile,(int(x-tile.width/2),int(y-tile.height/2)),tile)
    d=ImageDraw.Draw(img,'RGBA'); shadow_w=18-6*(hop/29 if hop else 0)
    d.ellipse((x-shadow_w,ground+4,x+shadow_w,ground+7),fill=(*accent,48))
    return img

def save_anim(stem,frames,colors=128):
    frames=[f.convert('RGB') for f in frames]
    frames[0].save(ASSETS/f'{stem}.png',optimize=True)
    pal=frames[0].quantize(colors=colors,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    idx=[f.quantize(palette=pal,dither=Image.Dither.NONE) for f in frames]
    idx[0].save(ASSETS/f'{stem}.gif',save_all=True,append_images=idx[1:],duration=FRAME_MS,loop=0,disposal=1,optimize=True)

def main():
    for dark in (False,True):
        s='dark' if dark else 'light'
        save_anim(f'hero-{s}',[hero_frame(i,dark,False) for i in range(FRAME_COUNT)],160)
        save_anim(f'hero-narrow-{s}',[hero_frame(i,dark,True) for i in range(FRAME_COUNT)],144)
        save_anim(f'millikan-mark-{s}',[millikan_frame(i,dark) for i in range(FRAME_COUNT)],96)
        save_anim(f'sidequest-{s}',[sidequest_frame(i,dark) for i in range(FRAME_COUNT)],96)
    print('Rendered authored motion assets')
if __name__=='__main__': main()
