import asyncio
import yt_dlp
import os
import innertube
import httpx
from dotenv import load_dotenv

load_dotenv()

class YouTubeHandler:
    def __init__(self):
        self.proxy = os.getenv("PROXY_URL")
        
        # Base yt-dlp config
        self.base_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
            'extract_flat': False,
            'cachedir': False,
            'youtube_include_dash_manifest': False,
            'allowed_extractors': ['youtube'],
            'force_ipv4': True,
            'geo_bypass': True,
            'cookiefile': 'cookies.txt',
            'proxy': self.proxy,
        }
        
        # InnerTube client
        self.it = innertube.InnerTube("WEB")
        
        self.invidious_instances = [
            "https://inv.tux.rs",
            "https://invidious.protokolla.fi",
            "https://invidious.lunar.icu",
            "https://iv.ggtyler.dev",
            "https://invidious.projectsegfau.lt",
            "https://invidious.tiekoetter.com"
        ]

    async def extract_info(self, url_or_id: str):
        """Extracts video metadata and direct URL with multi-client and Invidious fallbacks."""
        video_id = url_or_id[-11:] if len(url_or_id) > 11 else url_or_id
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        for client in ['android', 'ios', 'tv', 'mweb']:
            res = await self._try_yt_dlp(url, client=client)
            if res: return res
        
        print(f"yt-dlp failed, trying Invidious fallback with proxy support...")
        res = await self._try_invidious(video_id)
        if res: return res

        return None

    async def _try_yt_dlp(self, url, client=None):
        opts = self.base_opts.copy()
        if client:
            opts['extractor_args'] = {'youtube': {'player_client': [client]}}
            
        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                return {
                    'title': info.get('title'),
                    'url': info.get('url'),
                    'webpage_url': info.get('webpage_url'),
                    'id': info.get('id'),
                    'duration': info.get('duration'),
                    'thumbnail': info.get('thumbnail')
                }
        except Exception:
            return None

    async def _try_invidious(self, video_id):
        proxy_mounts = {"all://": self.proxy} if self.proxy else None
        async with httpx.AsyncClient(timeout=10.0, proxies=proxy_mounts) as client:
            for instance in self.invidious_instances:
                try:
                    resp = await client.get(f"{instance}/api/v1/videos/{video_id}")
                    if resp.status_code == 200:
                        data = resp.json()
                        return {
                            'title': data.get('title'),
                            'url': data.get('adaptiveFormats')[0].get('url') if data.get('adaptiveFormats') else None,
                            'webpage_url': f"https://www.youtube.com/watch?v={video_id}",
                            'id': video_id,
                            'duration': data.get('lengthSeconds'),
                            'thumbnail': data.get('videoThumbnails', [{}])[0].get('url')
                        }
                except Exception:
                    continue
        return None

    async def search(self, query: str, limit: int = 5):
        """Search for videos using InnerTube."""
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: self.it.search(query))
            results = []
            contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
            for section in contents:
                if 'itemSectionRenderer' in section:
                    for item in section['itemSectionRenderer']['contents']:
                        if 'videoRenderer' in item:
                            v = item['videoRenderer']
                            duration = 0
                            if 'lengthText' in v:
                                parts = list(map(int, v['lengthText']['simpleText'].split(':')))
                                for p in parts: duration = duration * 60 + p
                            
                            results.append({
                                'title': v['title']['runs'][0]['text'],
                                'id': v['videoId'],
                                'thumbnail': v['thumbnail']['thumbnails'][-1]['url'] if 'thumbnail' in v else '',
                                'duration': duration
                            })
                            if len(results) >= limit: break
                if len(results) >= limit: break
            return results
        except Exception:
            return []

    async def get_related_video(self, video_id: str):
        """Fetches a related video using InnerTube."""
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: self.it.next(video_id))
            secondary = data['contents']['twoColumnWatchNextResults']['secondaryResults']['secondaryResults']['results']
            for item in secondary:
                if 'compactVideoRenderer' in item:
                    return item['compactVideoRenderer']['videoId']
            return None
        except Exception:
            return None

# Singleton instance
yt_handler = YouTubeHandler()
