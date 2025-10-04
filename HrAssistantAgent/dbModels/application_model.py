from dataclasses import dataclass

@dataclass
class Application:
    id: int
    job_id: int
    name: str
    email: str
    phone: str
    resume_url: str