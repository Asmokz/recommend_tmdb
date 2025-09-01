import json
import os
import datetime
from typing import Dict, Any, Optional

PROFILE_TEMPLATE = {
    "seen": [],                 # liste des IDs de films vus
    "personal_ratings": {},     # {movie_id: note utilisateur}
    "last_suggested": {},       # {movie_id: date ISO}
}

def load_profile(profile_path: str = "resources/profile.json") -> Dict[str, Any]:
    """Charge le profil utilisateur ou initialise un nouveau fichier."""
    if not os.path.exists(profile_path):
        save_profile(PROFILE_TEMPLATE, profile_path)
    with open(profile_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profile(profile: Dict[str, Any], profile_path: str = "resources/profile.json") -> None:
    """Sauvegarde le profil utilisateur."""
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

def has_seen(movie_id: str, profile: Dict[str, Any]) -> bool:
    """Vérifie si un film a déjà été vu."""
    return movie_id in profile.get("seen", [])

def mark_seen(movie_id: str, profile: Dict[str, Any], profile_path: str = "resources/profile.json") -> None:
    """Ajoute un film à la liste des films vus."""
    if movie_id not in profile["seen"]:
        profile["seen"].append(movie_id)
    save_profile(profile, profile_path)

def get_personal_rating(movie_id: str, profile: Dict[str, Any]) -> float:
    """Retourne la note personnelle attribuée à un film (0.0 si absente)."""
    return float(profile.get("personal_ratings", {}).get(movie_id, 0.0))

def rate_movie(movie_id: str, rating: float, profile: Dict[str, Any], profile_path: str = "resources/profile.json") -> None:
    """Attribue une note personnelle à un film."""
    profile.setdefault("personal_ratings", {})[movie_id] = rating
    save_profile(profile, profile_path)

def update_last_suggested(movie_id: str, profile: Dict[str, Any], profile_path: str = "resources/profile.json") -> None:
    """Met à jour la date de dernière suggestion pour un film."""
    today = datetime.date.today().isoformat()
    profile.setdefault("last_suggested", {})[movie_id] = today
    save_profile(profile, profile_path)

def get_last_suggested(movie_id: str, profile: Dict[str, Any]) -> Optional[str]:
    """Retourne la date de dernière suggestion d’un film."""
    return profile.get("last_suggested", {}).get(movie_id)

def enrich_movie(movie: Dict[str, Any], tags_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Enrichit un film avec des infos locales (platform, tags).
    Exemple tags.json:
    {
      "550": {"platform": "Netflix", "tags": ["chill", "classique"]},
      "603": {"platform": "Prime Video", "tags": ["action"]}
    }
    """
    extra = tags_map.get(str(movie["id"]), {})
    return {**movie, **extra}
