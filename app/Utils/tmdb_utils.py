import tmdbv3api
import urllib.parse
import requests


class Movie:
    def __init__(self, movie_name=None, release_date=None, movie_id=None):
        self.tmdb = tmdbv3api.TMDb()
        self.tmdb.api_key = 'e842ac72f0a72988c663c44003975970'
        self.movie = tmdbv3api.Movie()

        # Name and year search
        if movie_name is not None:
            self.release_date = release_date
            self.movie_name = movie_name
            self.search = self.movie.search(self.movie_name)
            self.id = self.get_id()
        else:
            self.id = int(movie_id)
            self.details = self.movie.details(self.id)

        self.french = self.get_metadata('fr')
        self.english = self.get_metadata('en')
        self.release_date = self.get_release_date()
        self.data = {
            'fr': self.french,
            'en': self.english
        }

    def get_id(self):
        """
        return Movie id accounting the title and the release date if provided
        """
        if self.release_date is not None:
            for a in range(int(self.tmdb.total_pages)):
                self.search = self.movie.search(self.movie_name, a + 1)

                for i in range(len(self.search)):
                    if any('release_date' in tup for tup in self.search[i].items()) and self.search[i].release_date[
                                                                                        0:4] == self.release_date:
                        return self.search[i].id
        else:
            return self.search[0].id

    def get_metadata(self, language):
        self.tmdb.language = language
        m = self.movie.details(self.id)
        replace = {"&": {"en": "and", "fr": "et"}}

        return {
            'type': 'movie',
            'title': m.title.replace("&", replace["&"][language]),
            'overview': m.overview,
            'poster_url': "https://image.tmdb.org/t/p/w1280" + m.poster_path,
            'release_date': m.release_date[:4],
            'imdb_id': m['imdb_id']
        }

    def get_imdb_id(self):
        return self.english['imdb_id']

    def get_release_date(self):
        return self.english['release_date']

    def get_title(self, language):
        if language == 'en':
            return self.english['title']
        if language == 'fr':
            return self.french['title']

    def get_poster_url(self, language):
        if language == 'en':
            return self.english['poster_url']
        if language == 'fr':
            return self.french['poster_url']

    def get_overview(self, language):
        if language == 'en':
            return self.english['overview']
        if language == 'fr':
            return self.french['overview']


class Serie:
    def __init__(self, serie_name=None, release_date=None, serie_id=None, season=None, episode=None):
        self.tmdb = tmdbv3api.TMDb()
        self.tmdb.api_key = 'e842ac72f0a72988c663c44003975970'
        self.serie = tmdbv3api.TV()

        # Name and year search
        if serie_name is not None:
            self.release_date = release_date
            self.serie_name = serie_name
            self.search = self.serie.search(self.serie_name)
            self.id = self.get_id()
        else:
            self.id = int(serie_id)
            self.season = int(season)
            self.episode = int(episode)
            self.details = self.serie.details(self.id)

        self.french = self.get_metadata('fr')
        self.english = self.get_metadata('en')
        self.data = {
            'en': self.english,
            'fr': self.french
        }


    def get_metadata(self, language):
        self.tmdb.language = language
        s = self.serie.details(self.id)

        replace = {"&": {"en": "and", "fr": "et"}}

        return {
            'type': 'serie',
            'season': self.season,
            'episode': self.episode,
            'title': self.exception_handler(s.name.replace("&", replace["&"][language])),
            'ended': (s.next_episode_to_air is None) or (s.next_episode_to_air["season_number"] is not self.season),
            'imdb_id': self.get_imdb_id()
            #'backdrop_path': "https://image.tmdb.org/t/p/w1280" + s.seasons[self.season-1]['poster_path']

        }


    def get_imdb_id(self):
        link = f"https://api.themoviedb.org/3/tv/{self.id}/external_ids?api_key={self.tmdb.api_key}&language=en-US"
        r = requests.get(link)
        return r.json()['imdb_id']

    def get_title(self, language):
        if language == 'en':
            return self.english['title']
        if language == 'fr':
            return self.french['title']

    def get_release_date(self):
        return self.english['release_date']

    def get_id(self):
        return self.id

    def exception_handler(self, tmdb_title):
        exceptions = {
            83867: "Andor"
        }

        if self.id not in exceptions.keys():
            return tmdb_title
        else:
            return exceptions[self.id]

def title_to_ygg_search_url(title, base_url):
    title = urllib.parse.quote_plus(title).lower()
    url = base_url + "/engine/search?name=" + title + "&description=&file=&uploader=&category=2145&sub_category=all" \
                                                      "&do=search&order=desc&sort=seed "
    return url


def title_to_rarbg_search_url(title, base_url):
    title = urllib.parse.quote_plus(title).lower()
    url = base_url + "/search/?search=" + title + "&order=seeders&by=DESC"
    return url



if __name__ == '__main__':

    movie = Movie(movie_id=289)
    print(f"{movie.data['en']['title']} ({movie.data['en']['release_date']})")

    #serie = Serie(serie_id=83867, season=1, episode=9)
    #print(serie.data)
