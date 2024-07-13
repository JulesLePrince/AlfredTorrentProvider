import requests
import os
from Utils import tmdb_utils

home = os.path.expanduser("~")

class YtsTorrentProvider:
    def __init__(self, base_yts_url, movie_infos: dict, quality_wanted: int = 2):
        self.imdb_id = movie_infos['en']['imdb_id']
        self.quality_wanted = quality_wanted

        self.link = f"{base_yts_url}/api/v2/movie_details.json?imdb_id=" + self.imdb_id
        response = requests.get(self.link)
        self.infos = response.json()

        self.versions = self.infos['data']['movie']['torrents']
        self.torrent_chosen = self.best_torrent()

    def best_torrent(self):
        quality_order = ['720p', '1080p', '2160p']
        chosen_one = None
        max_seed = -1

        while chosen_one is None or abs(self.quality_wanted) > 2:
            for torrent in self.versions:
                if torrent['quality'] == quality_order[abs(self.quality_wanted)] and torrent['seeds'] > max_seed:
                    chosen_one = torrent
                    max_seed = torrent['seeds']
            self.quality_wanted -= 1

        return chosen_one

    def download(self, path=home, torrent_name='torrent'):
        torrent_url = self.torrent_chosen['url']

        # Downwload to cache folder
        torrent = requests.get(torrent_url)
        open(f"{path}/{torrent_name}.torrent", 'wb').write(torrent.content)

        return f"{path}/{torrent_name}.torrent"

if __name__ == '__main__':
    movie = tmdb_utils.Movie(movie_id=36557 )
    torrent_dl = YtsTorrentProvider(base_yts_url="https://yts.mx", movie_infos=movie.data, quality_wanted=2)
    print(torrent_dl.torrent_chosen)