#!/usr/bin/env python3
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]; ASSETS=ROOT/'assets'
FRAME_COUNT=28; FRAME_MS=420
HERO_SIZE=(960,300); NARROW_SIZE=(420,180); MILLIKAN_SIZE=(960,56); SIDEQUEST_SIZE=(960,70)
LIGHT=(248,246,241); DARK=(17,18,20); INK_L=(28,27,25,255); INK_D=(242,238,230,255)
CORAL=(205,104,77); SAGE=(126,142,120); SAND=(212,188,150)
FONTS={'serif':['/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf','C:/Windows/Fonts/georgia.ttf'],'sans':['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','C:/Windows/Fonts/SegUIVar.ttf'],'sans_medium':['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','C:/Windows/Fonts/seguisb.ttf']}

def face(kind,size):
    for p in FONTS[kind]:
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default(size=size)
def phase(i,total): return math.tau*i/(total-1)
def paper_field(width,height,p,dark):
    bg=np.array(DARK if dark else LIGHT,dtype=np.float32); yy,xx=np.mgrid[0:height,0:width]; u=xx/max(1,width-1); v=yy/max(1,height-1)
    centers=[(.78+.025*math.sin(p),.18+.03*math.cos(p),SAND,.22,.34),(.62+.03*math.cos(p),.72+.025*math.sin(2*p),SAGE,.18,.40),(.93+.02*math.sin(2*p),.58+.02*math.cos(p),CORAL,.10,.28)]
    canvas=np.broadcast_to(bg,(height,width,3)).copy()
    for cx,cy,c,amt,rad in centers:
        dx=(u-cx)/rad; dy=(v-cy)/(rad*1.25); w=np.exp(-(dx*dx+dy*dy)*2.4)*amt; tone=np.array(c,dtype=np.float32)
        if dark: tone=bg+(tone-110)*.22
        canvas+=(tone-bg)*w[...,None]
    canvas+=(np.sin(xx*.19+yy*.13)+np.cos(xx*.11-yy*.17))[...,None]*.32
    im=Image.fromarray(np.uint8(np.clip(canvas,0,255)),'RGB').convert('RGBA'); layer=Image.new('RGBA',(width,height),(0,0,0,0)); d=ImageDraw.Draw(layer,'RGBA'); fibre=(230,226,214,16) if dark else (91,81,68,12)
    for k in range(11):
        y0=height*(.11+k*.072); pts=[]
        for x in range(-20,width+21,16):
            q=x/width; y=y0+4.5*math.sin(math.tau*(q*.82)+p+k*.37)+1.8*math.sin(math.tau*(q*1.7)-p*.5+k); pts.append((x,y))
        d.line(pts,fill=fibre,width=1)
    return Image.alpha_composite(im,layer).convert('RGB')
def draw_type(im,dark,narrow=False):
    d=ImageDraw.Draw(im,'RGBA'); ink=INK_D if dark else INK_L
    if narrow:
        d.text((28,28),'Xinchen Lee',font=face('serif',38),fill=ink); d.text((30,92),'AI, systems, and',font=face('sans_medium',18),fill=ink); d.text((30,119),'things I felt like building.',font=face('sans',18),fill=ink)
    else:
        d.text((66,48),'Xinchen Lee',font=face('serif',60),fill=ink); d.text((70,143),'AI, systems, and things I felt like building.',font=face('sans_medium',24),fill=ink); d.line((70,194,390,194),fill=(230,226,214,80) if dark else (60,55,49,45),width=1)
