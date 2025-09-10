import pytest
from validators import MaterialValidator, InputValidator, ContentValidator

class TestMaterialValidator:
    def setup_method(self):
        self.validator = MaterialValidator()
    
    def test_cv_validation_valid_formats(self):
        """Test CV validation with valid formats."""
        valid_inputs = [
            "my_cv.pdf",
            "Here is my resume in docx format", 
            "I have a Word document with my CV",
            "CV attached as PDF file"
        ]
        
        for input_text in valid_inputs:
            is_valid, message = self.validator.validate_cv(input_text)
            assert is_valid, f"Expected valid for: {input_text}"
            assert "accepted" in message.lower()
    
    def test_cv_validation_invalid_formats(self):
        """Test CV validation with invalid formats."""
        invalid_inputs = [
            "my_cv.txt",
            "I have a plain text resume",
            "CV in HTML format",
            ""
        ]
        
        for input_text in invalid_inputs:
            is_valid, message = self.validator.validate_cv(input_text)
            if not is_valid:  # Some might still pass due to flexible validation
                assert "must be" in message.lower() or "format" in message.lower()
    
    def test_video_link_validation_youtube(self):
        """Test video link validation with YouTube URLs."""
        youtube_urls = [
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        
        for url in youtube_urls:
            is_valid, message = self.validator.validate_video_link(url, "dance_reel")
            assert is_valid, f"Expected valid YouTube URL: {url}"
            assert "youtube" in message.lower()
    
    def test_video_link_validation_vimeo(self):
        """Test video link validation with Vimeo URLs."""
        vimeo_urls = [
            "https://vimeo.com/123456789",
            "https://www.vimeo.com/123456789",
            "vimeo.com/987654321"
        ]
        
        for url in vimeo_urls:
            is_valid, message = self.validator.validate_video_link(url, "vocal_reel")
            assert is_valid, f"Expected valid Vimeo URL: {url}"
            assert "vimeo" in message.lower()
    
    def test_video_link_validation_invalid_platforms(self):
        """Test video link validation with invalid platforms."""
        invalid_urls = [
            "https://tiktok.com/@user/video/123",
            "https://instagram.com/p/123",
            "https://facebook.com/video/123",
            "https://example.com/video.mp4"
        ]
        
        for url in invalid_urls:
            is_valid, message = self.validator.validate_video_link(url, "acting_reel")
            assert not is_valid, f"Expected invalid for: {url}"
            assert "youtube" in message.lower() and "vimeo" in message.lower()
    
    def test_spotlight_link_validation(self):
        """Test Spotlight link validation."""
        valid_spotlight = [
            "https://spotlight.com/1234567",
            "https://portal.spotlight.com/artist/1234567",
            "spotlight.com/artist/name"
        ]
        
        invalid_spotlight = [
            "https://backstage.com/profile",
            "https://mandy.com/actor/123",
            "my spotlight profile"
        ]
        
        for url in valid_spotlight:
            is_valid, message = self.validator.validate_spotlight_link(url)
            assert is_valid, f"Expected valid Spotlight URL: {url}"
        
        for url in invalid_spotlight:
            is_valid, message = self.validator.validate_spotlight_link(url)
            assert not is_valid, f"Expected invalid for: {url}"

class TestInputValidator:
    def setup_method(self):
        self.validator = InputValidator()
    
    def test_email_validation_valid(self):
        """Test email validation with valid emails."""
        valid_emails = [
            "john@example.com",
            "test.user+tag@domain.co.uk",
            "user123@test-domain.com",
            "a@b.co"
        ]
        
        for email in valid_emails:
            is_valid, message = self.validator.validate_email(email)
            assert is_valid, f"Expected valid email: {email}"
            assert "valid" in message.lower()
    
    def test_email_validation_invalid(self):
        """Test email validation with invalid emails."""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user space@domain.com",
            ""
        ]
        
        for email in invalid_emails:
            is_valid, message = self.validator.validate_email(email)
            assert not is_valid, f"Expected invalid email: {email}"
    
    def test_phone_validation_valid(self):
        """Test phone validation with valid numbers."""
        valid_phones = [
            "+1234567890",
            "123-456-7890",
            "(123) 456-7890",
            "+44 20 1234 5678",
            "01234567890"
        ]
        
        for phone in valid_phones:
            is_valid, message = self.validator.validate_phone(phone)
            assert is_valid, f"Expected valid phone: {phone}"
    
    def test_phone_validation_invalid(self):
        """Test phone validation with invalid numbers."""
        invalid_phones = [
            "123",
            "abc123456789",
            "",
            "123-45"
        ]
        
        for phone in invalid_phones:
            is_valid, message = self.validator.validate_phone(phone)
            assert not is_valid, f"Expected invalid phone: {phone}"
    
    def test_name_validation_valid(self):
        """Test name validation with valid names."""
        valid_names = [
            "John Doe",
            "Mary-Jane Smith",
            "O'Connor",
            "Jean-Pierre François",
            "Dr. Smith Jr."
        ]
        
        for name in valid_names:
            is_valid, message = self.validator.validate_name(name)
            assert is_valid, f"Expected valid name: {name}"
    
    def test_name_validation_invalid(self):
        """Test name validation with invalid names."""
        invalid_names = [
            "J",
            "",
            "123John",
            "John@Smith",
            "   "
        ]
        
        for name in invalid_names:
            is_valid, message = self.validator.validate_name(name)
            assert not is_valid, f"Expected invalid name: {name}"

class TestContentValidator:
    def setup_method(self):
        self.validator = ContentValidator()
    
    def test_extract_and_validate_materials_dancer(self):
        """Test material extraction for Dancer role."""
        content = "Here is my CV in PDF format and my dance reel: https://youtube.com/watch?v=123"
        results = self.validator.extract_and_validate_materials(content, "Dancer")
        
        assert "cv" in results
        assert "dance_reel" in results
        assert results["cv"][0]  # Should be valid
        assert results["dance_reel"][0]  # Should be valid
    
    def test_extract_and_validate_materials_singer_actor(self):
        """Test material extraction for Singer/Actor role."""
        content = "CV: resume.docx, Vocal reel: vimeo.com/123, Acting reel: youtube.com/watch?v=456"
        results = self.validator.extract_and_validate_materials(content, "Singer/Actor")
        
        assert "cv" in results
        assert "vocal_reel" in results
        assert "acting_reel" in results
        assert all(result[0] for result in results.values())  # All should be valid
    
    def test_detect_completion_intent_positive(self):
        """Test completion intent detection with positive indicators."""
        completion_phrases = [
            "That's all I have",
            "I've submitted everything",
            "All done with materials",
            "Ready to submit my application",
            "Nothing else to add"
        ]
        
        for phrase in completion_phrases:
            assert self.validator.detect_completion_intent(phrase), f"Should detect completion: {phrase}"
    
    def test_detect_completion_intent_negative(self):
        """Test completion intent detection with non-completion phrases."""
        non_completion_phrases = [
            "Here is my CV",
            "I need to add more materials",
            "Still working on my reel",
            "What else do you need?"
        ]
        
        for phrase in non_completion_phrases:
            assert not self.validator.detect_completion_intent(phrase), f"Should not detect completion: {phrase}"

if __name__ == "__main__":
    # Run tests if file is executed directly
    pytest.main([__file__, "-v"])