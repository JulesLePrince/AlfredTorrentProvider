import sys
sys.path.append("/Users/julesleprince/Developer/Alfred/alfred-server/Utils")
import requests
from requests_toolbelt import MultipartEncoder
import random
import string
from bs4 import BeautifulSoup
import unidecode
import unidecode
import urllib.parse
from Utils import tmdb_utils
import os
import yaml


class YggTorrentMovieProvider:
    def __init__(self, base_url, username, password, movie_infos: dict = None, quality=1):
        self.base_url = base_url  # Url of ygg_torrent
        self.username = username  # Username
        self.password = password  # Password
        self.movie_infos = movie_infos  # Movie infos in English & French
        self.session = requests.session() # We create a Session

        #clearance_file = open('/Users/julesleprince/Developer/Alfred/alfred-server/Downloaders/CF-Clearance-Scraper/cookies.json')
        #clearance_data = json.loads(clearance_file.read())

        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        self.cppkies = {
        }  # Cookies

        # login
        self.login_status = self.login()
        if self.login_status == 200:
            print(f"Successfully connected to YggTorrent with code {self.login_status}")
        else:
            print(f"Connexion error with code {self.login_status}")

        # Create the urls from the titles
        self.french_url = self.title_to_ygg_search_url(f"{movie_infos['fr']['title']} {movie_infos['fr']['release_date']}")
        print(self.french_url)
        self.english_url = self.title_to_ygg_search_url(f"{movie_infos['en']['title']} {movie_infos['en']['release_date']}")
        print(self.english_url)
        self.torrent_max_size = 16

        # Potential movie list
        self.potential_movie_list = self.get_list_of_films(self.french_url, 10) + self.get_list_of_films(
            self.english_url, 10)

        # Best torrent algorithm
        self.chosen_one = self.best_torrent(self.potential_movie_list, quality=quality)

    def login(self):
        """
        Login method to ygg_torrent
        return 200 if all is successful
        """

        # Auth Information that will be formatted later
        auth = {
            "id": self.username,
            "pass": self.password
        }

        # I format the auth request to match ygg_torrent format
        boundary = '----WebKitFormBoundary' \
                   + ''.join(random.sample(string.ascii_letters + string.digits, 16))
        m = MultipartEncoder(fields=auth, boundary=boundary)

        # Needed headers
        sah_headers = {
            'Content-Type': m.content_type,
            "user-agent": self.user_agent
        }

        # Try to connect to ygg_torrent. If successful add the ygg session token to the cookies, else return error 400
        r1 = self.session.get(f"{self.base_url}/auth/login", headers=sah_headers, cookies=self.cppkies)
        try:
            yggtorrent_token = r1.cookies.get_dict()["ygg_"]
        except:
            return 400

        self.cppkies["ygg_"] = yggtorrent_token

        # Connect with the account to ygg torrent
        self.session.post(self.base_url + '/auth/process_login', data=m, headers=sah_headers, cookies=self.cppkies)
        test = self.session.get(self.base_url + '/user/ajax_usermenu', cookies=self.cppkies, headers=sah_headers)

        return test.status_code

    def get_id(self, film_link: str):
        """
        Get the id of a movie from the movie link
        """
        r = 0
        i = 1

        while film_link[-i] != "/":
            r = -i
            i = i + 1

        id_ = ""

        while film_link[r] != "-":
            id_ = id_ + film_link[r]
            r = r + 1

        return id_

    def get_list_of_films(self, list_link, list_size):
        """
        Return a list of the n first results of a ygg_torrent movie research page
        """

        # Needed Headers
        sah_headers = {
            "user-agent": self.user_agent
        }


        # Raw html string of the link
        html_string = self.session.get(list_link, headers=sah_headers, cookies=self.cppkies).text

        soup = BeautifulSoup(html_string, 'lxml')  # Parse the HTML as a string

        try:
            table = soup.find_all('table')[1]
        except IndexError:
            return []

        table = soup.find_all('table')[1]  # Grab the first table

        # In case the list_size is greater than the size of the actual url_list
        if list_size > len(table.find_all('tr')) - 2:
            list_size = len(table.find_all('tr')) - 2

        data = []

        for num in range(list_size + 1):
            data.append({})

        n = 0
        for n in range(list_size + 1):
            a = table.find_all('tr')[n + 1].find_all('a')[1]

            data[n]["title"] = a.text.lower()
            data[n]["ygg_link"] = unidecode.unidecode(a.get('href'))
            data[n]["size"] = float(table.find_all('tr')[n + 1].find_all('td')[5].text[0:-2])
            data[n]["seeds"] = int(table.find_all('tr')[n + 1].find_all('td')[7].text)
            data[n]["id"] = self.get_id(data[n]["ygg_link"])
            data[n]["url"] = self.base_url + "/engine/download_torrent?id=" + data[n]["id"]

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

        n = 0  # best list
        score = 0  # best score
        size = 0

        for i in range(len(film_list)):
            s = 0
            film_title = film_list[i]["title"].lower().replace('multivision', '')

            if film_list[i]["size"] <= self.torrent_max_size:

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
                    n = i
                    size = film_list[i]["size"]

        return film_list[n]

    def download(self, path='cache', torrent_name='torrent'):
        """
        Download a torrent from its id
        """

        torrent_url = self.chosen_one['url']

        # Needed headers
        sah_headers = {
            "user-agent": self.user_agent
        }

        # We save torrent into path
        torrent = self.session.get(torrent_url, allow_redirects=True, cookies=self.cppkies, headers=sah_headers)
        open(f"{path}/{torrent_name}.torrent", 'wb').write(torrent.content)

        return f"{path}/{torrent_name}.torrent"

    def title_to_ygg_search_url(self, title):
        title = title.replace("-", "")
        title = urllib.parse.quote_plus(title).lower()
        url = self.base_url + "/engine/search?name=" + title + "&do=search&order=desc&sort=seed"
        return url


if __name__ == '__main__':
    movie = tmdb_utils.Movie(movie_id=575264)
    #serie = tmdb_utils.Serie(serie_id=94997, season=1, episode=9)
    torrent_dl = YggTorrentMovieProvider("https://www.ygg.re", "Radarr_Alfred", "Jules2005", movie.data, quality=2)
    print(torrent_dl.chosen_one)