def ribbon(im,p,dark,narrow=False):
    d=ImageDraw.Draw(im,'RGBA'); x0,x1,cy,amp=(245,406,74,16) if narrow else (515,932,112,30); base=(230,225,214) if dark else (75,69,62); accent=(221,130,96) if dark else CORAL
    for j in range(5):
        pts=[]
        for x in np.linspace(x0,x1,130):
            q=(x-x0)/(x1-x0); y=cy+(j-2)*5+amp*math.sin(math.tau*(q*.78)+p+j*.22)*(.35+.65*q)+7*math.sin(math.tau*(q*1.9)-p*.5+j*.31)*(.2+.8*q); pts.append((x,y))
        d.line(pts,fill=(*base,34 if j!=2 else 58),width=1)
    t=(1-math.cos(p))/2; x=x0+(x1-x0)*(.12+.70*t); q=(x-x0)/(x1-x0); y=cy+amp*math.sin(math.tau*(q*.78)+p+.44)*(.35+.65*q)+7*math.sin(math.tau*(q*1.9)-p*.5+.62)*(.2+.8*q); r=3 if narrow else 4; d.ellipse((x-r,y-r,x+r,y+r),fill=(*accent,175 if dark else 160)); box=(333,127,397,174) if narrow else (822,203,918,270); d.arc(box,start=205+2*math.sin(p),end=300+2*math.sin(p),fill=(255,252,245,120) if dark else (255,255,251,170),width=2); d.arc((box[0]+1,box[1]+1,box[2]+1,box[3]+1),start=205,end=300,fill=(*accent,70),width=1)
def hero_frame(i,total,dark,narrow=False):
    p=phase(i,total); im=paper_field(*(NARROW_SIZE if narrow else HERO_SIZE),p,dark); ribbon(im,p,dark,narrow); draw_type(im,dark,narrow); return im
def millikan_frame(i,total,dark):
    p=phase(i,total); im=paper_field(*MILLIKAN_SIZE,p*.35,dark); d=ImageDraw.Draw(im,'RGBA'); ink=(225,217,204,105) if dark else (76,69,60,85); d.line((420,14,540,14),fill=ink,width=1); d.line((420,45,540,45),fill=ink,width=1); d.line((438,11,438,48),fill=(*ink[:3],55),width=1); d.line((522,11,522,48),fill=(*ink[:3],55),width=1); t=(1-math.cos(p))/2; y=20+18*t; x=480+4*math.sin(p*2); d.polygon([(x,y-6),(x-4,y),(x,y+5),(x+4,y)],fill=(*CORAL,165 if dark else 150)); pts=[]
    for n in range(40):
        q=n/39; pts.append((560+q*120,30+6*math.sin(q*math.tau*1.1+p*.5)*math.exp(-q*1.2)))
    d.line(pts,fill=ink,width=1); return im
def sidequest_frame(i,total,dark):
    p=phase(i,total); im=paper_field(*SIDEQUEST_SIZE,p*.25,dark); d=ImageDraw.Draw(im,'RGBA'); ink=(226,218,205,105) if dark else (74,68,60,78); y=45; d.line((580,y,882,y),fill=ink,width=1); d.line((742,31,742,55),fill=(*ink[:3],65),width=1); t=(1-math.cos(p))/2; x=620+235*t; hop=23*math.sin(math.pi*t)**1.7; yy=y-hop; w,h=38,23; d.rounded_rectangle((x-w/2,yy-h/2,x+w/2,yy+h/2),radius=3,fill=(248,244,236,210) if not dark else (33,34,36,230),outline=(*CORAL,150),width=1); d.line((x-w/2+5,yy-h/2+6,x+w/2-5,yy-h/2+6),fill=(*ink[:3],90),width=1); d.ellipse((x-w/2+5,yy-h/2+2,x-w/2+7,yy-h/2+4),fill=(*CORAL,150)); return im
def save(name,maker,dark):
    ASSETS.mkdir(exist_ok=True); frames=[maker(i,FRAME_COUNT,dark) for i in range(FRAME_COUNT)]; stem=f"{name}-{'dark' if dark else 'light'}"; frames[0].save(ASSETS/f'{stem}.png',optimize=True); pal=frames[0].quantize(colors=96,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE); qs=[f.quantize(palette=pal,dither=Image.Dither.NONE) for f in frames]; qs[0].save(ASSETS/f'{stem}.gif',save_all=True,append_images=qs[1:],duration=FRAME_MS,loop=0,disposal=1,optimize=True)
def main():
    for dark in (False,True):
        save('hero',lambda i,t,d:hero_frame(i,t,d,False),dark); save('hero-narrow',lambda i,t,d:hero_frame(i,t,d,True),dark); save('millikan-mark',millikan_frame,dark); save('sidequest',sidequest_frame,dark)
    print('Rendered profile motion assets')
if __name__=='__main__': main()
