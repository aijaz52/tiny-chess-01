import json as F,os,urllib.request as L;e=range;U=os.environ['MAKEFUN_ENV_URL'];W=0;P,N,A,R,Q,K=e(1,7);V=[0,100,320,330,500,900,20000];B=[Q,R,A,N];I=32000;M=30000
D={N:[33,31,18,14,-14,-18,-31,-33],A:[17,15,-15,-17],R:[16,-16,1,-1]};D[Q]=D[K]=D[A]+D[R];Z=range(128);_=None
PT=[x-74 for x in b"JJJJJJJJ\xac\xd0\x87\xa9\x8e\xc8l?DQdi\x8b\x82c6<WP_aV[3/HEV[PT10FF@MMk>'I63;bp4JJJJJJJJJJJJJJJJ\xfc\xf7\xe8\xd0\xdd\xce\xef\x05\xa8\xae\x9f\x8d\x82\x7f\x9c\x9ejbWOHN[[WSGCCBMINQDKJEIBWRRTWJLCJJJJJJJJ\xa3\xf1(\x19\x87\xe9;\xdf\x01!\x92na\x88Q9\x1b\x86o\x8b\x9e\xcb\x93vA[]\x7fo\x8f\\`=NZWf]_B3AVT][c:-\x15>GI\\<7\xe15\x10)9.73\x10$=.+/\x0b\xe71B1HA12\x1626TSIA7!9M```UR88DZcZ[N83GIYTG64 6@EH63\x1e-\x173;48\x18\n-N\xf8%1 QB0Z8=h\x85\\\x1b:ourm|oHFO]|ooQHDWWdlVTNJYYYXe\\TNYZJQ_kK)G<5=>#5<5?BCA92BFQ>G=F<LBJIHPJNGSVSXTMLDMW]QTGA>GRTWMC;<8CINA;/3A3EA:E9jtj}\x89Siuej\x84\x88\x9a\x8ddvE]dn[w\x87Z2?QdbmB6&0>ISCP3\x1d1:9MJE)\x1e:6AIUD\x037=K[ZQ%0WT\\YVVROUWWUGMRMQQQONGEGNMWKLKILMORNEDB?FJEIC>B:DDJLAA?GALMIE=N6.JgV\x85vuw2#EK:\x83f\x80=9QRg\x82y\x83//::I[HKA0A@HFMG<L?HELXO'BULRYGKI8AT;1+\x18A``ee]T^9^js\x84chJ6PS{ym]SM`bw\x83r\x83n8f]yilqa:/YPS[TO43,::3&*).4\x1fE*6!\taZ;\x12(LWgI6CBF$-AbL:6P`496>/,1<&\x19I/#\x1c\x1e)\x17<<4\x1c\x1e,;/KQB\n\x1f:SR;nV\x14R.bX\x00'88?YN9>[X[[paUT[aY^wvWB`bedkdM8F_beaS?7GU_aZQA/?NWXNE9\x15(5?.<2\x1f"]
PT[79]+=256
for i in(128,129,133,135,184,199,258):PT[i]-=256
PT=[PT[i:i+64]for i in e(0,768,64)];Y=[0,0,1,1,2,4,0];v,H=([[0]*128 for _ in e(16)]for _ in e(2))
for p in e(1,15):
 c=p>>3;t=p&7
 if t in(0,7):continue
 g=1-2*c
 for z in Z:i=(7-(z>>4)if c==W else z>>4)*8+(z&7);v[p][z]=g*([82,337,365,477,1025,0][t-1]+PT[2*t-2][i]);H[p][z]=g*([94,281,297,512,936,0][t-1]+PT[2*t-1][i])
def a(s):return'abcdefgh'[s&7]+str(1+(s>>4))
def j(s):return int(s[1])*16+ord(s[0])-113
class S:
 __slots__=[*'bscekh']
 def __init__(A):A.b=[0]*128;A.s=W;A.c=A.h=0;A.e=-1;A.k=[-1,-1]
def pf(f):
 s=S();a=f.split();z=a[0].split('/')
 for r in e(8):
  x=0
  for h in z[r]:
   if h.isdigit():x+=int(h)
   else:
    c=not h.isupper();t=' pnbrqk'.index(h.lower());v=(7-r)*16+x;s.b[v]=c<<3|t
    if t==K:s.k[c]=v
    x+=1
 s.s=a[1]!='w'
 for b in a[2]if a[2:]else'':s.c|={'K':1,'Q':2,'k':4,'q':8}.get(b,0)
 if a[3:]and a[3]!='-':s.e=j(a[3])
 s.h=hash((tuple(s.b),s.s,s.c,s.e));return s
