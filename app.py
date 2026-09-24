"""Local prompt-to-image evolution, with a separately paced Spout output."""
import argparse, json, math, os, threading, time, traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import numpy as np
import cv2
from grid import SIZE, calibration, compose, export

ROOT=Path(__file__).resolve().parent
os.environ.setdefault('HF_HOME',str(ROOT/'models'))
os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING','1')
PROMPT='Bioluminescent flowing coral, liquid turquoise and magenta, intricate organic patterns, luminous abstract art, black background'
lock=threading.Lock()
stop=threading.Event()
settings=dict(prompt=PROMPT,layout='mosaic',gap=4,speed=0.08,brightness=1.0,freeze=False,blackout=False,calibrate=False)
status=dict(ai='Starting',ai_fps=0,output_fps=0,spout=False,error='',frames=0)
latest=None
jpeg=b''

def update(data):
    allowed=set(settings)
    if not isinstance(data,dict) or set(data)-allowed: raise ValueError('Unknown control')
    clean={}
    for k,v in data.items():
        if k=='prompt':
            if not isinstance(v,str) or not v.strip() or len(v)>2000: raise ValueError('Enter a prompt, up to 2000 characters')
            clean[k]=v.strip()
        elif k=='layout':
            if v not in ('mosaic','repeat'): raise ValueError('Invalid layout')
            clean[k]=v
        elif k in ('freeze','blackout','calibrate'):
            if type(v) is not bool: raise ValueError('Invalid switch')
            clean[k]=v
        else:
            lo,hi={'gap':(0,30),'speed':(0.005,0.5),'brightness':(0,1)}[k]
            n=float(v)
            if not math.isfinite(n) or not lo<=n<=hi: raise ValueError(f'{k} out of range')
            clean[k]=int(n) if k=='gap' else n
    with lock:
        settings.update(clean)
        temporary=ROOT/'settings.tmp'
        temporary.write_text(json.dumps(settings,indent=2),encoding='utf-8')
        temporary.replace(ROOT/'settings.json')

