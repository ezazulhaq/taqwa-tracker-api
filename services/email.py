import httpx
from config.email import config

class EmailService:
    
    @staticmethod
    async def send_email_with_resend(
        to_email: str,
        subject: str,
        html_content: str
    ) -> bool:
        """
        Send email using Resend API
        """
        if not config.api_key:
            print("⚠️ WARNING: API_KEY not configured. Email not sent.")
            return False
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {config.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": config.from_email,
                        "to": [to_email],
                        "bcc": "ezazulhaq.it@gmail.com",
                        "subject": subject,
                        "html": html_content
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    print(f"✅ Email sent successfully to {to_email}")
                    return True
                else:
                    print(f"❌ Failed to send email: {response.status_code} - {response.text}")
                    return False
                    
            except httpx.RequestError as e:
                print(f"❌ Email sending error: {str(e)}")
                return False

    @staticmethod
    def get_verification_email_html(verification_link: str, user_name: str) -> str:
        """
        Generate HTML for email verification email
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Welcome to {config.app_name}!</h1>
            </div>
            
            <div style="background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px;">Hi {user_name or "there"},</p>
                
                <p style="font-size: 16px;">
                    Thank you for signing up! Please verify your email address to complete your registration.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_link}" 
                    style="background-color: #667eea; color: white; padding: 14px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666;">
                    Or copy and paste this link in your browser:<br>
                    <a href="{verification_link}" style="color: #667eea; word-break: break-all;">{verification_link}</a>
                </p>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    This link will expire in 24 hours for security reasons.
                </p>
                
                <p style="font-size: 14px; color: #666;">
                    If you didn't create an account with {config.app_name}, you can safely ignore this email.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2025 {config.app_name}. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def get_password_reset_email_html(reset_link: str, user_name: str) -> str:
        """
        Generate HTML for password reset email
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Password Reset Request</h1>
            </div>
            
            <div style="background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px;">Hi {user_name or "there"},</p>
                
                <p style="font-size: 16px;">
                    We received a request to reset your password for your {config.app_name} account.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" 
                    style="background-color: #f5576c; color: white; padding: 14px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666;">
                    Or copy and paste this link in your browser:<br>
                    <a href="{reset_link}" style="color: #f5576c; word-break: break-all;">{reset_link}</a>
                </p>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    This link will expire in 1 hour for security reasons.
                </p>
                
                <p style="font-size: 14px; color: #666;">
                    If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2025 {config.app_name}. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def get_welcome_email_html(user_name: str) -> str:
        """
        Generate HTML for welcome email after verification
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">🎉 You're All Set!</h1>
            </div>
            
            <div style="background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px;">Hi {user_name or "there"},</p>
                
                <p style="font-size: 16px;">
                    Your email has been verified successfully! Welcome to {config.app_name}.
                </p>
                
                <p style="font-size: 16px;">
                    You can now enjoy all the features of your account.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{config.front_end_url}" 
                    style="background-color: #4facfe; color: white; padding: 14px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Get Started
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666;">
                    If you have any questions, feel free to reach out to our support team.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2025 {config.app_name}. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