def ia(s,C,c):
 b=s.b
 for d in(-15,-17)if c==W else(15,17):
  t=C+d
  if not t&136 and b[t]==c<<3|P:return 1
 for J in N,K:
  for d in D[J]:
   t=C+d
   if not t&136:
    p=b[t]
    if p&7==J and p>>3==c:return 1
 for J in A,R:
  for d in D[J]:
   t=C+d
   while not t&136:
    p=b[t]
    if p:
     if p&7 in(J,Q)and p>>3==c:return 1
     break
    t+=d
 return 0
def ic(s,c):return 0 if s.k[c]<0 else ia(s,s.k[c],c^1)
def gp(s):
 m=[];b=s.b;w=s.s;h=w^1
 for C in Z:
  p=b[C]
  if not p or p>>3!=w:continue
  J=p&7
  if J==P:
   c=16-32*w;j=7-7*w;a=C+c
   if not a&136 and not b[a]:
    if a>>4==j:
     for x in B:m.append(C|a<<7|x<<14|3<<21)
    else:
     m.append(C|a<<7)
     if C>>4==1+5*w:
      i=C+c*2
      if not i&136 and not b[i]:m.append(C|i<<7)
   for d in c-1,c+1:
    t=C+d
    if t&136:continue
    X=b[t]
    if X and X>>3==h:
     if t>>4==j:
      for x in B:m.append(C|t<<7|x<<14|X<<17|3<<21)
     else:m.append(C|t<<7|X<<17)
    elif t==s.e:m.append(C|t<<7|b[t-c]<<17|1<<21)
  elif J in(N,K):
   for d in D[J]:
    t=C+d
    if t&136:continue
    X=b[t]
    if X and X>>3==w:continue
    m.append(C|t<<7|X<<17)
   if J==K:
    v=112*w
    for f,g,x,y,z in(1,6,5,6,0),(2,2,3,2,1):
     if s.c&f<<2*w and not b[v+x]and not b[v+y]and(not z or not b[v+z])and not ia(s,v+4,h)and not ia(s,v+x,h)and not ia(s,v+y,h):m.append(v+4|v+g<<7|2<<21)
  else:
   for d in D[J]:
    t=C+d
    while not t&136:
     X=b[t]
     if X:
      if X>>3!=w:m.append(C|t<<7|X<<17)
      break
     m.append(C|t<<7);t+=d
 return m
C={0:2,7:1,112:8,119:4,4:3,116:12}
def ai(s,k):
 O=k&127;i=k>>7&127;j=k>>17&15;Y=k>>21&3;b=s.b;w=s.s;p=b[O];J=p&7;u=s.c,s.e,s.k[w],s.k[w^1],s.h;c=s.c&~C.get(O,0)
 if j:c&=~C.get(i,0)
 s.c=c;s.e=-1;b[O]=0
 if Y==1:b[i-16+32*w]=0
 elif Y==2:a,d={6:(7,5),2:(0,3),118:(119,117)}.get(i,(112,115));b[d],b[a]=b[a],0
 elif Y==3:p=w<<3|k>>14&7
 elif J==P and abs(i-O)==32:s.e=(O+i)//2
 b[i]=p
 if J==K:s.k[w]=i
 s.s=w^1;s.h=hash((tuple(b),s.s,s.c,s.e));return u
def ak(s,a,u):
 O=a&127;i=a>>7&127;j=a>>17&15;Y=a>>21&3;b=s.b;w=s.s^1;s.s=w;s.c,s.e,s.k[w],s.k[w^1],s.h=u;p=b[i]
 if Y==3:p=w<<3|P
 b[O]=p;b[i]=0
 if Y==1:b[i-16+32*w]=j
 elif Y==2:a,d={6:(7,5),2:(0,3),118:(119,117)}.get(i,(112,115));b[a],b[d]=b[d],0
 elif j:b[i]=j
def lm(s):
 w=s.s;r=[]
 for m in gp(s):
  u=ai(s,m)
  if not ic(s,w):r.append(m)
  ak(s,m,u)
 return r
def mu(m):return a(m&127)+a(m>>7&127)+('  nbrq'[m>>14&7]if m>>14&7 else'')
def ev(s):
 a=b=t=0
 for z in Z:p=s.b[z];a+=v[p][z];b+=H[p][z];t+=Y[p&7]
 t=min(t,24);return(a*t+b*(24-t))*(1-2*s.s)//24
