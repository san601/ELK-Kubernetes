from flask import Flask, request
from elasticapm.contrib.flask import ElasticAPM
import logging
from logging.handlers import RotatingFileHandler
import os

app = Flask(__name__)

# Replace this with your actual ELK server IP
app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': 'my-windows-flask-app',
    'SECRET_TOKEN': '',  # Add if your APM server uses one
    'SERVER_URL': 'http://127.0.0.1:8200',
    'ENVIRONMENT': 'development',
}

apm = ElasticAPM(app)

log_dir = r"D:\elk_apm_test_flask\log_dir"
os.makedirs(log_dir, exist_ok=True)

log_file_path = os.path.join(log_dir, "flask_access.log")

# Setup rotating file handler (max 10 MB per file, keep 5 backups)
handler = RotatingFileHandler(log_file_path, maxBytes=10*1024*1024, backupCount=5)
handler.setLevel(logging.INFO)

# Log format - can be JSON or plain text
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)

app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

@app.after_request
def log_request(response):
    # Customize log line: IP, method, path, status code
    log_line = f'{request.remote_addr} - [{request.method}] {request.path} {response.status_code}'
    app.logger.info(log_line)
    return response

@app.route('/')
def home():
    return 'Hello from Flask with APM!'

@app.route('/error')
def error():
    raise ValueError("Intentional error for testing APM")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
