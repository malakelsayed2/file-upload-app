from flask import Flask, render_template, request, redirect, url_for
import boto3
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Manually set your AWS credentials and region here
aws_access_key_id = 'AKIA5WLTTN3S3K7TUKPH'
aws_secret_access_key = 'Kx9ZxOSFHQbOhfw3cbyjsMpTpYfpylFxtE+T5tvp'
region_name = 'us-east-1'  # e.g., 'us-east-1'
bucket_name = 'your-s3-bucket-name'

# AWS S3 Client
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)

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
        bucket_name,
        filename,
    )
        
    # Redirect to the file list page
    return redirect(url_for('file_list'))

@app.route('/files')
def file_list():
    # Get all objects from the S3 bucket
    response = s3.list_objects_v2(Bucket=bucket_name)
    
    files = []
    if 'Contents' in response:
        for item in response['Contents']:
            # Create file info dictionary
            file_info = {
                'name': item['Key'],
                'size': format_size(item['Size']),
                'last_modified': item['LastModified'],
                'url': f"https://{bucket_name}.s3.amazonaws.com/{item['Key']}",
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
