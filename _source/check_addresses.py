"""Check that every Frostline address answers the way it should since the 2026-09-28 swap
(this site on frostlinenorge.no, the store on skole.frostlinenorge.no), old links included.

  python3 _source/check_addresses.py            # the finished state
  python3 _source/check_addresses.py --store    # halfway: the store moved, this site not yet

Every request resolves through Google's DNS over HTTPS (curl --doh-url), because the network
this Mac is often on answers port 53 from its own cache. One line per check, then a count;
exits 1 if any failed.
"""
import re, subprocess, sys, tempfile, urllib.parse

DOH = 'https://dns.google/dns-query'
STORE_STAGE = '--store' in sys.argv
APEX, SKOLE, OLD = 'https://frostlinenorge.no', 'https://skole.frostlinenorge.no', 'https://russ.frostlinenorge.no'


def get(url):
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run(['curl', '-s', '--max-time', '25', '--doh-url', DOH, '-H', 'Cache-Control: no-cache',
                            '-D', f'{d}/h', '-o', f'{d}/b', url], capture_output=True, text=True)
        if r.returncode:
            return {'status': 0, 'err': f'curl exit {r.returncode}', 'h': {}, 'body': ''}
        # the last response's headers (a 103 Early Hints from Shopify comes first)
        heads = re.split(r'\n\s*\n', open(f'{d}/h', errors='replace').read())
        last = [x for x in heads if x.startswith('HTTP/')][-1].splitlines()
        h = {k.lower(): v.strip() for k, v in (line.split(':', 1) for line in last[1:] if ':' in line)}
        return {'status': int(last[0].split()[1]), 'h': h, 'body': open(f'{d}/b', errors='replace').read()}


def refresh(body):
    m = re.search(r'http-equiv="refresh" content="0; url=([^"]+)"', body)
    return m.group(1) if m else None


fails = 0


def check(url, what, ok, got):
    global fails
    fails += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {url:62} {what}" + ('' if ok else f'   (got: {got})'))


def redirect(url, to, code=301):
    """A redirect to `to` (a relative Location counts as the absolute address it means)."""
    r = get(url)
    loc = urllib.parse.urljoin(url, r['h'].get('location', '')) if r['h'].get('location') else ''
    to = urllib.parse.urljoin(url, to)
    check(url, f'{code} to {to}', r['status'] == code and loc == to, f"{r['status']} {loc or r.get('err', '')}")


def page(url, server, text=None):
    r = get(url)
    srv = r['h'].get('server', '')
    good = r['status'] == 200 and server.lower() in srv.lower() and (text is None or text in r['body'])
    check(url, f'200 from {server}' + (f', has "{text}"' if text else ''), good, f"{r['status']} {srv} {r.get('err', '')}")


def forwards(url, to, status=200):
    """A page that sends you on: with a 0-second refresh (status 200) or by script (a 404 page)."""
    r = get(url)
    if status == 200:
        good, got = r['status'] == 200 and refresh(r['body']) == to, f"{r['status']} refresh {refresh(r['body'])}"
    else:
        good, got = r['status'] == 404 and to in r['body'], f"{r['status']}"
    check(url, f"{status}, forwards to {to}", good, got)


def image(url):
    r = get(url)
    check(url, '200 image/png', r['status'] == 200 and r['h'].get('content-type', '').startswith('image/png'),
          f"{r['status']} {r['h'].get('content-type', '')}")


# the store, wherever the rest stands
page(f'{SKOLE}/', 'cloudflare', 'Frostline')
redirect(f'{SKOLE}/lorenskog', '/?skole=lorenskog')
redirect(f'{SKOLE}/l%C3%B8renskog', '/?skole=lorenskog')
redirect(f'{SKOLE}/demo', '/?skole=demo')
redirect('https://mgnmt8-ih.myshopify.com/', f'{SKOLE}/')
page('https://webmail.frostlinenorge.no/', '', None)

if STORE_STAGE:
    # the store is primary on skole: its old domain and www send everything there, path and all
    redirect(f'{APEX}/', f'{SKOLE}/')
    redirect('https://www.frostlinenorge.no/', f'{SKOLE}/')
    redirect(f'{APEX}/lorenskog', f'{SKOLE}/?skole=lorenskog')
    redirect(f'{APEX}/demo', f'{SKOLE}/?skole=demo')
    redirect(f'{APEX}/cart?x=1', f'{SKOLE}/cart?x=1')
    page(f'{OLD}/', 'GitHub', 'Frostline')
else:
    page(f'{APEX}/', 'GitHub', 'Frostline')
    page(f'{APEX}/hoodie', 'GitHub', 'Hoodie | Frostline')
    page(f'{APEX}/storrelser', 'GitHub', 'Størrelser | Frostline')
    redirect('http://frostlinenorge.no/', f'{APEX}/')
    redirect('http://www.frostlinenorge.no/', f'{APEX}/')
    redirect('https://www.frostlinenorge.no/', f'{APEX}/')
    forwards(f'{APEX}/lorenskog', f'{SKOLE}/lorenskog')
    forwards(f'{APEX}/l%C3%B8renskog', f'{SKOLE}/l%C3%B8renskog')
    forwards(f'{APEX}/demo', f'{SKOLE}/demo')
    forwards(f'{APEX}/products/lorenskog-bukse', SKOLE, 404)
    forwards(f'{APEX}/Hoodie', '"hoodie"', 404)
    for f in ('frostline-logo.png', 'frostline-logo-email.png', 'frostline-logo-navy-email.png',
              'frostline-logo-white-outline.png', 'frostline-logo-white.png'):
        image(f'{APEX}/cdn/shop/t/2/assets/{f}')
    forwards(f'{OLD}/', f'{APEX}/')
    forwards(f'{OLD}/hoodie', f'{APEX}/hoodie')
    forwards(f'{OLD}/zip-hoodie', f'{APEX}/zip-hoodie')
    forwards(f'{OLD}/img/anything.webp', APEX, 404)
    redirect('http://russ.frostlinenorge.no/', f'{OLD}/')

print(f"\n{'all good' if not fails else f'{fails} failed'}")
sys.exit(1 if fails else 0)
