#!/usr/bin/env python3
"""Valida os requisitos de instalação/offline do PWA. Uso: python3 tools/validar_pwa.py (na raiz do projeto)."""
import json,os,re,struct,sys
RAIZ=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
erros=[];ok=[]
def c(cond,msg):
    (ok if cond else erros).append(msg)
def png_tam(p):
    with open(p,'rb') as f:
        h=f.read(24)
    return struct.unpack('>II',h[16:24]) if h[:8]==b'\x89PNG\r\n\x1a\n' else None
M=json.load(open(f'{RAIZ}/manifest.json',encoding='utf-8'))
for k in ['name','short_name','start_url','scope','display','theme_color','background_color','icons','orientation','lang','id']:
    c(k in M,f'manifest.{k}')
c(M.get('display') in('standalone','fullscreen'),'display standalone/fullscreen')
c(not M.get('start_url','').startswith('/'),'start_url relativo (GitHub Pages)')
c(not M.get('scope','').startswith('/'),'scope relativo (GitHub Pages)')
tam={}
for i in M['icons']:
    p=f"{RAIZ}/{i['src']}";c(os.path.exists(p),'ícone existe: '+i['src'])
    if os.path.exists(p):
        t=png_tam(p);w,h=map(int,i['sizes'].split('x'));c(t==(w,h),f"ícone {i['src']} tem {t} = {w}x{h}")
        tam.setdefault(i.get('purpose','any'),set()).add(w)
c({192,512}<=tam.get('any',set()),'ícones any 192 e 512')
c({192,512}<=tam.get('maskable',set()),'ícones maskable 192 e 512')
html=open(f'{RAIZ}/index.html',encoding='utf-8').read()
for t in ['rel="manifest"','name="viewport"','viewport-fit=cover','name="theme-color"','apple-mobile-web-app-capable','mobile-web-app-capable','apple-mobile-web-app-status-bar-style','apple-mobile-web-app-title','rel="apple-touch-icon"','apple-touch-startup-image','rel="icon"','msapplication-config']:
    c(t in html,'index.html: '+t)
for r in re.findall(r'(?:href|src)="([^"#]+)"',html):
    if r.startswith('http'):continue
    c(os.path.exists(f'{RAIZ}/'+r.split('?')[0]),'referência existe: '+r)
    c(not r.startswith('/'),'caminho relativo: '+r)
sw=open(f'{RAIZ}/service-worker.js',encoding='utf-8').read()
c("addEventListener('fetch'" in sw,'service worker trata fetch (offline)')
c('skipWaiting' in sw and 'clients.claim' in sw,'service worker atualiza sozinho')
pre=json.loads(re.search(r'const PRECACHE=(\[.*?\]);',sw,re.S).group(1))
for p in pre:
    c(os.path.exists(f'{RAIZ}/'+('index.html' if p=='./' else p)),'pré-cache existe: '+p)
c(any(p in('./','index.html') for p in pre),'pré-cache inclui a página inicial')
c("register('service-worker.js'" in open(f'{RAIZ}/js/pwa.js',encoding='utf-8').read(),'service worker registrado com caminho relativo')
for a in ['icons/apple-touch-icon.png','favicon.ico','browserconfig.xml','.nojekyll','404.html']:
    c(os.path.exists(f'{RAIZ}/{a}'),'arquivo: '+a)
for s in re.findall(r'href="(assets/splash/[^"]+)"',html):
    c(os.path.exists(f'{RAIZ}/{s}'),'splash existe: '+s)
css=open(f'{RAIZ}/css/app.css',encoding='utf-8').read()
c(not re.search(r'url\(\s*["\']?/(?!/)',css),'css sem caminhos absolutos')
js=open(f'{RAIZ}/js/game.js',encoding='utf-8').read()
c(not re.search(r'(?:src|href)=["\']/(?!/)',js),'js sem caminhos absolutos')
c("'assets/escudos/'" in js,'pasta de escudos relativa')
print(f'{len(ok)} verificações OK, {len(erros)} erro(s)')
for e in erros:print('ERRO:',e)
sys.exit(1 if erros else 0)
