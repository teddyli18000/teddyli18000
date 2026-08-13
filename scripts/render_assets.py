#!/usr/bin/env python3
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
FRAME_COUNT = 28
FRAME_MS = 450
HERO_SIZE = (960, 300)
NARROW_SIZE = (420, 180)
MILLIKAN_SIZE = (280, 96)
SIDEQUEST_SIZE = (220, 96)
LIGHT = (249, 247, 242)
DARK = (18, 19, 21)
INK_L = (30, 29, 27, 255)
INK_D = (243, 239, 232, 255)
CORAL = (194, 93, 70)
SAGE = (120, 137, 114)
SAND = (205, 181, 145)

FONTS = {
    'serif': ['/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf','C:/Windows/Fonts/georgia.ttf'],
    'sans': ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','C:/Windows/Fonts/SegUIVar.ttf'],
    'sans_medium': ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','C:/Windows/Fonts/seguisb.ttf'],
}

def face(kind, size):
    for p in FONTS[kind]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size=size)

def phase(i,total):
    return math.tau * i / (total - 1)

def paper(width,height,p,dark):
    bg = np.array(DARK if dark else LIGHT,dtype=np.float32)
    yy,xx = np.mgrid[0:height,0:width]
    u=xx/max(1,width-1); v=yy/max(1,height-1)
    canvas=np.broadcast_to(bg,(height,width,3)).copy()
    waves=[
        (0.5+0.5*np.sin(math.tau*(u*.42+v*.14)+.12*math.sin(p)), SAND, .13),
        (0.5+0.5*np.cos(math.tau*(u*.20-v*.50)-.16*math.sin(p)), SAGE, .075),
        (0.5+0.5*np.sin(math.tau*(u*.70+v*.24)+.12*math.cos(p)), CORAL, .045),
    ]
    for val,col,strength in waves:
        tone=np.array(col,dtype=np.float32)
        if dark:
            tone=bg+(tone-120)*.18
        canvas += (tone-bg)*(val-.5)[...,None]*strength
    grain=(np.sin(xx*.23+yy*.17)+np.cos(xx*.13-yy*.19))*0.23
    canvas += grain[...,None]
    im=Image.fromarray(np.uint8(np.clip(canvas,0,255)),'RGB').convert('RGBA')
    layer=Image.new('RGBA',(width,height),(0,0,0,0)); d=ImageDraw.Draw(layer,'RGBA')
    f=(236,229,216,13) if dark else (89,77,62,10)
    for k in range(9):
        base=height*(.13+k*.085); pts=[]
        for x in range(-10,width+11,20):
            q=x/max(1,width)
            y=base+1.1*math.sin(math.tau*q*.75+k*.45+p*.10)+.55*math.sin(math.tau*q*1.8+k)
            pts.append((x,y))
        d.line(pts,fill=f,width=1)
    return Image.alpha_composite(im,layer).convert('RGB')

def draw_type(im,dark,narrow=False):
    d=ImageDraw.Draw(im,'RGBA'); ink=INK_D if dark else INK_L
    if narrow:
        d.text((28,26),'Xinchen Lee',font=face('serif',37),fill=ink)
        d.text((30,91),'AI, systems, and',font=face('sans_medium',18),fill=ink)
        d.text((30,119),'things I felt like building.',font=face('sans',18),fill=ink)
    else:
        d.text((66,46),'Xinchen Lee',font=face('serif',60),fill=ink)
        d.text((70,143),'AI, systems, and things I felt like building.',font=face('sans_medium',24),fill=ink)
        d.line((70,194,389,194),fill=(235,228,216,62) if dark else (58,52,46,42),width=1)

def silk(im,p,dark,narrow=False):
    d=ImageDraw.Draw(im,'RGBA')
    if narrow:
        x0,x1,cy,amp=(235,420,67,17)
    else:
        x0,x1,cy,amp=(500,960,108,36)
    base=(226,218,204) if dark else (82,74,66)
    sage=(159,170,148) if dark else SAGE
    for j in range(7):
        pts=[]
        for x in np.linspace(x0,x1,160):
            q=(x-x0)/(x1-x0); envelope=.20+.80*q
            y=cy+(j-3)*4.5 + amp*math.sin(math.tau*(q*.78)+p*.34+j*.16)*envelope
            y += 7*math.sin(math.tau*(q*1.65)-p*.20+j*.42)*(.18+.82*q)
            pts.append((x,y))
        col=sage if j in (1,5) else base
        d.line(pts,fill=(*col,24 if j not in (2,3,4) else 38),width=1)
    t=(1-math.cos(p))/2
    x=x0+(x1-x0)*(.12+.66*t); q=(x-x0)/(x1-x0)
    y=cy+amp*math.sin(math.tau*(q*.78)+p*.34+.48)*(.20+.80*q)
    y += 7*math.sin(math.tau*(q*1.65)-p*.20+.84)*(.18+.82*q)
    r=2.5 if narrow else 3.5; accent=(222,126,97) if dark else CORAL
    d.ellipse((x-r,y-r,x+r,y+r),fill=(*accent,185))
    d.line((x-16,y+5,x-4,y+1),fill=(*accent,72),width=1)

