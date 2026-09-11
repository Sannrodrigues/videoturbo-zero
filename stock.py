from pathlib import Path
import requests

PEXELS_SEARCH = 'https://api.pexels.com/v1/videos/search'

def search_videos(api_key: str, query: str, orientation: str, per_page: int = 5):
    headers = {'Authorization': api_key}
    params = {'query': query, 'orientation': orientation, 'size': 'medium', 'per_page': per_page}
    r = requests.get(PEXELS_SEARCH, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get('videos', [])

def _best_file(video):
    files = [f for f in video.get('video_files', []) if f.get('link')]
    if not files:
        return None
    # Prefer HD/FHD while avoiding giant source files.
    files.sort(key=lambda f: abs((f.get('width') or 1280) - 1280) + abs((f.get('height') or 720) - 720))
    return files[0]

def download_for_queries(api_key: str, queries, orientation: str, dest_dir: str):
    out = []
    credits = []
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    seen = set()
    for i, q in enumerate(queries):
        videos = search_videos(api_key, q, orientation)
        picked = next((v for v in videos if v.get('id') not in seen and _best_file(v)), None)
        if not picked:
            continue
        seen.add(picked.get('id'))
        vf = _best_file(picked)
        path = Path(dest_dir) / f'clip_{i+1:02d}.mp4'
        with requests.get(vf['link'], stream=True, timeout=90) as rr:
            rr.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in rr.iter_content(chunk_size=1024*1024):
                    if chunk: f.write(chunk)
        out.append(str(path))
        credits.append({'query': q, 'pexels_url': picked.get('url',''), 'creator': picked.get('user',{}).get('name','')})
    return out, credits
