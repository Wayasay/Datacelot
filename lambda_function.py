import json
import boto3
from botocore.exceptions import ClientError
from urllib.parse import parse_qs
import uuid
from datetime import datetime

def lambda_handler(event, context):
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS, GET'
    }
    
    try:
        http_method = event.get('httpMethod', 'POST')
        
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
        elif http_method == 'GET':
            return get_contact_form(headers)
        elif http_method == 'POST':
            return process_contact_form(event, headers)
        else:
            return {
                'statusCode': 405,
                'headers': headers,
                'body': json.dumps({'error': 'Method not allowed'})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def get_contact_form(headers):
    # Return simple contact form HTML
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Contact Form</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h2>Contact Us</h2>
        <form method="POST">
            <div class="form-group">
                <label for="name">Name *</label>
                <input type="text" id="name" name="name" required>
            </div>
            <div class="form-group">
                <label for="email">Email *</label>
                <input type="email" id="email" name="email" required>
            </div>
            <div class="form-group">
                <label for="phone">Phone</label>
                <input type="tel" id="phone" name="phone">
            </div>
            <div class="form-group">
                <label for="message">Message *</label>
                <textarea id="message" name="message" rows="5" required></textarea>
            </div>
            <button type="submit">Send Message</button>
        </form>
    </body>
    </html>
    """
    
    return {
        'statusCode': 200,
        'headers': {**headers, 'Content-Type': 'text/html'},
        'body': html_content
    }

def process_contact_form(event, headers):
    # Parse form data
    content_type = event.get('headers', {}).get('content-type', '').lower()
    
    if 'application/json' in content_type:
        # JSON data from API call
        body = json.loads(event['body'])
    else:
        # Form data from HTML form
        form_data = parse_qs(event['body'])
        body = {key: value[0] for key, value in form_data.items()}
    
    # Extract fields
    name = body.get('name', '').strip()
    email = body.get('email', '').strip()
    phone = body.get('phone', '').strip()
    message = body.get('message', '').strip()
    
    # Validate required fields
    if not name or not email or not message:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'message': 'Name, email, and message are required'
            })
        }
    
    # Insert into DynamoDB
    try:
        submission_id = insert_contact_record(name, email, phone, message)
        
        # Return success page or JSON
        if 'application/json' in content_type:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'message': 'Message sent successfully',
                    'submissionId': submission_id
                })
            }
        else:
            # Return success HTML
            success_html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Message Sent</title></head>
            <body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
                <h2>Thank You!</h2>
                <p>Your message has been sent successfully.</p>
                <p><strong>Submission ID:</strong> {submission_id}</p>
                <a href="javascript:history.back()">← Go Back</a>
            </body>
            </html>
            """
            return {
                'statusCode': 200,
                'headers': {**headers, 'Content-Type': 'text/html'},
                'body': success_html
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'success': False, 'message': f'Database error: {str(e)}'})
        }

def insert_contact_record(name, email, phone, message):
    # Store in DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
    table = dynamodb.Table('ContactFormSubmissions')
    
    submission_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    table.put_item(
        Item={
            'SubmissionId': submission_id,
            'Timestamp': timestamp,
            'Name': name,
            'Email': email,
            'Phone': phone or 'Not provided',
            'Message': message,
            'Status': 'New'
        }
    )
    
    # Send email notification
    send_email_notification(submission_id, name, email, phone, message, timestamp)
    
    return submission_id

def send_email_notification(submission_id, name, email, phone, message, timestamp):
    ses_client = boto3.client('ses', region_name='eu-north-1')
    
    RECIPIENT_EMAIL = 'f.okoye@icloud.com'
    SOURCE_EMAIL = 'f.okoye@icloud.com'
    
    # Email content
    subject = f"New Contact Form Submission from {name}"
    
    email_body = f"""
New contact form submission received:

Submission Details:
- Submission ID: {submission_id}
- Timestamp: {timestamp}
- Name: {name}
- Email: {email}
- Phone: {phone or 'Not provided'}

Message:
{message}

You can reply directly to this email to respond to {name}.
View all submissions in your DynamoDB table: ContactFormSubmissions
    """
    
    html_body = f"""
    <html>
    <body>
        <h2>New Contact Form Submission</h2>
        
        <h3>Submission Details:</h3>
        <table border="1" style="border-collapse: collapse; padding: 10px;">
            <tr><td><strong>Submission ID:</strong></td><td>{submission_id}</td></tr>
            <tr><td><strong>Timestamp:</strong></td><td>{timestamp}</td></tr>
            <tr><td><strong>Name:</strong></td><td>{name}</td></tr>
            <tr><td><strong>Email:</strong></td><td><a href="mailto:{email}">{email}</a></td></tr>
            <tr><td><strong>Phone:</strong></td><td>{phone or 'Not provided'}</td></tr>
        </table>
        
        <h3>Message:</h3>
        <p style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #007bff;">
            {message.replace(chr(10), '<br>')}
        </p>
        
        <hr>
        <p><em>You can reply directly to this email to respond to {name}.</em></p>
        <p><small>View all submissions in your DynamoDB table: ContactFormSubmissions</small></p>
    </body>
    </html>
    """
    
    try:
        response = ses_client.send_email(
            Destination={'ToAddresses': [RECIPIENT_EMAIL]},
            Message={
                'Body': {
                    'Text': {'Data': email_body},
                    'Html': {'Data': html_body}
                },
                'Subject': {'Data': subject}
            },
            Source=SOURCE_EMAIL,
            ReplyToAddresses=[email]  # Allows direct reply to the submitter
        )
        print(f"Email sent successfully. MessageId: {response['MessageId']}")
        return response['MessageId']
        
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        # Don't fail the whole function if email fails
        return None