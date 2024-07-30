from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.TorrentProviders import ygg, yts, sharewood
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
    torrent_movie_provider = yts.YtsTorrentProvider(base_yts_url="https://yts.mx", movie_infos=movie.data, quality_wanted=quality_wanted)
    #torrent_movie_provider = ygg.YggTorrentMovieProvider("https://www.ygg.re", "Radarr_Alfred", "Jules2005", movie.data, quality=quality_wanted)
    #torrent_movie_provider = sharewood.SharewoodMovieProvider(base_url="https://www.sharewood.tv", passkey="fdbcd62ae3966e61aa872d0b90173fbd", movie_infos=movie.data, quality_wanted=quality_wanted)

    torrent_title = unidecode(movie.data['en']['title']).replace(' ', '_').replace("'", "_").lower()
    file_path = torrent_movie_provider.download(path="app/cachedTorrents", torrent_name=torrent_title)

    return FileResponse(path=file_path, filename=f"{torrent_title}.torrent", media_type='text/torrent')

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

    episode = tmdb_utils.Serie(serie_id=tmdb_id, season=season, episode=episode)
    torrent_episode_provider = sharewood.SharewoodSerieEpisodeProvider(passkey='fdbcd62ae3966e61aa872d0b90173fbd', base_url='https://www.sharewood.tv', episode_infos=episode.data, quality_wanted=quality_wanted)

    torrent_title = unidecode(episode.data['en']['title']).replace(' ', '_').replace("'", "_").lower()
    file_path = torrent_episode_provider.download(path="app/cachedTorrents", torrent_name=torrent_title)

    return FileResponse(path=file_path, filename=f"{torrent_title}.torrent", media_type='text/torrent')