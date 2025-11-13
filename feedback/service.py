from sqlmodel import Session, select
from feedback.entity import Feedback
from feedback.model import FeedbackRequest, FeedbackResponse
from shared.email import EmailService


class FeedbackService:
    
    async def create_feedback(self, feedback_request: FeedbackRequest, session: Session) -> FeedbackResponse:
        """Create feedback and send notification email"""
        
        # Save feedback to database
        feedback = Feedback(
            user_id=feedback_request.user_id,
            content=feedback_request.content,
            category=feedback_request.category,
            email=str(feedback_request.email)
        )
        
        session.add(feedback)
        session.commit()
        session.refresh(feedback)
        
        # Send confirmation email
        email_sent = await EmailService.send_email_with_resend(
            to_email=str(feedback_request.email),
            subject="Feedback Received - Thank You!",
            html_content=self._get_feedback_confirmation_html(feedback_request.content)
        )
        
        # Update email_sent status
        if email_sent:
            db_feedback = session.get(Feedback, feedback.id)
            if db_feedback:
                db_feedback.email_sent = True
                session.commit()
        
        return FeedbackResponse(
            id=feedback.id,
            message="Feedback submitted successfully",
            email_sent=email_sent
        )
    
    def _get_feedback_confirmation_html(self, content: str) -> str:
        """Generate HTML for feedback confirmation email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Thank You for Your Feedback!</h1>
            </div>
            
            <div style="background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px;">Thank you for taking the time to share your feedback with us.</p>
                
                <p style="font-size: 16px;">We have received your message and our team will review it carefully.</p>
                
                <div style="background-color: #e8f4fd; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p style="font-size: 14px; color: #666; margin: 0;"><strong>Your feedback:</strong></p>
                    <p style="font-size: 14px; margin: 10px 0 0 0;">{content[:200]}{'...' if len(content) > 200 else ''}</p>
                </div>
                
                <p style="font-size: 14px; color: #666;">
                    Your input helps us improve our services and better serve the Muslim community.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2025 Taqwa Tracker. All rights reserved.</p>
            </div>
        </body>
        </html>
        """