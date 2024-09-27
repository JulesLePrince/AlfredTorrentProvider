import json
import sys
sys.path.append("/Users/julesleprince/Developer/Alfred/alfred-server/Utils")
import requests
import urllib.parse
from app.Utils import tmdb_utils
import unicodedata


class YggApiTorrentMovieProvider:
    def __init__(self, base_url, passkey, movie_infos: dict = None, quality=1):
        self.base_url = base_url  # Url of ygg_torrent
        self.passkey = passkey  # Password
        self.movie_infos = movie_infos  # Movie infos in English & French


        # Create the urls from the titles
        self.french_url = self.title_to_ygg_search_url(f"{movie_infos['fr']['title']} {movie_infos['fr']['release_date']}")
        self.english_url = self.title_to_ygg_search_url(f"{movie_infos['en']['title']} {movie_infos['en']['release_date']}")

        self.torrent_max_size = 30

        # Potential movie list
        self.potential_movie_list = self.get_list_of_films(self.french_url) + self.get_list_of_films(
            self.english_url)

        self.potential_movie_list = self.get_potential_movie_list()

        # Best torrent algorithm
        self.chosen_one = self.best_torrent(self.potential_movie_list, quality=quality)


    def get_list_of_films(self, search_url):
        """
        Return a list of the n first results of a ygg_torrent movie research page
        """

        url_res = requests.get(search_url).content.decode("utf-8")
        data = json.loads(url_res)

        return data

    def best_torrent(self, film_list, quality=1):
        biases = [
            {
                'multi': 0 if self.movie_infos["en"]["original_language"] == 0 else 30,
                'four_k': 10,
                'hd': 20,
                'avc': 8,
                'bluray': 5
            },
            {
                'multi': 0 if self.movie_infos["en"]["original_language"] == 'fr' else 30,
                'four_k': 10,
                'hd': 20,
                'avc': 8,
                'bluray': 5
            },
            {
                'multi': 0 if self.movie_infos["en"]["original_language"] == 'fr' else 30,
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

        res = None
        score = 0  # best score

        for i in range(len(film_list)):
            s = 0
            film_title = film_list[i]["title"].lower().replace('multivision', '')

            if film_list[i]["size"]/1000000000 <= self.torrent_max_size and film_list[i]['seeders'] >= 3:


                if any(word in film_title for word in multi):
                    s += biases[quality]['multi']

                if any(word in film_title for word in four_k):
                    s += biases[quality]['four_k']
                else:
                    if any(word in film_title for word in hd):
                        s += biases[quality]['hd']

                if any(word in film_title for word in bluray):
                    s += biases[quality]['bluray']

                #print(f"title: {film_title} \n score: {s}\n\n")
                if s > score:
                    score = s
                    res = film_list[i]

        return res

    def download(self, path='cache', torrent_name='torrent'):
        """
        Download a torrent from its id
        """
        torrent_url = f"https://yggapi.eu/torrent/{self.chosen_one['id']}/download?passkey={self.passkey}"

        # We save torrent into path
        torrent = requests.get(torrent_url, allow_redirects=True)
        if len(torrent.content) < 100:
            raise ValueError

        open(f"{path}/{torrent_name}.torrent", 'wb').write(torrent.content)


        return f"{path}/{torrent_name}.torrent"

    def title_to_ygg_search_url(self, title):
        title = title.replace(" - ", " ").replace("’", " ")
        title = urllib.parse.quote_plus(title).lower()
        url = f"https://yggapi.eu/torrents?page=1&q={title}&order_by=uploaded_at&per_page=25"
        return url


    def coincides(self, file_title, movie_title):
        return remove_accents(file_title).lower()[0] == remove_accents(movie_title).lower()[0]
    def filter_potential_movies(self, pot_list, movie_title):
        res = []
        for file in pot_list:
            if self.coincides(file['title'], movie_title):
                res.append(file)
        return res

    def get_potential_movie_list(self):
        french_list = self.filter_potential_movies(self.get_list_of_films(self.french_url), self.movie_infos["fr"]["title"])
        english_list = self.filter_potential_movies(self.get_list_of_films(self.english_url), self.movie_infos["en"]["title"])
        return french_list + english_list


class YggApiSerieEpisodeProvider:
    def __init__(self, base_url, passkey, episode_infos: dict = None, quality=1):
        self.base_url = base_url  # Url of ygg_torrent
        self.passkey = passkey  # Password
        self.episode_infos = episode_infos  # Movie infos in English & French

        # Search Torrent
        self.torrent_max_size = 50.0
        if int(episode_infos['en']['season']) < 10:
            season = "S0" + str(episode_infos['en']['season'])
        else:
            season = "S" + str(episode_infos['en']['season'])

        if int(episode_infos['en']['episode']) < 10:
            episode = "E0" + str(episode_infos['en']['episode'])
        else:
            episode = "E" + str(episode_infos['en']['episode'])

        if episode_infos['en']['ended']:
            self.french_url = self.title_to_ygg_search_url(
                f"{episode_infos['fr']['title']} {season}")
            self.english_url = self.title_to_ygg_search_url(
                f"{episode_infos['en']['title']} {season}")
        else:
            self.french_url = self.title_to_ygg_search_url(
                f"{episode_infos['fr']['title']} {season}{episode}")
            self.english_url = self.title_to_ygg_search_url(
                f"{episode_infos['en']['title']} {season}{episode}")

        # Potential movie list
        self.potential_episode_list = self.get_list_of_films(self.french_url) + self.get_list_of_films(
            self.english_url)

        self.potential_episode_list = sorted(self.potential_episode_list, key=lambda d: -d['seeders'])

        # Best torrent algorithm
        self.chosen_one = self.best_torrent(self.potential_episode_list, quality=quality)


    def get_list_of_films(self, search_url):
        """
        Return a list of the n first results of a ygg_torrent movie research page
        """

        url_res = requests.get(search_url).content.decode("utf-8")
        data = json.loads(url_res)

        return data

    def best_torrent(self, film_list, quality=1):

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

        res = None
        score = 0  # best score

        for i in range(len(film_list)):
            s = 0
            film_title = film_list[i]["title"].lower().replace('multivision', '')

            if film_list[i]["size"]/1000000000 <= self.torrent_max_size:

                if any(word in film_title for word in multi):
                    s += biases[quality]['multi']

                if any(word in film_title for word in four_k):
                    s += biases[quality]['four_k']
                else:
                    if any(word in film_title for word in hd):
                        s += biases[quality]['hd']

                if any(word in film_title for word in bluray):
                    s += biases[quality]['bluray']


                if s > score:
                    score = s
                    res = film_list[i]

        return res

    def download(self, path='cache', torrent_name='torrent'):
        """
        Download a torrent from its id
        """
        torrent_url = f"https://yggapi.eu/torrent/{self.chosen_one['id']}/download?passkey=cIuo0dI1QQ7L0Vu4XLOlLCoKo0Cm3zO9"

        # We save torrent into path
        torrent = requests.get(torrent_url, allow_redirects=True)
        open(f"{path}/{torrent_name}.torrent", 'wb').write(torrent.content)
        if len(torrent.content) < 100:
            raise ValueError

        return f"{path}/{torrent_name}.torrent"

    def title_to_ygg_search_url(self, title):
        title = title.replace(" - ", " ")
        title = urllib.parse.quote_plus(title).lower()
        url = f"https://yggapi.eu/torrents?page=1&q={title}&order_by=uploaded_at&per_page=25"
        return url

def remove_accents(text):
    # Normalize the text to decompose combined characters
    normalized_text = unicodedata.normalize('NFD', text)
    # Filter out combining characters (accents)
    text_without_accents = ''.join(char for char in normalized_text if not unicodedata.combining(char))
    return text_without_accents

if __name__ == '__main__':
    movie = tmdb_utils.Movie(movie_id=660000)
    torrent_dl = YggApiTorrentMovieProvider("https://www.ygg.re", "cIuo0dI1QQ7L0Vu4XLOlLCoKo0Cm3zO9", movie.data, quality=2)
    torrent_dl.download(path="/Users/julesleprince/Downloads", torrent_name="test")
    print(torrent_dl.chosen_one)

    """serie = tmdb_utils.Serie(serie_id=203744, season=1, episode=7)
    torrent_dl = YggSerieEpisodeProvider(base_url="", passkey="cIuo0dI1QQ7L0Vu4XLOlLCoKo0Cm3zO9", episode_infos=serie.data, quality=2)
    print(torrent_dl.chosen_one)"""


