from crewai.tools import BaseTool
from pathlib import Path
import json

class ProfileLoader(BaseTool):
    name: str = "profile_loader"
    description: str = (
        "Loads a user profile from data/profiles.json."
    )

    def _run(self, user_id: str):
        """Return a dict with the profile or an empty dict if not found."""
        db_path = Path(__file__).resolve().parents[2] / "data" / "profiles.json"
        if not db_path.exists():
            return {}
        with open(db_path, encoding="utf-8") as fp:
            db = json.load(fp)
        return db.get(user_id, {})