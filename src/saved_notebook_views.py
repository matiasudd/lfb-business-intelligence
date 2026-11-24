"""Create offline HTML copies from saved notebook cells; never execute data code."""
from pathlib import Path
import json,html,re

def inline(s):
    s=html.escape(s)
    s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<a href="\2">\1</a>',s)
    s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)
    s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    return s

def markdown(s):
    lines=s.splitlines();out=[];table=[]
    def flush():
        nonlocal table
        if table:
            rows=[]
            for i,line in enumerate(table):
                if re.fullmatch(r'[| :\-]+',line):continue
                tag='th' if not rows else 'td';rows.append('<tr>'+''.join(f'<{tag}>{inline(v.strip())}</{tag}>' for v in line.strip('|').split('|'))+'</tr>')
            out.append('<table>'+''.join(rows)+'</table>');table=[]
    for line in lines:
        if line.startswith('|'):table.append(line);continue
        flush()
        m=re.match(r'^(#{1,6}) (.*)',line)
        if m:out.append(f'<h{len(m[1])}>{inline(m[2])}</h{len(m[1])}>')
        elif line.strip():out.append('<p>'+inline(line)+'</p>')
    flush();return '\n'.join(out)

def render(root):
    root=Path(root);out=root/'docs/readable_views';out.mkdir(parents=True,exist_ok=True)
    css='''body{font:16px/1.55 Arial,sans-serif;color:#14283d;max-width:1150px;margin:40px auto;padding:0 24px}h1,h2,h3{color:#16446d}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f6fa;padding:16px;font:13px/1.5 Consolas,monospace}table{border-collapse:collapse;width:100%;margin:20px 0;display:block;overflow:auto}td,th{border:1px solid #dbe3eb;padding:8px;vertical-align:top;overflow-wrap:anywhere}th{background:#e7eef5;text-align:left}img{max-width:100%;height:auto}section{margin:22px 0}.note{background:#f3f6fa;padding:16px}code{overflow-wrap:anywhere}'''
    for source in sorted((root/'notebooks').glob('*.ipynb')):
        nb=json.loads(source.read_text(encoding='utf-8'));parts=['<p class="note">Offline reading copy of the saved notebook. No code runs on this page. No datasets are included.</p>']
        for cell in nb['cells']:
            text=''.join(cell['source']) if isinstance(cell['source'],list) else cell['source']
            if cell['cell_type']=='markdown':parts.append('<section>'+markdown(text)+'</section>');continue
            parts.append('<section><pre>'+html.escape(text)+'</pre>')
            for output in cell.get('outputs',[]):
                data=output.get('data',{})
                if 'image/png' in data:
                    b=data['image/png'];b=''.join(b) if isinstance(b,list) else b
                    parts.append('<img alt="Saved notebook chart" src="data:image/png;base64,'+b+'">')
                elif 'text/html' in data:
                    h=data['text/html'];parts.append(''.join(h) if isinstance(h,list) else h)
                else:
                    t=output.get('text',data.get('text/plain',''));t=''.join(t) if isinstance(t,list) else t
                    if t:parts.append('<pre>'+html.escape(t)+'</pre>')
            parts.append('</section>')
        (out/(source.stem+'.html')).write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>'+source.stem+'</title><style>'+css+'</style><body>'+''.join(parts)+'</body></html>',encoding='utf-8')
    return out

if __name__=='__main__':print(render(Path(__file__).resolve().parents[1]))
