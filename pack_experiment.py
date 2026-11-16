#!/usr/bin/env python3
"""Compare whole-source table encodings; optionally measure with makefun."""
import argparse
import ast
import json
import lzma
import os
from pathlib import Path
import subprocess
import tempfile
import random
import base64

HEAD = b"#coding:l1\nimport lzma;exec(lzma.decompress('"
TAIL = b"'.encode('l1')))\n"


def packed(payload):
    out = bytearray(HEAD)
    for i, b in enumerate(payload):
        if b == 0:
            out.extend(b'\\x00' if i + 1 < len(payload) and 48 <= payload[i+1] <= 57 else b'\\0')
        elif b in (10, 13, 39, 92):
            out.extend({10: b'\\n', 13: b'\\r', 39: b"\\'", 92: b'\\\\'}[b])
        else:
            out.append(b)
    return bytes(out) + TAIL


def load(source):
    scope = {'__name__': 'experiment'}
    exec(compile(source, '<candidate>', 'exec'), scope)
    return scope


def previous():
    try:
        return subprocess.check_output(['git', 'show', 'HEAD~1:engine.py'], stderr=subprocess.DEVNULL).decode()
    except subprocess.CalledProcessError:
        tree = ast.parse(subprocess.check_output(['git', 'show', 'HEAD~1:main.py']))
        literal = tree.body[1].value.args[0].args[0].func.value.value
        return lzma.decompress(literal.encode('latin1')).decode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('engine.py'))
    parser.add_argument('--out', type=Path, default=Path('/tmp/pack-candidates'))
    parser.add_argument('--real', type=int, default=8, help='measure this many XZ finalists plus baselines with makefun')
    parser.add_argument('--apply', action='store_true', help='apply the best real-compressor candidate to the source')
    args = parser.parse_args()
    os.environ.setdefault('MAKEFUN_ENV_URL', 'http://experiment.invalid')
    source = args.source.read_text()
    helpers = [line for line in source.splitlines(True) if line.startswith(('def ta(', 'def fa('))]
    source = ''.join(line for line in source.splitlines(True) if line not in helpers)
    at = source.index('D={')
    source = source[:at] + ''.join(helpers) + source[at:]
    baseline = load(source)
    tables = baseline['PT']
    flat = sum(tables, [])
    start = source.index('\n', source.index('SQ=')) + 1
    end = source.index('PW=')
    variants = {'baseline': source, 'previous': previous()}
    encodings = {
        'decimal-lists': 'PT=' + repr(tables).replace(' ', '') + '\n',
        'decimal-flat': 'PT=' + repr(flat).replace(' ', '') + '\nPT=[PT[i:i+64]for i in range(0,768,64)]\n',
        'comma-string': "PT=list(map(int,'" + ','.join(map(str, flat)) + "'.split(',')))\nPT=[PT[i:i+64]for i in range(0,768,64)]\n",
        'space-string': "PT=list(map(int,'" + ' '.join(map(str, flat)) + "'.split()))\nPT=[PT[i:i+64]for i in range(0,768,64)]\n",
        'table-strings': "PT=[list(map(int,a.split(',')))for a in'" + ' '.join(','.join(map(str, t)) for t in tables) + "'.split()]\n",
    }
    for shift in (0, 68, 128):
        values=bytes((v+shift)%256 for v in flat)
        restore=f'PT=[(v-{shift}+128)%256-128 for v in PT]\n'
        # PeSTO has a few entries outside signed-byte range: retain them exactly.
        fix=''.join(f'PT[{i}]={v}\n' for i,v in enumerate(flat) if not -128<=v<128)
        for kind in ('b64','b85','hex','literal'):
            if kind == 'hex':
                encoding=f'PT=bytes.fromhex({values.hex()!r})\n'
            elif kind == 'literal':
                encoding=f'PT={values!r}\n'
            else:
                encode=base64.b64encode if kind=='b64' else base64.b85encode
                encoding=f'import base64 as Z\nPT=Z.{kind}decode({encode(values).decode()!r})\n'
            encodings[f'bytes-{shift}-{kind}']=encoding+restore+fix+'PT=[PT[i:i+64]for i in range(0,768,64)]\n'
    for radix in (8, 16, 32, 64):
        for shift in (68, 128, 180):
            values=[v+shift for v in flat]
            if min(values)<0:continue
            alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#'
            chars=''.join(alphabet[v//radix]+alphabet[v%radix] for v in values)
            encoding=f"PT=[{alphabet!r}.index(c)for c in{chars!r}]\nPT=[PT[i]*{radix}+PT[i+1]-{shift} for i in range(0,1536,2)]\nPT=[PT[i:i+64]for i in range(0,768,64)]\n"
            encodings[f'radix-{radix}-{shift}']=encoding
    # Offset character encodings exploit repeated table values without base85.
    for offset in (68, 128, 160, 256, 400):
        if min(flat)+offset >= 0:
            chars = ''.join(chr(x+offset) for x in flat)
            encodings[f'chars-{offset}'] = f'PT=[ord(c)-{offset} for c in{chars!r}]\nPT=[PT[i:i+64]for i in range(0,768,64)]\n'
    for order in ('normal', 'transpose'):
        values = flat if order == 'normal' else [tables[t][i] for i in range(64) for t in range(12)]
        restore = 'PT=[PT[i:i+64]for i in range(0,768,64)]\n' if order == 'normal' else 'PT=[PT[i::12]for i in range(12)]\n'
        for delta in (False, True):
            encoded = [v-(values[i-1] if i else 0) for i,v in enumerate(values)] if delta else values
            for offset in (256, 300, 350, 400, 450, 500, 600):
                if min(encoded)+offset < 0:
                    continue
                chars = ''.join(chr(v+offset) for v in encoded)
                if delta:
                    encoding = f"PT=[];a=0\nfor c in{chars!r}:a+=ord(c)-{offset};PT.append(a)\n"
                else:
                    encoding = f'PT=[ord(c)-{offset} for c in{chars!r}]\n'
                encodings[f'{order}-delta{int(delta)}-{offset}'] = encoding+restore
    for name, encoding in encodings.items():
        text = source[:start] + encoding + source[end:]
        variants[name] = text
        # Cluster utility functions and the table setup separately.
        lines = text.splitlines(True)
        variants[name+'-cluster'] = ''.join([lines[0], lines[3], *lines[4:]])
        at = variants[name+'-cluster'].index('class S:')
        variants[name+'-cluster'] = variants[name+'-cluster'][:at] + ''.join(lines[1:3]) + variants[name+'-cluster'][at:]
    for shift in range(68, 151):
        values=bytes((v+shift)%256 for v in flat)
        correction={}
        for i,v in enumerate(flat):
            difference=v-(values[i]-shift)
            if difference:correction.setdefault(difference,[]).append(i)
        fix=''.join(f'for i in{tuple(indices)!r}:PT[i]+={difference}\n' for difference,indices in correction.items())
        encoding=f'PT=[x-{shift} for x in {values!r}]\n'+fix+'PT=[PT[i:i+64]for i in range(0,768,64)]\n'
        text=source[:start]+encoding+source[end:]
        variants[f'byte-offset-{shift}']=text
        lines=text.splitlines(True)
        variants[f'byte-offset-{shift}-cluster']=''.join([lines[0],lines[3],*lines[4:]])
        at=variants[f'byte-offset-{shift}-cluster'].index('class S:')
        s=variants[f'byte-offset-{shift}-cluster']
        variants[f'byte-offset-{shift}-cluster']=s[:at]+''.join(lines[1:3])+s[at:]
    rewrites = [
        ('MG=[[0]*128 for _ in range(16)];EG=[[0]*128 for _ in range(16)]', 'MG,EG=([[0]*128 for _ in range(16)]for _ in range(2))'),
        ('a,d={6:(7,5),2:(0,3),118:(119,117)}.get(i,(112,115))', 'a,d=CD.get(i,(112,115))'),
        ('g=1 if c==W else-1', 'g=1-2*c'),
        ('O=a&127;i=a>>7&127;j=a>>17&15;Y=a>>21&3', 'O=a&127;i=a>>7&127;o=a>>14&7;j=a>>17&15;Y=a>>21&3'),
        ('r=a;h=None;k=l;e=TT.get(k)', 'r=a;k=l;e=TT.get(k);h=None'),
        ('a=b=t=0', 'a=0;b=0;t=0'),
    ]
    for seed in ('normal-delta0-300-cluster', 'normal-delta0-600-cluster'):
        for mask in range(1, 64):
            text = variants[seed]
            for bit, (old,new) in enumerate(rewrites):
                if mask & (1<<bit):
                    text=text.replace(old,new)
                    if bit == 1:
                        text=text.replace('C0={', 'CD={6:(7,5),2:(0,3),118:(119,117)}\nC0={').replace('c,e={6:(7,5),2:(0,3),118:(119,117)}.get(i,(112,115))','c,e=CD.get(i,(112,115))')
            variants[f'{seed}-code-{mask}']=text
    loop_old = 'for z in SQ:i=((7-(z>>4)if c==W else z>>4)*8)+(z&7);MG[p][z]=g*([82,337,365,477,1025,0][t-1]+PT[2*t-2][i]);EG[p][z]=g*([94,281,297,512,936,0][t-1]+PT[2*t-1][i])'
    loop_new = 'for E,v,j in(MG,[82,337,365,477,1025,0],0),(EG,[94,281,297,512,936,0],1):\n  for z in SQ:i=((7-(z>>4)if c==W else z>>4)*8)+(z&7);E[p][z]=g*(v[t-1]+PT[2*t-2+j][i])'
    for offset in range(180, 1001, 10):
        chars = ''.join(chr(v+offset) for v in flat)
        encoding = f'PT=[ord(c)-{offset} for c in{chars!r}]\nPT=[PT[i:i+64]for i in range(0,768,64)]\n'
        text=source[:start]+encoding+source[end:]
        for loop in (False, True):
            candidate=text.replace(loop_old,loop_new) if loop else text
            variants[f'offset-{offset}-loop-{int(loop)}']=candidate
    # Definitions only resolve their global references when called, so their
    # order can change while all initialization statements stay in place.
    seed_source = variants['chars-400']
    tree = ast.parse(seed_source)
    lines = seed_source.splitlines(True)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    slots = [(n.lineno-1, n.end_lineno) for n in functions]
    blocks = [''.join(lines[a:b]) for a,b in slots]
    rng = random.Random(4096)
    for i in range(80):
        order = list(range(len(blocks)))
        if i == 0:
            order.sort(key=lambda k: functions[k].name)
        elif i == 1:
            order.reverse()
        else:
            rng.shuffle(order)
        output = []; last = 0
        for (a,b), k in zip(slots, order):
            output.extend(lines[last:a]); output.append(blocks[k]); last=b
        output.extend(lines[last:])
        variants[f'function-order-{i}'] = ''.join(output)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'original.py').write_text(source)
    rows = []
    for name, text in variants.items():
        candidate = load(text)
        assert candidate['PT'] == tables, name
        assert candidate['MG'] == baseline['MG'] and candidate['EG'] == baseline['EG'], name
        assert candidate['NL'] == 150000, name
        data = text.encode()
        payload = lzma.compress(data, format=lzma.FORMAT_XZ, preset=9)
        path = args.out / (name+'.py')
        path.write_text(text)
        rows.append({'name': name, 'raw': len(data), 'xz': len(payload), 'xz_stub': len(packed(payload))})
    rows.sort(key=lambda r: r['xz_stub'])
    finalists = {r['name'] for r in rows[:args.real]} | {'baseline', 'previous'}
    for row in rows:
        if args.real and row['name'] in finalists:
            with tempfile.NamedTemporaryFile(suffix='.py', prefix='.pack-', dir=args.source.resolve().parent) as temp, tempfile.NamedTemporaryFile(suffix='.py', prefix='.packed-', dir=args.source.resolve().parent) as entry:
                temp.write((args.out / (row['name']+'.py')).read_bytes())
                temp.flush()
                subprocess.check_output(['node', '/root/makefun/tiny-chess-01-kit/cli/makefun.mjs', 'compress', temp.name, '--out', entry.name, '--json'])
                (args.out / (row['name']+'-packed.py')).write_bytes(Path(entry.name).read_bytes())
            row['real'] = (args.out / (row['name']+'-packed.py')).stat().st_size
        print(json.dumps(row), flush=True)
    (args.out / 'results.json').write_text(json.dumps(rows, indent=2)+'\n')
    if args.real:
        best = min((r for r in rows if 'real' in r), key=lambda r: r['real'])
        print('BEST:', json.dumps(best))
        if args.apply:
            args.source.write_bytes((args.out / (best['name']+'.py')).read_bytes())


if __name__ == '__main__':
    main()
