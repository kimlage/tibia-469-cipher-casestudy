#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, struct, subprocess
from pathlib import Path
from typing import Any
DB_DEFAULT='./data/bonelord_operational.sqlite'; DISCORD_CHANNEL='0'; DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
PIC=Path('./tmp/tibia_clients/tibia760_inno/app/Tibia.pic'); OUT=Path('./tmp/tibia_clients/tibia760_extracted')
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT): subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def create(cur):
    cur.executescript('''
    create table if not exists tibia760_pic_container_extract_runs(run_id integer primary key autoincrement,created_at text not null,pic_path text not null,version_hex text not null,image_count integer not null,extracted_count integer not null,decision text not null,next_action text not null,payload_json text not null);
    create table if not exists tibia760_pic_container_extract_items(run_id integer not null,image_index integer not null,width integer not null,height integer not null,tiles_x integer not null,tiles_y integer not null,transparent_rgb text not null,output_png text,decode_status text not null,evidence_json text not null,primary key(run_id,image_index));''')
def decode_sprite(data, off, transparent):
    if off<=0 or off+2>len(data): return None,'BAD_OFFSET'
    size=struct.unpack_from('<H',data,off)[0]; pos=off+2; end=pos+size; pixels=[]
    while pos<end and len(pixels)<1024:
        if pos+4>end: return None,'RLE_TRUNC'
        trans,col=struct.unpack_from('<HH',data,pos); pos+=4
        pixels.extend([transparent]*trans)
        need=col*3
        if pos+need>end: return None,'RGB_TRUNC'
        for _ in range(col):
            r,g,b=data[pos],data[pos+1],data[pos+2]; pos+=3; pixels.append((r,g,b,255))
    if len(pixels)<1024: pixels.extend([transparent]*(1024-len(pixels)))
    return pixels[:1024],'OK'
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args(); con=sqlite3.connect(args.db); cur=con.cursor(); create(cur); OUT.mkdir(parents=True,exist_ok=True)
    data=PIC.read_bytes(); version=data[:4].hex(); n=struct.unpack_from('<H',data,4)[0]; pos=6; entries=[]
    for idx in range(n):
        tx,ty=data[pos],data[pos+1]; tr=(data[pos+2],data[pos+3],data[pos+4],0); pos+=5; count=tx*ty; offs=[]
        for _ in range(count): offs.append(struct.unpack_from('<I',data,pos)[0]); pos+=4
        entries.append({'idx':idx,'tx':tx,'ty':ty,'transparent':tr,'offsets':offs})
    items=[]; extracted=0
    try:
        from PIL import Image
    except Exception as e:
        Image=None
    for e in entries:
        w,h=e['tx']*32,e['ty']*32; status='OK'; outpng=None
        if Image:
            img=Image.new('RGBA',(w,h),e['transparent'])
            for ti,off in enumerate(e['offsets']):
                pix,st=decode_sprite(data,off,e['transparent'])
                if st!='OK': status=st; continue
                tile=Image.new('RGBA',(32,32)); tile.putdata(pix)
                x=(ti%e['tx'])*32; y=(ti//e['tx'])*32; img.paste(tile,(x,y))
            out=OUT/f'image_{e["idx"]:02d}_{w}x{h}.png'; img.save(out); outpng=str(out); extracted+=1 if status=='OK' else 0
        items.append({'image_index':e['idx'],'width':w,'height':h,'tiles_x':e['tx'],'tiles_y':e['ty'],'transparent_rgb':e['transparent'][:3],'output_png':outpng,'decode_status':status})
    decision='TIBIA760_PIC_CONTAINER_EXTRACTED' if extracted==n else 'TIBIA760_PIC_CONTAINER_PARTIAL'
    next_action='inspect extracted images for font sheet and compare charset/order' if extracted else 'fix decoder'
    cur.execute('insert into tibia760_pic_container_extract_runs(created_at,pic_path,version_hex,image_count,extracted_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?)',(now(),str(PIC),version,n,extracted,decision,next_action,j({'items':items})))
    run_id=cur.lastrowid
    for i in items: cur.execute('insert into tibia760_pic_container_extract_items(run_id,image_index,width,height,tiles_x,tiles_y,transparent_rgb,output_png,decode_status,evidence_json) values (?,?,?,?,?,?,?,?,?,?)',(run_id,i['image_index'],i['width'],i['height'],i['tiles_x'],i['tiles_y'],j(i['transparent_rgb']),i['output_png'],i['decode_status'],j(i)))
    con.commit(); print(json.dumps({'run_id':run_id,'decision':decision,'version_hex':version,'image_count':n,'extracted_count':extracted,'items':items},ensure_ascii=False))
    if args.discord: send('\n'.join([f'[469][tibia760-pic-extract][run={run_id}] container Tibia.pic 7.60 extraído',f'imagens={n} | extraídas={extracted} | decisão={decision}','próxima ação: localizar font sheet visual e testar charset se diferir do 7.10.']))
if __name__=='__main__': main()
