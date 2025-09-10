from typing import Tuple, Dict
import re
import logging

logger = logging.getLogger(__name__)

class MaterialValidator:
    """Handles validation of submitted materials like CVs and video reels."""
    
    @staticmethod
    def validate_cv(content: str) -> Tuple[bool, str]:
        """Validate CV submission format."""
        content_lower = content.lower()
        
        # Check for common document formats
        valid_formats = ["pdf", "doc", "docx", "word", ".pdf", ".doc", ".docx"]
        
        if any(format_type in content_lower for format_type in valid_formats):
            return True, "CV format accepted"
        
        # Check if it mentions attachment or file
        attachment_keywords = ["attachment", "attached", "file", "document", "resume", "cv"]
        if any(keyword in content_lower for keyword in attachment_keywords):
            return True, "CV submission noted"
        
        return False, "CV must be in PDF or Word format"
    
    @staticmethod
    def validate_video_link(content: str, material_type: str) -> Tuple[bool, str]:
        """Validate video reel link format."""
        # YouTube patterns
        youtube_patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)',
            r'youtube\.com',
            r'youtu\.be'
        ]
        
        # Vimeo patterns
        vimeo_patterns = [
            r'vimeo\.com/\d+',
            r'vimeo\.com'
        ]
        
        content_lower = content.lower()
        
        # Check for YouTube
        if any(re.search(pattern, content_lower) for pattern in youtube_patterns):
            return True, f"{material_type} link accepted (YouTube)"
        
        # Check for Vimeo
        if any(re.search(pattern, content_lower) for pattern in vimeo_patterns):
            return True, f"{material_type} link accepted (Vimeo)"
        
        # Check if they mention having a reel without providing link
        reel_keywords = ["reel", "video", "demo", "showreel", "footage"]
        if any(keyword in content_lower for keyword in reel_keywords):
            return False, f"Please provide a direct YouTube or Vimeo link for your {material_type}"
        
        return False, f"{material_type} must be a YouTube or Vimeo link"
    
    @staticmethod
    def validate_spotlight_link(content: str) -> Tuple[bool, str]:
        """Validate Spotlight profile link."""
        spotlight_patterns = [
            r'spotlight\.com',
            r'portal\.spotlight\.com'
        ]
        
        content_lower = content.lower()
        
        if any(re.search(pattern, content_lower) for pattern in spotlight_patterns):
            return True, "Spotlight link accepted"
        
        return False, "Please provide a valid Spotlight profile URL"

class InputValidator:
    """Handles validation of user input data."""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format."""
        if not email:
            return False, "Email is required"
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return True, "Email format is valid"
        
        return False, "Please provide a valid email address"
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """Validate phone number format."""
        if not phone:
            return False, "Phone number is required"
        
        # Remove common separators and spaces
        clean_phone = re.sub(r'[\s\-\(\)\.]', '', phone)
        
        # Check for reasonable length (8-15 digits with optional country code)
        if re.match(r'^\+?\d{8,15}$', clean_phone):
            return True, "Phone number format is valid"
        
        return False, "Please provide a valid phone number"
    
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, str]:
        """Validate name format."""
        if not name or len(name.strip()) < 2:
            return False, "Please provide your full name"
        
        # Check for reasonable name format (letters, spaces, hyphens, apostrophes)
        if re.match(r"^[a-zA-Z\s\-'\.]+$", name.strip()):
            return True, "Name format is valid"
        
        return False, "Please provide a valid name using only letters"

class ContentValidator:
    """Handles content-based validation."""
    
    @staticmethod
    def extract_and_validate_materials(content: str, role_type: str) -> Dict[str, Tuple[bool, str]]:
        """Extract and validate all materials mentioned in content."""
        results = {}
        
        # Define required materials by role
        role_materials = {
            "Dancer": ["cv", "dance_reel"],
            "Dancer Who Sings": ["cv", "dance_reel", "vocal_reel"],
            "Singer/Actor": ["cv", "vocal_reel", "acting_reel"]
        }
        
        required_materials = role_materials.get(role_type, [])
        
        for material in required_materials:
            if material == "cv":
                results[material] = MaterialValidator.validate_cv(content)
            else:
                results[material] = MaterialValidator.validate_video_link(content, material)
        
        return results
    
    @staticmethod
    def detect_completion_intent(content: str) -> bool:
        """Detect if user indicates they've completed providing materials."""
        completion_phrases = [
            "that's all", "that's everything", "all done", "finished",
            "complete", "nothing else", "no more", "done",
            "submitted everything", "all materials", "ready to submit"
        ]
        
        content_lower = content.lower()
        return any(phrase in content_lower for phrase in completion_phrases)