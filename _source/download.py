"""Read posts/*.json (one per post, as returned by the browser JS), download every image
into raw/<nn>-<k>.jpg and write posts.json with local file names."""
import json, glob, os, subprocess, sys
S = os.path.dirname(os.path.abspath(__file__))
posts = []
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
for f in sorted(glob.glob(os.path.join(S, 'posts', '*.json'))):
    n = os.path.basename(f)[:2]
    d = json.load(open(f))
    code = d['p'].strip('/').split('/')[-1]
    files = []
    for k, im in enumerate(d.get('imgs', []), 1):
        out = os.path.join(S, 'raw', f'{n}-{k}.jpg')
        if not os.path.exists(out) or os.path.getsize(out) < 1000:
            r = subprocess.run(['curl', '-sL', '--max-time', '40', '-A', UA, '-o', out, im['s']])
        ok = os.path.exists(out) and os.path.getsize(out) > 1000
        files.append({'file': os.path.basename(out), 'w': im['w'], 'h': im['h'], 'alt': im.get('alt', ''), 'ok': ok})
        print(n, k, 'OK' if ok else 'FAIL', os.path.getsize(out) if os.path.exists(out) else 0)
    posts.append({'n': n, 'code': code, 'date': d.get('dt', ''), 'caption': d.get('cap', ''), 'video': d.get('vid', 0), 'images': files})
json.dump(posts, open(os.path.join(S, 'posts.json'), 'w'), ensure_ascii=False, indent=1)
print('posts:', len(posts), 'images:', sum(len(p['images']) for p in posts), 'failed:', sum(1 for p in posts for i in p['images'] if not i['ok']))