E={};G={};ND=T=0;NL=30000;o={};q=[];y={}
def O(e,d,b,z=-1):return sorted(e,key=lambda m:(m!=d,-V[m>>17&7]*10+V[b[m&127]&7]*(m>>17&7>0)-100*(m>>14&7==Q),not(not m>>14 and m in y.get(z,())),-G.get(m,0),m))
def x(s,a,b,Z):
 global ND,T;ND+=1
 if ND>=NL:T=1;return ev(s)
 w=s.s;h=ic(s,w)
 if not h:
  d=ev(s)
  if d>=b:return b
  if d>a:a=d
  if Z>=24:return a
 n=0
 for m in O([m for m in gp(s)if h or m>>17&15 or m>>21&3 in(1,3)],_,s.b):
  if not h and m>>21&3!=3 and d+V[m>>17&7]+180<a:continue
  u=ai(s,m)
  if ic(s,w):ak(s,m,u);continue
  n+=1;v=-ev(s)if Z>=24 else-x(s,-b,-a,Z+1);ak(s,m,u)
  if T:return a
  if v>=b:return b
  if v>a:a=v
 if h and not n:return-M+Z
 return a
def X(s,d,a,b,Z,J=1):
 global ND,T
 if T:return 0,_
 ND+=1
 if ND>=NL:T=1;return ev(s),_
 a=max(a,Z-M);b=min(b,M-Z-1)
 if a>=b:return a,_
 l=s.h
 if J and o.get(l,0)+q.count(l)>1:return(-25 if ev(s)>50 else 0),_
 w=s.s;H=ic(s,w);d+=H and d>0 and Z<16
 if Z>=64:return ev(s),_
 if d<=0:return x(s,a,b,Z),_
 r=a;h=_;e=J and E.get(l)
 if e:
  p,g,f,h=e
  if abs(g)>29000:g-=Z if g>0 else-Z
  if p>=d and(f==0 or f==1 and g<=a or f==2 and g>=b):return g,h
 t=O(gp(s),h,s.b,Z);i=n=0;c=-I;F=Z and d<3 and not H and ev(s)+120*d<a
 if J and not H and d>=3 and any(1<s.b[m&127]&7<K for m in t):
  u=s.s,s.e;s.s^=1;s.e=-1;v=-X(s,d-2-(d>8),-b,-a,Z+1,0)[0];s.s,s.e=u
  if T:return 0,_
  if v>=b:return b,_
 for m in t:
  u=ai(s,m)
  if ic(s,w):ak(s,m,u);continue
  C=not(m>>14 or ic(s,s.s))
  if F and n and C:ak(s,m,u);continue
  n+=1
  if J:q.append(l)
  if n>1:v=-X(s,d-1-(1+(n>12))*(Z>0 and d>2 and n>3 and not H and C),-a-1,-a,Z+1,J)[0]
  if n==1 or v>a:v=-X(s,d-1,-b,-a,Z+1,J)[0]
  if J:q.pop()
  ak(s,m,u)
  if T:break
  if v>c:c,i=v,m
  if v>a:a=v
  if a>=b:
   if not m>>17 and m>>21&3==0:G[m]=G.get(m,0)+d*d;y[Z]=([m]+[k for k in y.get(Z,())if k!=m])[:2]
   break
 if T:return c,i
 if not n:return H*(Z-M),_
 f=1 if c<=r else 2 if c>=b else 0
 if J:E[l]=d,c+(Z if c>29000 else-Z if c<-29000 else 0),f,i
 return c,i
def sr(s,f,r):
 global ND,T,o,q;E.clear();G.clear();y.clear();ND=T=0;o=r or{};q=[];l=lm(s)
 if not l:return
 c=[m for m in l if mu(m)in f]or l;k=s.h;h=c[0];z={};r=0
 for d in e(1,64):
  p=O(c,h if d>1 else _,s.b);p.sort(key=lambda m:(m==h,z.get(m,-I)),reverse=1)
  for w in(40,I)if d>2 else(I,):
   a,b=(r-w,r+w)if w<I else(-I,I);L=a;i=-I;j=c[0];z={}
   for m in p:
    u=ai(s,m);q.append(k);v=-X(s,d-1,-b,-a,1)[0];q.pop();ak(s,m,u)
    if T:break
    z[m]=v
    if v>i:i,j=v,m
    if v>a:a=v
    if a>=b:break
   if T or L<i<b:break
  if T:break
  h,r=j,i
  if r>=29000:break
 return h
def cr(m,x=_):
 s=pf('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1');c={s.h:1}
 for u in m if x is _ else m[:x]:
  v=next((m for m in lm(s)if mu(m)==u),_)
  if v is _:break
  ai(s,v);c[s.h]=c.get(s.h,0)+1
 return c,s
def po(p,b):
 with L.urlopen(L.Request(U+p,F.dumps(b).encode(),{'content-type':'application/json'}))as a:return F.load(a)
def cm(g):
 s=pf(g['fen']);a=g.get('legal_moves')or[];e,j=cr(g.get('moves')or[]);d=sr(s,set(a),e)
 if d is _:return a[0]if a else'0000'
 return mu(d)
def ah():
 while 1:
  g=po('/game',{})
  if g.get('status')=='done':break
  while g.get('status')=='your_move':m=cm(g);g=po('/move',{'game':g['game'],'move':m})
if __name__=='__main__':ah()
