from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Optional
from uuid import UUID, uuid4
from datetime import datetime

class JobInput(BaseModel):
    files: List[str]
    profiles: Dict[str, str]
    output_root: str

class JobOptions(BaseModel):
    priority: Literal['urgent', 'normal', 'background'] = 'normal'
    schedule: Optional[datetime] = None

class JobTicket(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    task: Literal['convert', 'render', 'optics', 'pipeline']
    input: JobInput
    options: Optional[JobOptions] = None
    loaded_profiles: Optional[Dict[str, Dict]] = None

class Versions(BaseModel):
    sw: Optional[str] = None
    dm: Optional[str] = None
    blender: Optional[str] = None
    luxcore: Optional[str] = None

class ConvertResult(BaseModel):
    status: Literal['success', 'failure', 'pending']
    missing_refs: Optional[int] = None
    crc: Optional[str] = None

class RenderResult(BaseModel):
    images: Optional[List[str]] = None
    video: Optional[str] = None

class OpticsResult(BaseModel):
    distances: Optional[List[int]] = None
    U0: Optional[float] = None
    Eavg_lux: Optional[float] = None

class Metadata(BaseModel):
    assembly: str
    timestamp: datetime = Field(default_factory=datetime.now)
    versions: Versions
    profiles: Dict[str, str]
    convert: Optional[ConvertResult] = None
    render: Optional[RenderResult] = None
    optics: Optional[OpticsResult] = None

class JobStatusResponse(BaseModel):
    job_id: UUID
    task: str
    status: Literal['queued', 'pending', 'running', 'success', 'failure']
    details: Optional[Dict] = None