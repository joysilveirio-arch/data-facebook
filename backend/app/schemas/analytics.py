from pydantic import BaseModel
from typing import List, Dict, Any

class OverviewOut(BaseModel):
    total_records: int
    total_labeled: int
    total_predicted: int
    distribution_label: Dict[str, int]
    distribution_predicted: Dict[str, int]
    top_authors: List[Dict[str, Any]]
    daily_counts: List[Dict[str, Any]]
    avg_likes: float