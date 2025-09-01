import requests
import os
from typing import List, Dict
from engine import Movie
from profile_utils import enrich_movie
import dotenv

dotenv.load_dotenv()  # Charger les variables d'environnement depuis .env

TMDB_API_KEY = os.getenv("TMDB_API_KEY")  # ⚠️ mets ta clé en variable d'env


BASE_URL = "https://api.themoviedb.org/3"



def fetch_movies_from_tmdb(genre_id: int = None, pages: int = 10) -> List[Dict]:
    """Récupère des films depuis TMDB (découverte + filtre genre)."""
    results = []
    for page in range(1, pages + 1):
        url = f"{BASE_URL}/discover/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "fr-FR",
            "sort_by": "popularity.desc",
            "page": page,
        }
        if genre_id:
            params["with_genres"] = genre_id

        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        results.extend(data.get("results", []))
    return results

def convert_to_movies(raw_movies: List[Dict], tags_map: Dict[str, Dict] = None) -> List[Movie]:
    """Transforme les films TMDB en objets Movie (+ enrichissement tags)."""
    tags_map = tags_map or {}
    movies = []
    for m in raw_movies:
        genres = [str(gid) for gid in m.get("genre_ids", [])]  # ici juste IDs
        movie_dict = {
            "id": str(m["id"]),
            "title": m["title"],
            "genres": genres,
            "length_min": None,  # tu pourrais appeler une autre API pour runtime
            "platform": None,    # enrichi plus tard via tags.json
            "rating": m.get("vote_average", 0),
            "tags": [],
        }
        movie_dict = enrich_movie(movie_dict, tags_map)
        movies.append(Movie.from_dict(movie_dict))
    return movies
