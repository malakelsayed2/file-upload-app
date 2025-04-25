from flask import Flask, render_template, request, redirect, url_for
import boto3
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file

app = Flask(__name__)

# AWS S3 Client
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('S3_REGION')
)

BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(url_for('home'))
        
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('home'))
        
    filename = secure_filename(file.filename)
        
    # Upload to S3
    s3.upload_fileobj(
        file,
        BUCKET_NAME,
        filename,
    )
        
    # Redirect to the file list page
    return redirect(url_for('file_list'))

@app.route('/files')
def file_list():
    # Get all objects from the S3 bucket
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)
    
    files = []
    if 'Contents' in response:
        for item in response['Contents']:
            # Create file info dictionary
            file_info = {
                'name': item['Key'],
                'size': format_size(item['Size']),
                'last_modified': item['LastModified'],
                'url': f"https://{BUCKET_NAME}.s3.amazonaws.com/{item['Key']}",
            }
            files.append(file_info)
    files.sort(key=lambda x: x['last_modified'], reverse=True)
    return render_template('filelist.html', files=files)

def format_size(size_bytes):
    # Format file size for display
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


