import requests
import json
from app.Utils import tmdb_utils
import time
import os

class SharewoodMovieProvider:
    def __init__(self, base_url, passkey, movie_infos, quality_wanted):
        self.base_url = base_url
        self.passkey = passkey
        self.movie_infos = movie_infos
        self.api_url = f"{self.base_url}/api/{self.passkey}"
        self.quality = quality_wanted

        ####
        title = f"{movie_infos['fr']['title']} {movie_infos['en']['release_date']}"
        media_list = self.get_list_of_movie(title=title)
        self.best_media = self.best_movie_torrent(torrent_list=media_list, quality=self.quality)

    def get_list_of_movie(self, title):
        search_url = f"{self.api_url}/search"
        params = {
            'name': title
        }

        # API requests
        media_list = requests.get(search_url, params=params).content.decode("utf-8")

        # bytes to strings
        media_list = json.loads(media_list)

        # String to json
        media_list = sorted(media_list, key=lambda d: d['seeders'], reverse=True)

        return media_list

    def best_movie_torrent(self, torrent_list: list, quality=1):
        biases = [
            {
                'multi': 30,
                'four_k': 10,
                'hd': 20,
                'avc': 8,
                'bluray': 5
            },
            {
                'multi': 30,
                'four_k': 10,
                'hd': 20,
                'avc': 8,
                'bluray': 5
            },
            {
                'multi': 30,
                'four_k': 20,
                'hd': 10,
                'avc': 8,
                'bluray': 0
            }
        ]

        multi = ["multi", "vff-eng", "eng"]
        four_k = ["4k", "2160", "2160p"]
        hd = ["1080", "hd"]
        bluray = ["bluray"]

        n = 0  # best list
        score = 0  # best score

        for i in range(len(torrent_list)):
            s = 0

            if torrent_list[i]["size"] / 1000000000 <= 15.0 and torrent_list[i]["seeders"] >= 2:

                if any(word in torrent_list[i]["name"].lower() for word in multi):
                    s += biases[quality]['multi']

                if any(word in torrent_list[i]["name"].lower() for word in four_k):
                    s += biases[quality]['four_k']
                elif any(word in torrent_list[i]["name"].lower() for word in hd):
                    s += biases[quality]['hd']

                if any(word in torrent_list[i]["name"].lower() for word in bluray):
                    s += biases[quality]['bluray']

                if s > score:
                    score = s
                    n = i

        return torrent_list[n]

    def download(self, path, torrent_name='torrent'):
        time.sleep(0.5)
        torrent_url = f"{self.api_url}/{self.best_media['id']}/download"  # the torrent download url
        r = requests.get(torrent_url)
        open(f"{path}/{torrent_name}.torrent", 'wb').write(r.content)  # Create torrent file

        return f"{path}/{torrent_name}.torrent"


if __name__ == '__main__':
    movie = tmdb_utils.Movie(movie_id=639933)
    torrent_dl = SharewoodMovieProvider(passkey='fdbcd62ae3966e61aa872d0b90173fbd', base_url='https://www.sharewood.tv', movie_infos=movie.data, quality_wanted=2)
