import argparse
import json
import random
from typing import Dict, Any, List, Optional, Tuple
import os

from profile_utils import (
    load_profile,
    has_seen,
    get_personal_rating,
    update_last_suggested,
)

# -------------------------
# MODELE DE DONNEE
# -------------------------

# Charger le mapping des genres TMDB
with open("genre_map.json", "r", encoding="utf-8") as f:
    GENRE_MAP = json.load(f)

def _map_genres(genre_ids):
    """Convertit les IDs TMDB en noms selon genre_map.json"""
    return [GENRE_MAP.get(str(gid), str(gid)) for gid in genre_ids]

class Movie:
    def __init__(self, id: str, title: str, genres: List[str], length_min: Optional[int],
                 platform: Optional[str], rating: float, seen: bool = False,
                 last_suggested: Optional[str] = None, tags: Optional[List[str]] = None):
        self.id = id
        self.title = title
        self.genres = genres
        self.length_min = length_min
        self.platform = platform
        self.rating = rating
        self.seen = seen
        self.last_suggested = last_suggested
        self.tags = tags or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "genres": self.genres,
            "length_min": self.length_min,
            "platform": self.platform,
            "rating": self.rating,
            "seen": self.seen,
            "last_suggested": self.last_suggested,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        return cls(
            id=str(d["id"]),
            title=d["title"],
            genres=d.get("genres", []),
            length_min=d.get("length_min"),
            platform=d.get("platform"),
            rating=d.get("rating", 0),
            seen=d.get("seen", False),
            last_suggested=d.get("last_suggested"),
            tags=d.get("tags", []),
        )

# -------------------------
# SCORING
# -------------------------

def _score_movie(movie, prefs: Dict[str, Any],
                 context: Optional[Dict[str, Any]] = None,
                 profile: Optional[Dict[str, Any]] = None) -> float:
    score = movie.rating or 0.0

    # --- Exclusions directes ---
    if prefs.get("exclude_seen") and profile and has_seen(movie.id, profile):
        return -999  # éliminé

    if prefs.get("avoid_genres"):
        if any(g in prefs["avoid_genres"] for g in _map_genres(movie.genres)):
            return -999

    if prefs.get("max_length_min") and movie.length_min:
        if movie.length_min > prefs["max_length_min"]:
            return -999

    # --- Genres préférés ---
    genre_weights = prefs.get("genres", {})
    if movie.genres:
        mapped = _map_genres(movie.genres)
        genre_score = sum(genre_weights.get(g, 0) for g in mapped) / len(mapped)
        score += genre_score

    # --- Plateformes préférées ---
    if movie.platform:
        score += prefs.get("platforms_preferred", {}).get(movie.platform, 0)

    # --- Note perso si dispo ---
    if profile:
        personal = get_personal_rating(movie.id, profile)
        if personal:
            score += personal

    # --- Contexte (mood) ---
    if context and context.get("mood") and movie.tags:
        if context["mood"] in movie.tags:
            score += 0.5

    return score

# -------------------------
# RECOMMANDATION
# -------------------------

def recommend(movies: List[Movie], prefs: Dict[str, Any],
              context: Optional[Dict[str, Any]] = None,
              profile: Optional[Dict[str, Any]] = None,
              k: int = 5, diversity: float = 0.3) -> Tuple[List[Movie], Dict[str, float]]:
    """
    Renvoie une liste de recommandations et les scores.
    - movies : liste de Movie (déjà chargés)
    - prefs : préférences utilisateur (poids genres, plateformes…)
    - context : humeur ou autre info
    - profile : données perso (notes, seen, last_suggested)
    - k : nombre de films à suggérer
    - diversity : proba de prendre un film au hasard dans le top pour varier
    """
    scored = [(m, _score_movie(m, prefs, context, profile)) for m in movies]
    scored.sort(key=lambda x: x[1], reverse=True)

    selected = []
    scores = {}
    for m, s in scored:
        if len(selected) >= k:
            break
        if random.random() < diversity and len(scored) > k:
            pick = random.choice(scored[k:])[0]
            selected.append(pick)
            scores[pick.id] = s
        else:
            selected.append(m)
            scores[m.id] = s

    # Mise à jour du profil (dernière suggestion)
    if profile:
        for m in selected:
            update_last_suggested(m.id, profile)

    return selected, scores

# -------------------------
# MAIN (CLI)
# -------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--movies", type=str, default="movies.json")
    parser.add_argument("--prefs", type=str, default="prefs.json")
    parser.add_argument("--profile", type=str, default="profile.json")
    parser.add_argument("--context", type=str, default="contexts.json")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--diversity", type=float, default=0.3)
    args = parser.parse_args()

    # Charger films
    with open(args.movies, "r", encoding="utf-8") as f:
        movies_raw = json.load(f)
    movies = [Movie.from_dict(m) for m in movies_raw]

    # Charger prefs
    with open(args.prefs, "r", encoding="utf-8") as f:
        prefs = json.load(f)

    # Charger profil
    profile = load_profile(args.profile)

    # Charger contexte (facultatif)
    context = None
    if args.context and os.path.exists(args.context):
        with open(args.context, "r", encoding="utf-8") as f:
            context = json.load(f)

    picks, scores = recommend(movies, prefs, context, profile,
                              k=args.k, diversity=args.diversity)

    print("\n🎬 Recommandations :")
    for m in picks:
        print(f"- {m.title} ({', '.join(m.genres)}) -> score {scores[m.id]:.2f}")

if __name__ == "__main__":
    main()
