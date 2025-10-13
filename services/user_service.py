from typing import Optional

from fastapi import Header


class UserService:
    
    def get_user_from_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
        """Extract user ID from Supabase JWT token if provided"""
        if not authorization or not authorization.startswith("Bearer "):
            return None
        
        token = authorization.split(" ")[1]
        try:
            user = supabase.auth.get_user(token)
            return user.user.id if user.user else None
        except:
            return None