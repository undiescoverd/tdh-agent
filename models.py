from pydantic import BaseModel, Field, EmailStr, HttpUrl, validator
from typing import Optional, Literal, Dict
import re

class ApplicantInfo(BaseModel):
    name: str = ""
    email: str = ""  # Using str instead of EmailStr to maintain compatibility
    phone: str = ""
    spotlight: Optional[str] = None  # Using str instead of HttpUrl for flexibility
    current_agency: Optional[str] = None
    work_auth: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^\+?\d[\d\s\-\(\)\.]{8,}$', v):
            raise ValueError('Invalid phone format')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

class MaterialsCollected(BaseModel):
    cv: Optional[str] = None
    dance_reel: Optional[str] = None
    vocal_reel: Optional[str] = None
    acting_reel: Optional[str] = None

class RequirementsCollected(BaseModel):
    basic_info: bool = False
    role_classification: bool = False
    materials_explanation: bool = False
    spotlight_check: bool = False
    representation_check: bool = False
    work_preferences: bool = False
    materials_collection: bool = False
    research_questions: bool = False

class WorkPreferences(BaseModel):
    theatre: bool = False
    abroad: bool = False
    cruises: bool = False
    tv_film: bool = False
    commercial: bool = False