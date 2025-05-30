from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class EssayState(BaseModel):
    user_id: str = "demo_user"
    topic: str = ""
    requirements: str = ""
    profile: Dict[str, str] = {}
    ideas: List[str] = Field(default_factory=list)
    outline: List[str] = Field(default_factory=list)
    draft: str = ""
    review_json: Optional[dict] = None
    passes: bool = False
