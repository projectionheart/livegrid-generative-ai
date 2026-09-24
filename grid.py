"""The 100-square atlas, shared by the renderer and template exporter."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SIZE = 1080
N = 10
CELL = SIZE // N

def cells():
    return [dict(id=r*N+c+1, name=f'Square {r*N+c+1:03}', row=r+1, column=c+1,
                 pixels=[c*CELL,r*CELL,CELL,CELL], uv=[c/N,r/N,1/N,1/N])
            for r in range(N) for c in range(N)]

def calibration():
    im=Image.new('RGB',(SIZE,SIZE))
    d=ImageDraw.Draw(im)
    try: font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',30)
    except OSError: font=ImageFont.load_default(size=30)
    for cell in cells():
        x,y,w,h=cell['pixels']; r=cell['row']; c=cell['column']
        d.rectangle((x,y,x+w-1,y+h-1),fill=(18+r*8,25+c*8,60+(r+c)%2*35),outline='white',width=2)
        d.text((x+w/2,y+h/2),f"{cell['id']:03}",font=font,fill='white',anchor='mm')
        d.line((x+6,y+16,x+6,y+6,x+16,y+6),fill='#65ffc0',width=3)
    return np.array(im)

def compose(rgb, layout='mosaic', gap=4):
    import cv2
    gap=int(gap)
    if layout=='repeat':
        tile=cv2.resize(rgb,(CELL,CELL))
        out=np.tile(tile,(N,N,1))
    else: out=cv2.resize(rgb,(SIZE,SIZE))
    if gap:
        for pos in range(0,SIZE,CELL):
            out[pos:pos+gap,:,:]=0; out[:,pos:pos+gap,:]=0
        out[-gap:,:,:]=0; out[:,-gap:,:]=0
    return np.ascontiguousarray(out)

def export(directory):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    Image.fromarray(calibration()).save(directory/'Calibration-100.png')
    (directory/'Grid-100.json').write_text(json.dumps(dict(width=SIZE,height=SIZE,rows=N,columns=N,cells=cells()),indent=2))
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" viewBox="0 0 {SIZE} {SIZE}">']
    for cell in cells():
        x,y,w,h=cell['pixels']
        lines.append(f'<rect id="square-{cell["id"]:03}" x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="white"/>')
    (directory/'Grid-100.svg').write_text('\n'.join(lines+['</svg>']))

if __name__=='__main__': export(Path(__file__).parent/'template')
