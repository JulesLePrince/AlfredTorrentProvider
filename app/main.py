from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.TorrentProviders import ygg, yts, sharewood, ygg_api
from app.Utils import tmdb_utils
from unidecode import unidecode


app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/filetest")
def read_root():
    return FileResponse(path="http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4", filename="bunny", media_type='text/mp4')

@app.get("/movie/get_torrent/{tmdb_id}")
def read_item(tmdb_id: int, quality:str="1080p"):
    match quality:
        case "720p":
            quality_wanted = 0
        case "1080p" :
            quality_wanted = 1
        case "4k":
            quality_wanted = 2
        case _:
            quality_wanted = 1

    movie = tmdb_utils.Movie(movie_id=tmdb_id)
    torrent_title = unidecode(movie.data['en']['title']).replace(' ', '_').replace("'", "_").lower()

    try:
        torrent_movie_provider = ygg_api.YggTorrentMovieProvider("https://www.ygg.re", "cIuo0dI1QQ7L0Vu4XLOlLCoKo0Cm3zO9", movie.data, quality=2)
        print(f"{movie.get_title('en')} found on Ygg")
        file_path = torrent_movie_provider.download(path="app/cachedTorrents", torrent_name=torrent_title)
        return FileResponse(path=file_path, filename=f"{torrent_title}.torrent", media_type='text/torrent')
    except:
        print(f"{movie.get_title('en')} not found on Ygg")

    try:
        torrent_movie_provider = sharewood.SharewoodMovieProvider(base_url="https://www.sharewood.tv", passkey="fdbcd62ae3966e61aa872d0b90173fbd", movie_infos=movie.data, quality_wanted=quality_wanted)
        file_path = torrent_movie_provider.download(path="app/cachedTorrents", torrent_name=torrent_title)
        print(f"{movie.get_title('en')} found on Sharewood")
        return FileResponse(path=file_path, filename=f"{torrent_title}.torrent", media_type='text/torrent')
    except :
        print(f"{movie.get_title('en')} not found on Sharewood")

    try:
        torrent_movie_provider = yts.YtsTorrentProvider(base_yts_url="https://yts.mx", movie_infos=movie.data, quality_wanted=quality_wanted)
        print(f"{movie.get_title('en')} found on Yts")
        file_path = torrent_movie_provider.download(path="app/cachedTorrents", torrent_name=torrent_title)
        return FileResponse(path=file_path, filename=f"{torrent_title}.torrent", media_type='text/torrent')

    except :
        print(f"{movie.get_title('en')} not found on Yts")

    return None

@app.get("/serie/get_torrent/{tmdb_id}")
def read_item(tmdb_id: int, quality:str="1080p", season:int=1, episode:int=1):
    match quality:
        case "720p":
            quality_wanted = 0
        case "1080p" :
            quality_wanted = 1
        case "4k":
            quality_wanted = 2
        case _:
            quality_wanted = 1

    serie_episode = tmdb_utils.Serie(serie_id=tmdb_id, season=season, episode=episode)
    torrent_title = unidecode(serie_episode.data['en']['title']).replace(' ', '_').replace("'", "_").lower()

    try :
        torrent_episode_yggProvider = ygg_api.YggSerieEpisodeProvider(base_url="https://www.ygg.re", passkey="cIuo0dI1QQ7L0Vu4XLOlLCoKo0Cm3zO9", episode_infos=serie_episode.data, quality=quality_wanted)
        file_path = torrent_episode_yggProvider.download(path="app/cachedTorrents", torrent_name=torrent_title)
        print(f"{serie_episode.data['en']['title']} Season {season}, Episode {episode} found on Ygg")
        return FileResponse(path=file_path, filename=f"{torrent_title}.torrent", media_type='text/torrent')
    except:
        print(f"{serie_episode.data['en']['title']} Season {season}, Episode {episode} NOT found on Ygg")

    try :
        torrent_episode_sharewoodProvider = sharewood.SharewoodSerieEpisodeProvider(passkey='fdbcd62ae3966e61aa872d0b90173fbd', base_url='https://www.sharewood.tv', episode_infos=serie_episode.data, quality_wanted=quality_wanted)
        file_path = torrent_episode_sharewoodProvider.download(path="app/cachedTorrents", torrent_name=torrent_title)
        print(f"{serie_episode.data['en']['title']} Season {season}, Episode {episode} found on Sharewood")
        return FileResponse(path=file_path, filename=f"{torrent_title}.torrent", media_type='text/torrent')
    except:
        print(f"{serie_episode.data['en']['title']} Season {season}, Episode {episode} NOT found on Sharewood")