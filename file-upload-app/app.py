import logging
import traceback
import os
from flask import Flask, render_template, request, redirect, url_for
import boto3
from werkzeug.utils import secure_filename
from dotenv import load_dotenv  # You can keep this, but it's not strictly necessary now

# load_dotenv()  # You can remove this line if you're not using a .env file

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit (adjust as needed)

# Configure Logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# AWS S3 Client
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    logging.debug("Starting upload function")
    try:
        if 'file' not in request.files:
            logging.debug("No file part in request")
            return redirect(url_for('home'))

        file = request.files['file']
        logging.debug(f"File received: {file.filename}")

        if file.filename == '':
            logging.debug("No file selected for upload")
            return redirect(url_for('home'))

        if request.content_length > app.config['MAX_CONTENT_LENGTH']:
            logging.warning("File size exceeded limit")
            return "File size exceeded limit", 413  # 413 Payload Too Large

        filename = secure_filename(file.filename)
        logging.debug(f"Secure filename: {filename}")

        logging.debug(f"Bucket name: {BUCKET_NAME}")

        try:
            s3.upload_fileobj(file, BUCKET_NAME, filename)
            logging.info(f"File '{filename}' uploaded successfully to S3")
            return redirect(url_for('file_list'))
        except ClientError as e:
            logging.error(f"S3 ClientError: {e}")
            return "Error uploading to S3", 500

    except Exception as e:
        logging.error(f"An error occurred during upload: {e}")
        logging.error(traceback.format_exc())  # Log the full traceback
        return f"An error occurred: {str(e)}", 500

@app.route('/files')
def file_list():
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)
    files = []
    if 'Contents' in response:
        for item in response['Contents']:
            file_info = {
                'name': item['Key'],
                'size': item['Size'],
                'url': f"https://{BUCKET_NAME}.s3.amazonaws.com/{item['Key']}",
                'last_modified': item['LastModified']
            }
            files.append(file_info)
    return render_template('filelist.html', files=files)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Enable debug mode for more info
