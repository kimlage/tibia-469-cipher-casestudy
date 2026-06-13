#!/usr/bin/env python3
import argparse, hashlib, json, os, re, sqlite3, subprocess, tarfile, urllib.parse, urllib.request, datetime as dt
from pathlib import Path
from typing import Any
DB_DEFAULT='./data/bonelord_operational.sqlite'; DISCORD_CHANNEL='0'; DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
BASE='https://clients.tibia.network'
VERSIONS=['713','760']
WORK=Path('./tmp/tibia_clients')
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT): subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def fetch(url,data=None):
    req=urllib.request.Request(url,data=data,headers={'User-Agent':'Mozilla/5.0','Referer':url,'Origin':BASE})
    with urllib.request.urlopen(req,timeout=60) as r: return r.read()
def get_linux_file_id(ver):
    html=fetch(f'{BASE}/download/tibia-{ver}').decode('utf-8','ignore')
    rows=re.findall(r'<tr>(.*?)</tr>',html,re.S)
    for row in rows:
        if 'Linux' in row and '.tgz' in row:
            m=re.search(r'name="file_id" value="(\d+)"',row)
            name=re.search(r'<td>(tibia[^<]+\.tgz)</td>',row)
            if m: return m.group(1), name.group(1) if name else f'tibia{ver}.tgz'
    return None,None
def parse_pic(path):
    data=path.read_bytes(); w=int.from_bytes(data[:2],'little'); h=int.from_bytes(data[2:4],'little'); pix=data[4:]; return {'width':w,'height':h,'pixel_count':len(pix),'sha256':hashlib.sha256(data).hexdigest(),'pixel_sha256':hashlib.sha256(pix).hexdigest(),'size':len(data),'status':'OK' if len(pix)==w*h else 'MISMATCH'}
def create(cur):
    cur.executescript('''
    create table if not exists tibia_font_version_compare_runs(run_id integer primary key autoincrement,created_at text not null,version_count integer not null,downloaded_count integer not null,unique_font_hash_count integer not null,decision text not null,next_action text not null,payload_json text not null);
    create table if not exists tibia_font_version_compare_items(run_id integer not null,version text not null,download_status text not null,font_path text,font_sha256 text,font_pixel_sha256 text,width integer,height integer,evidence_json text not null,primary key(run_id,version));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args(); con=sqlite3.connect(args.db); cur=con.cursor(); create(cur); WORK.mkdir(parents=True,exist_ok=True)
    results=[]
    # Include already downloaded 7.10.
    p710=WORK/'tibia710/tibia/font.pic'
    if p710.exists():
        meta=parse_pic(p710); results.append({'version':'710','download_status':'LOCAL_EXISTING','font_path':str(p710),**meta})
    for ver in VERSIONS:
        try:
            fid,name=get_linux_file_id(ver)
            if not fid: raise RuntimeError('no linux tgz file_id')
            tgz=WORK/name
            if not tgz.exists(): tgz.write_bytes(fetch(f'{BASE}/download/tibia-{ver}',urllib.parse.urlencode({'file_id':fid,'download':'Download'}).encode()))
            outdir=WORK/f'tibia{ver}'; outdir.mkdir(exist_ok=True)
            with tarfile.open(tgz,'r:gz') as tf: tf.extractall(outdir)
            fonts=list(outdir.rglob('font.pic'))
            if not fonts: raise RuntimeError('font.pic not found')
            meta=parse_pic(fonts[0]); results.append({'version':ver,'download_status':'DOWNLOADED','font_path':str(fonts[0]),**meta})
        except Exception as e:
            results.append({'version':ver,'download_status':'ERROR:'+str(e),'font_path':None,'sha256':None,'pixel_sha256':None,'width':None,'height':None,'evidence':{}})
    hashes={r.get('pixel_sha256') for r in results if r.get('pixel_sha256')}
    decision='MULTI_VERSION_FONTS_IDENTICAL_OR_COMPARABLE' if len(hashes)<=1 else 'MULTI_VERSION_FONTS_DIFFER_REQUIRE_SEPARATE_SWEEP'
    next_action='if identical, charset route remains rejected for accessible 7.x fonts' if len(hashes)<=1 else 'run visual alphabet sweeps per differing font'
    cur.execute('insert into tibia_font_version_compare_runs(created_at,version_count,downloaded_count,unique_font_hash_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?)',(now(),len(results),sum(1 for r in results if r['download_status'] in ('DOWNLOADED','LOCAL_EXISTING')),len(hashes),decision,next_action,j({'results':results})))
    run_id=cur.lastrowid
    for r in results: cur.execute('insert into tibia_font_version_compare_items(run_id,version,download_status,font_path,font_sha256,font_pixel_sha256,width,height,evidence_json) values (?,?,?,?,?,?,?,?,?)',(run_id,r['version'],r['download_status'],r.get('font_path'),r.get('sha256'),r.get('pixel_sha256'),r.get('width'),r.get('height'),j(r)))
    con.commit(); print(json.dumps({'run_id':run_id,'decision':decision,'results':results},ensure_ascii=False))
    if args.discord: send('\n'.join([f'[469][font-version-compare][run={run_id}] comparação font.pic 7.x',f'versões={len(results)} | baixadas={sum(1 for r in results if r["download_status"] in ("DOWNLOADED","LOCAL_EXISTING"))} | hashes únicos={len(hashes)}',f'decisão={decision}',f'próxima ação: {next_action}']))
if __name__=='__main__': main()