def hero_frame(i,total,dark,narrow=False):
    p=phase(i,total); im=paper(*(NARROW_SIZE if narrow else HERO_SIZE),p,dark)
    silk(im,p,dark,narrow); draw_type(im,dark,narrow); return im

def millikan_frame(i,total,dark):
    p=phase(i,total); im=paper(*MILLIKAN_SIZE,p*.18,dark); d=ImageDraw.Draw(im,'RGBA')
    ink=(229,220,206,130) if dark else (73,66,57,105); accent=(222,126,97) if dark else CORAL
    d.line((34,23,244,23),fill=ink,width=1); d.line((34,73,244,73),fill=ink,width=1)
    for x in range(54,245,38):
        d.line((x,20,x,26),fill=(*ink[:3],70),width=1); d.line((x,70,x,76),fill=(*ink[:3],70),width=1)
    t=(1-math.cos(p))/2; y=31+33*t; x=139+4*math.sin(p*2)
    d.polygon([(x,y-7),(x-5,y),(x,y+6),(x+5,y)],fill=(*accent,185))
    span=13+2*math.sin(p)
    d.line((x-span,y,x+span,y),fill=(*ink[:3],80),width=1)
    d.line((x-span,y-3,x-span,y+3),fill=(*ink[:3],80),width=1)
    d.line((x+span,y-3,x+span,y+3),fill=(*ink[:3],80),width=1)
    return im

def sidequest_frame(i,total,dark):
    p=phase(i,total); im=paper(*SIDEQUEST_SIZE,p*.12,dark); d=ImageDraw.Draw(im,'RGBA')
    ink=(230,221,208,125) if dark else (70,64,56,92); accent=(222,126,97) if dark else CORAL
    ground=71; d.line((12,ground,208,ground),fill=(*ink[:3],70),width=1)
    d.rounded_rectangle((105,57,124,71),radius=2,outline=(*ink[:3],80),width=1)
    d.rounded_rectangle((124,51,143,71),radius=2,outline=(*ink[:3],80),width=1)
    t=(1-math.cos(p))/2; x=28+153*t; hop=31*math.exp(-((x-126)/42)**2); y=ground-14-hop; w,h=36,25
    fill=(35,36,38,230) if dark else (252,249,243,238)
    d.rounded_rectangle((x-w/2,y-h/2,x+w/2,y+h/2),radius=4,fill=fill,outline=(*accent,175),width=1)
    d.line((x-w/2+5,y-h/2+7,x+w/2-5,y-h/2+7),fill=(*ink[:3],100),width=1)
    for n in range(3):
        d.ellipse((x-w/2+5+n*5,y-h/2+2,x-w/2+7+n*5,y-h/2+4),fill=(*accent,125 if n==0 else 70))
    return im

def save(name,maker,dark,frames_count=FRAME_COUNT):
    ASSETS.mkdir(exist_ok=True); frames=[maker(i,frames_count,dark) for i in range(frames_count)]; stem=f"{name}-{'dark' if dark else 'light'}"
    frames[0].save(ASSETS/f'{stem}.png',optimize=True)
    pal=frames[0].quantize(colors=128,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    qs=[f.quantize(palette=pal,dither=Image.Dither.NONE) for f in frames]
    qs[0].save(ASSETS/f'{stem}.gif',save_all=True,append_images=qs[1:],duration=FRAME_MS,loop=0,disposal=1,optimize=True)

def main():
    for dark in (False,True):
        save('hero',lambda i,t,d:hero_frame(i,t,d,False),dark)
        save('hero-narrow',lambda i,t,d:hero_frame(i,t,d,True),dark)
        save('millikan-mark',millikan_frame,dark)
        save('sidequest',sidequest_frame,dark)
    print('Rendered human-motion profile assets')
if __name__=='__main__': main()
