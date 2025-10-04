from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class Job:
    title: str
    company: str
    id: Optional[int] = None
    location: Optional[str] = "Remote"
    type: Optional[str] = None
    salary: Optional[str] = "Competitive"
    description: Optional[str] = None
    requirements: Optional[List[str]] = field(default_factory=list)    
    posted: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create a Job object from a dict (Supabase response)."""        
        return cls(
            id = data.get("id", None),
            title=data["title"],
            company=data["company"],
            location=data.get("location", "Remote"),
            type=data.get("type"),
            salary=data.get("salary", "Competitive"),
            description=data.get("description"),
            requirements=data.get("requirements") if data.get("requirements") else [],
            posted = data.get("posted", None)
        )
    
    def to_dict(self):
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "type": self.type,
            "salary": self.salary,
            "description": self.description,
            "requirements": self.requirements,
        }