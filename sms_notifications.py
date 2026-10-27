import os
from twilio.rest import Client

# Get Twilio credentials from environment variables
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")


def send_disruption_alert(to_phone_number: str, supplier_name: str, 
                         disruption_type: str, category: str) -> dict:
    """
    Send an SMS alert about a supply chain disruption
    
    Args:
        to_phone_number: The recipient's phone number (E.164 format)
        supplier_name: Name of the supplier experiencing the disruption
        disruption_type: Type of disruption (e.g., "Supply chain delay")
        category: Equipment category affected
    
    Returns:
        Dictionary with status of SMS send operation and any error messages
    """
    # Check if Twilio credentials are available
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        return {
            "success": False,
            "error": "Missing Twilio credentials. Please set the TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER environment variables."
        }
    
    try:
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Format the message
        message_body = (
            f"⚠️ SUPPLY CHAIN DISRUPTION ALERT\n\n"
            f"Supplier: {supplier_name}\n"
            f"Category: {category}\n"
            f"Issue: {disruption_type}\n\n"
            f"Please check the Supply Chain Disruption Simulator for more details."
        )
        
        # Send the SMS
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        
        return {
            "success": True,
            "message_sid": message.sid,
            "status": message.status
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def send_solution_notification(to_phone_number: str, supplier_name: str, 
                               solution: str, category: str) -> dict:
    """
    Send an SMS notification about a solution implementation
    
    Args:
        to_phone_number: The recipient's phone number (E.164 format)
        supplier_name: Name of the supplier
        solution: Applied solution
        category: Equipment category affected
    
    Returns:
        Dictionary with status of SMS send operation and any error messages
    """
    # Check if Twilio credentials are available
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        return {
            "success": False,
            "error": "Missing Twilio credentials. Please set the TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER environment variables."
        }
    
    try:
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Format the message
        message_body = (
            f"✅ SUPPLY CHAIN SOLUTION IMPLEMENTED\n\n"
            f"Supplier: {supplier_name}\n"
            f"Category: {category}\n"
            f"Solution: {solution}\n\n"
            f"Supply chain operations are being restored. Check the Supply Chain Disruption Simulator for current status."
        )
        
        # Send the SMS
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        
        return {
            "success": True,
            "message_sid": message.sid,
            "status": message.status
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }