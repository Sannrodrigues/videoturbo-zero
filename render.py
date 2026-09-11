import json, math, os, re, subprocess
from pathlib import Path


def run(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError(f'Programa não encontrado: {cmd[0]}. Instale FFmpeg e FFprobe.') from exc
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout)[-5000:])
    return p.stdout

def media_duration(path):
    out = run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',path])
    return float(json.loads(out)['format']['duration'])

def format_srt_time(sec):
    ms = int(round(sec * 1000))
    h, rem = divmod(ms, 3600000); m, rem = divmod(rem, 60000); s, ms = divmod(rem, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def split_chunks(text, max_chars=72):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks=[]
    for sent in sentences:
        words=sent.split(); cur=''
        for w in words:
            nxt=(cur+' '+w).strip()
            if len(nxt)>max_chars and cur:
                chunks.append(cur); cur=w
            else: cur=nxt
        if cur: chunks.append(cur)
    return chunks or [text]

def make_srt(text, total_duration, output):
    if total_duration <= 0:
        raise ValueError('A narração gerada não possui duração válida.')
    chunks=split_chunks(text)
    weights=[max(1,len(c)) for c in chunks]; total=sum(weights); t=0.0
    lines=[]
    for i,(c,w) in enumerate(zip(chunks,weights),1):
        dur=total_duration*w/total
        end=min(total_duration,t+dur)
        lines += [str(i), f'{format_srt_time(t)} --> {format_srt_time(end)}', c, '']
        t=end
    Path(output).write_text('\n'.join(lines), encoding='utf-8')
    return output

def normalize_clip(src, out, duration, width, height):
    vf=f'scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps=30,format=yuv420p'
    run(['ffmpeg','-y','-stream_loop','-1','-i',src,'-t',f'{duration:.3f}','-an','-vf',vf,
         '-c:v','libx264','-preset','veryfast','-crf','23',out])

def render_video(clips, narration, subtitles, output, width, height, burn_subtitles=True):
    if not clips: raise ValueError('Nenhum vídeo de apoio disponível.')
    work=Path(output).parent / '_render'; work.mkdir(parents=True, exist_ok=True)
    total=media_duration(narration)
    if total <= 0:
        raise ValueError('A narração gerada não possui duração válida.')
    segdur=total/len(clips)
    norm=[]
    for i,c in enumerate(clips):
        p=str(work/f'norm_{i:02d}.mp4'); normalize_clip(c,p,segdur,width,height); norm.append(p)
    concat=work/'concat.txt'
    concat.write_text('\n'.join("file '"+p.replace("'", "'\\''")+"'" for p in norm),encoding='utf-8')
    base=str(work/'base.mp4')
    run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',base])
    cmd=['ffmpeg','-y','-i',base,'-i',narration]
    if burn_subtitles:
        # Use absolute SRT path; FFmpeg's subtitles filter may require libass.
        srt=os.path.abspath(subtitles).replace('\\','/').replace(':','\\:').replace("'","\\'")
        cmd += ['-vf', f"subtitles='{srt}':force_style='FontName=Arial,FontSize=18,Outline=2,Shadow=0,Alignment=2,MarginV=50'"]
    cmd += ['-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','veryfast','-crf','22','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',output]
    run(cmd)
    return output