def generate():
    global latest
    try:
        import torch
        from diffusers import AutoPipelineForText2Image
        if not torch.cuda.is_available(): raise RuntimeError('NVIDIA CUDA is unavailable. Check the NVIDIA driver.')
        with lock: status['ai']='Loading SD-Turbo (first launch downloads model)'
        local_model=ROOT/'models/sd-turbo'
        model_source=str(local_model) if (local_model/'model_index.json').exists() else 'stabilityai/sd-turbo'
        pipe=AutoPipelineForText2Image.from_pretrained(model_source,torch_dtype=torch.float16,variant='fp16',use_safetensors=True,local_files_only=local_model.exists()).to('cuda')
        pipe.set_progress_bar_config(disable=True)
        rng=torch.Generator(device='cuda').manual_seed(240923)
        a=torch.randn((1,4,64,64),generator=rng,device='cuda',dtype=torch.float16)
        b=torch.randn(a.shape,generator=rng,device='cuda',dtype=torch.float16)
        phase=0.; old_prompt=None; embeds=None
        with torch.inference_mode():
            while not stop.is_set():
                with lock: s=settings.copy()
                if s['freeze'] or s['blackout'] or s['calibrate']:
                    stop.wait(.1); continue
                start=time.perf_counter()
                if s['prompt']!=old_prompt:
                    embeds=pipe.encode_prompt(s['prompt'],'cuda',1,False)[0]
                    old_prompt=s['prompt']
                latent=a*math.cos(phase*math.pi/2)+b*math.sin(phase*math.pi/2)
                result=pipe(prompt_embeds=embeds,latents=latent,num_inference_steps=1,guidance_scale=0.0,height=512,width=512).images[0]
                frame=np.asarray(result.convert('RGB'))
                elapsed=time.perf_counter()-start
                with lock:
                    latest=frame; status.update(ai='Generating',ai_fps=round(1/elapsed,2),frames=status['frames']+1)
                # Smooth noise evolution; this is image synthesis, not a temporal video model.
                phase+=min(elapsed,1.0)*s['speed']
                if phase>=1:
                    phase-=1; a=b; b=torch.randn(a.shape,generator=rng,device='cuda',dtype=torch.float16)
    except Exception as e:
        traceback.print_exc()
        with lock: status.update(ai='Error',error=str(e))

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def respond(self,code,body,kind):
        self.send_response(code); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store'); self.end_headers()
        try: self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError): pass
    def do_GET(self):
        path=self.path.split('?')[0]
        if path=='/': self.respond(200,(ROOT/'index.html').read_bytes(),'text/html; charset=utf-8')
        elif path=='/status':
            with lock: body=json.dumps(dict(settings=settings,status=status)).encode()
            self.respond(200,body,'application/json')
        elif path=='/preview.jpg':
            with lock: body=jpeg
            self.respond(200 if body else 503,body,'image/jpeg')
        else: self.respond(404,b'Not found','text/plain')
    def do_POST(self):
        # JSON only, localhost only, and reject requests initiated by another website.
        if self.headers.get('Origin') not in (None,f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'):
            return self.respond(403,b'Forbidden','text/plain')
        try:
            if self.path!='/control': raise ValueError('Unknown endpoint')
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=8192 or not self.headers.get('Content-Type','').startswith('application/json'): raise ValueError('JSON required')
            update(json.loads(self.rfile.read(length)))
            self.respond(200,b'{"ok":true}','application/json')
        except (ValueError,TypeError) as e: self.respond(400,json.dumps({'error':str(e)}).encode(),'application/json')

def run(args):
    global jpeg
    import glfw, SpoutGL
    from OpenGL.GL import GL_RGB
    if not glfw.init(): raise RuntimeError('Could not start OpenGL')
    glfw.window_hint(glfw.VISIBLE,glfw.FALSE)
    window=glfw.create_window(64,64,'LiveGrid Spout Context',None,None)
    if not window: raise RuntimeError('Could not create an OpenGL context')
    glfw.make_context_current(window)
    sender=SpoutGL.SpoutSender(); sender.setSenderName('LiveGrid-AI-100')
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    chart=calibration(); smooth=None
    if args.calibration:
        settings['calibrate']=True; status['ai']='Calibration only'
    else: threading.Thread(target=generate,daemon=True).start()
    begin=time.perf_counter(); tick=begin; count=0; lastpreview=0; sent=0
    print(f'LiveGrid ready: http://127.0.0.1:{args.port} | Spout: LiveGrid-AI-100',flush=True)
    try:
        while not stop.is_set() and (not args.seconds or time.perf_counter()-begin<args.seconds):
            started=time.perf_counter()
            with lock: s=settings.copy(); source=latest
            if source is not None and not s['freeze']:
                if smooth is None: smooth=source.astype(np.float32)
                else: cv2.accumulateWeighted(source,smooth,0.18)
            if s['blackout']: out=np.zeros_like(chart)
            elif s['calibrate'] or smooth is None: out=chart.copy()
            else: out=compose(smooth.astype(np.uint8),s['layout'],s['gap'])
            if s['brightness']<1: out=(out*s['brightness']).astype(np.uint8)
            ok=sender.sendImage(out,SIZE,SIZE,GL_RGB,False,0)
            glfw.poll_events()
            if ok: sent+=1
            if started-lastpreview>.12:
                preview=cv2.resize(out,(640,640))
                encoded=cv2.imencode('.jpg',cv2.cvtColor(preview,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,85])[1].tobytes()
                with lock: jpeg=encoded; status['spout']=bool(ok)
                lastpreview=started
            count+=1
            if started-tick>=1:
                with lock: status['output_fps']=round(count/(started-tick),1)
                count=0; tick=started
            stop.wait(max(0,1/30-(time.perf_counter()-started)))
    finally:
        stop.set(); server.shutdown(); sender.releaseSender(); glfw.destroy_window(window); glfw.terminate()
        print(json.dumps(dict(sent=sent,status=status)),flush=True)

if __name__=='__main__':
    if (ROOT/'settings.json').exists():
        try: update(json.loads((ROOT/'settings.json').read_text(encoding='utf-8')))
        except (ValueError,OSError): pass
    p=argparse.ArgumentParser(); p.add_argument('--calibration',action='store_true'); p.add_argument('--seconds',type=float,default=0); p.add_argument('--port',type=int,default=8765)
    run(p.parse_args())
