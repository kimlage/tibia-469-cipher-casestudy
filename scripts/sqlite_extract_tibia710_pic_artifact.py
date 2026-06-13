#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
PIC_DIR=Path('./tmp/tibia_clients/tibia710/tibia')
OUT_DIR=Path('./tmp/tibia_clients/extracted')
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT): subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def create(cur):
    cur.executescript('''
    create table if not exists tibia_pic_artifact_runs(run_id integer primary key autoincrement,created_at text not null,client_version text not null,artifact_count integer not null,decision text not null,next_action text not null,payload_json text not null);
    create table if not exists tibia_pic_artifact_items(run_id integer not null,file_name text not null,path text not null,width integer not null,height integer not null,pixel_count integer not null,file_size integer not null,format_status text not null,output_png text,evidence_json text not null,primary key(run_id,file_name));''')
def parse_pic(path:Path):
    data=path.read_bytes(); w=int.from_bytes(data[:2],'little'); h=int.from_bytes(data[2:4],'little'); pix=data[4:]
    status='PIC_RAW_8BIT_HEADER_MATCH' if len(pix)==w*h else 'PIC_SIZE_MISMATCH'
    return w,h,pix,status,len(data)
def write_png(path:Path,w:int,h:int,pix:bytes,out:Path):
    try:
        from PIL import Image
        im=Image.frombytes('L',(w,h),pix)
        # Invert-ish stretch for visual font contrast if needed, preserve raw grayscale.
        im.save(out)
        return str(out)
    except Exception:
        return None
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); cur=con.cursor(); create(cur); OUT_DIR.mkdir(parents=True,exist_ok=True)
    items=[]
    for p in sorted(PIC_DIR.glob('*.pic')):
        w,h,pix,status,size=parse_pic(p); out=OUT_DIR/(p.stem+'.png'); png=write_png(p,w,h,pix,out) if status=='PIC_RAW_8BIT_HEADER_MATCH' else None
        items.append({'file_name':p.name,'path':str(p),'width':w,'height':h,'pixel_count':len(pix),'file_size':size,'format_status':status,'output_png':png})
    decision='TIBIA710_PIC_ARTIFACTS_EXTRACTED' if items and all(i['format_status']=='PIC_RAW_8BIT_HEADER_MATCH' for i in items) else 'TIBIA710_PIC_ARTIFACT_PARSE_PARTIAL'
    next_action='derive authentic font glyph order from font.pic/tibia.pic and rerun charset base tests' if decision.endswith('EXTRACTED') else 'inspect mismatched pic files'
    cur.execute('insert into tibia_pic_artifact_runs(created_at,client_version,artifact_count,decision,next_action,payload_json) values (?,?,?,?,?,?)',(now(),'7.10-linux',len(items),decision,next_action,j({'items':items})))
    run_id=cur.lastrowid
    for i in items:
        cur.execute('insert into tibia_pic_artifact_items(run_id,file_name,path,width,height,pixel_count,file_size,format_status,output_png,evidence_json) values (?,?,?,?,?,?,?,?,?,?)',(run_id,i['file_name'],i['path'],i['width'],i['height'],i['pixel_count'],i['file_size'],i['format_status'],i['output_png'],j(i)))
    con.commit(); print(json.dumps({'run_id':run_id,'decision':decision,'items':items},ensure_ascii=False))
    if args.discord: send('\n'.join([f'[469][tibia-pic-artifact][run={run_id}] cliente Tibia 7.10 Linux extraído',f'artifacts={len(items)} | decisão={decision}','font.pic/tibia.pic/status/etc viraram PNGs auditáveis em tmp/tibia_clients/extracted','próxima ação: usar charset real CP1252/font-order para teste base-N, sem promoção.']))
if __name__=='__main__': main()
