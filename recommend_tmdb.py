import json
import os
from engine import recommend
from tmdb_loader import fetch_movies_from_tmdb, convert_to_movies
from profile_utils import load_profile

def main():
    # Charger prefs.json
    with open("prefs.json", "r", encoding="utf-8") as f:
        prefs = json.load(f)

    # Charger profil
    profile = load_profile("profile.json")

    # Charger tags.json (optionnel)
    tags_map = {}
    if os.path.exists("tags.json"):
        with open("tags.json", "r", encoding="utf-8") as f:
            tags_map = json.load(f)

    # Étape 1 : récupérer films depuis TMDB
    raw_movies = fetch_movies_from_tmdb(genre_id=28, pages=2)  # ex: Action
    movies = convert_to_movies(raw_movies, tags_map)

    # Étape 2 : lancer le moteur de recommandation
    picks, scores = recommend(movies, prefs, context=None, profile=profile, k=3)

    # Étape 3 : afficher résultats
    print("\n🎬 Suggestions via TMDB :")
    for m in picks:
        print(f"- {m.title} (genres={m.genres}) -> score {scores[m.id]:.2f}")

if __name__ == "__main__":
    main()
