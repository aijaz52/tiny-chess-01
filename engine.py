import os,json,urllib.request as L
e=range;P,N,B,R,Q,K=e(1,7);V=[0,100,320,330,500,900,0];D={N:(33,31,18,14,-14,-18,-31,-33),B:(17,15,-15,-17),R:(16,-16,1,-1)};D[Q]=D[K]=D[B]+D[R];U=os.getenv('MAKEFUN_ENV_URL')
def a(s):return'abcdefgh'[s&7]+str(1+(s>>4))
def j(s):return ord(s[0])-97+(int(s[1])-1)*16
class S:
 def __init__(s):s.b=[0]*128;s.s=s.c=s.h=0;s.e=-1;s.k=[-1,-1]
def pf(f):
 s=S();x=f.split()
 for r,row in enumerate(x[0].split('/')):
  c=0
  for p in row:
   if p.isdigit():c+=int(p)
   else:
    t=' pnbrqk'.index(p.lower());z=(7-r)*16+c;s.b[z]=(not p.isupper())<<3|t
    if t==K:s.k[not p.isupper()]=z
    c+=1
 s.s=x[1]!='w';s.c=sum(1<<'KQkq'.index(c)for c in x[2]if c in'KQkq');s.e=j(x[3])if len(x)>3 and x[3]!='-'else-1;return s
def ia(s,C,c):
 b=s.b
 for d in((-15,-17)if c==0 else(15,17)):
  t=C+d
  if not t&136 and b[t]==c*8+P:return 1
 for J in(N,K):
  for d in D[J]:
   t=C+d
   if not t&136 and b[t]&7==J and b[t]>>3==c:return 1
 for J in(B,R):
  for d in D[J]:
   t=C+d
   while not t&136:
    p=b[t]
    if p:
     if p&7 in(J,Q)and p>>3==c:return 1
     break
    t+=d
 return 0
def ic(s,c):return ia(s,s.k[c],c^1)if s.k[c]>=0 else 0
def gp(s):
 b=s.b;w=s.s;h=w^1;m=[]
 for C in e(128):
  p=b[C]
  if C&136 or not p or p>>3!=w:continue
  J=p&7
  if J==P:
   d=16-32*w;last=7-7*w;t=C+d
   if not t&136 and not b[t]:
    if t>>4==last:
     for x in(N,B,R,Q):m.append(C|t<<7|x<<14|3<<21)
    else:
     m.append(C|t<<7)
     if C>>4==1+5*w and not b[t+d]:m.append(C|(t+d)<<7)
   for t in(C+d-1,C+d+1):
    if t&136:continue
    X=b[t]
    if X and X>>3==h:
     if t>>4==last:
      for x in(N,B,R,Q):m.append(C|t<<7|x<<14|X<<17|3<<21)
     else:m.append(C|t<<7|X<<17)
    elif t==s.e:m.append(C|t<<7|b[t-d]<<17|1<<21)
  else:
   for d in D[J]:
    t=C+d
    while not t&136:
     X=b[t]
     if not X or X>>3!=w:m.append(C|t<<7|X<<17)
     if X or J in(N,K):break
     t+=d
   if J==K:
    v=112*w
    for f,g,x,y,z in((1,6,5,6,0),(2,2,3,2,1)):
     if s.c&f<<2*w and not b[v+x]and not b[v+y]and(not z or not b[v+z])and not ia(s,v+4,h)and not ia(s,v+x,h)and not ia(s,v+y,h):m.append(v+4|(v+g)<<7|2<<21)
 return m
C={0:2,7:1,112:8,119:4,4:3,116:12}
def ai(s,m):
 o=m&127;i=m>>7&127;j=m>>14&7;c=m>>17&15;f=m>>21&3;b=s.b;w=s.s;p=b[o];u=s.c,s.e,s.k[0],s.k[1],s.s;s.c&=~C.get(o,0)
 if c:s.c&=~C.get(i,0)
 s.e=-1;b[o]=0
 if f==1:b[i-16+32*w]=0
 if f==2:
  x,y={6:(7,5),2:(0,3),118:(119,117)}.get(i,(112,115));b[y],b[x]=b[x],0
 if f==3:p=w<<3|j
 elif p&7==P and abs(i-o)==32:s.e=(o+i)//2
 b[i]=p
 if p&7==K:s.k[w]=i
 s.s^=1;return u
def ak(s,m,u):
 o=m&127;i=m>>7&127;j=m>>14&7;c=m>>17&15;f=m>>21&3;b=s.b;w=s.s^1;p=b[i]
 if f==3:p=w<<3|P
 b[o]=p;b[i]=c if f!=1 else 0
 if f==1:b[i-16+32*w]=c
 if f==2:
  x,y={6:(7,5),2:(0,3),118:(119,117)}.get(i,(112,115));b[x],b[y]=b[y],0
 s.c,s.e,s.k[0],s.k[1],s.s=u
def lm(s):
 w=s.s;r=[]
 for m in gp(s):
  u=ai(s,m)
  if not ic(s,w):r.append(m)
  ak(s,m,u)
 return r
def mu(m):return a(m&127)+a(m>>7&127)+('  nbrq'[m>>14&7]if m>>14&7 else'')
def ms(s,m):
 p=s.b[m&127];c=m>>17&15;t=m>>14&7
 return 100*V[t]+10*V[c&7]-V[p&7]
ND=NL=0
def ev(s):return sum((1-2*(p>>3))*V[p&7]for p in s.b if p)*(1-2*s.s)
def sr(s,f,r):
 global ND
 m=[i for i in lm(s)if not f or mu(i)in f];ND=0
 def score(m):
  global ND
  ND+=1;u=ai(s,m);v=-ev(s);ak(s,m,u);return v
 return max(m,key=score)if m else None
def po(p,b):
 with L.urlopen(L.Request(U+p,json.dumps(b).encode(),{'content-type':'application/json'}))as r:return json.load(r)
def cm(g):
 a=g.get('legal_moves')or[]
 if not a:return'0000'
 m=sr(pf(g['fen']),set(a),{})
 return mu(m)if m is not None else a[0]
def ah():
 while 1:
  g=po('/game',{})
  if g.get('status')=='done':break
  while g.get('status')=='your_move':g=po('/move',{'game':g['game'],'move':cm(g)})
if __name__=='__main__':ah()
