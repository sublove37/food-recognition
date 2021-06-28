from genericpath import exists
from PIL import Image
from flask import Flask, request, Response, jsonify, send_from_directory, abort, render_template
from io import BytesIO
import aiohttp
import asyncio
import sys
import os
import imageio
import argparse
import requests
import cv2
import numpy as np
from pathlib import Path
from werkzeug.utils import secure_filename
from modules import get_prediction
import hashlib
from flask_ngrok import run_with_ngrok

parser = argparse.ArgumentParser('YOLOv5 Online Food Recognition')
parser.add_argument('--type', type=str, default='local', help="Run on local or ngrok")
parser.add_argument('--host',  type=str, default='192.168.100.4', help="Local IP")



app = Flask(__name__, template_folder='templates', static_folder='assets')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
UPLOAD_FOLDER = './assets/uploads'
DETECTION_FOLDER = './assets/detections'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DETECTION_FOLDER'] = DETECTION_FOLDER

path = Path(__file__).parent


@app.route('/')
def homepage():
    # html_file = path / 'template' / 'index.html'
    # print(html_file)
    return render_template("index.html")


@app.route('/analyze', methods=['POST'])
def analyze():
    f = request.files['file']

    ori_file_name = secure_filename(f.filename)
    _, ext = os.path.splitext(ori_file_name)

    # Get cache name by hashing image
    data = f.read()
    filename = hashlib.md5(data).hexdigest() + f'{ext}'
    
    # save file to /static/uploads
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    np_img = np.fromstring(data, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    cv2.imwrite(filepath, img)

    # predict image
    output_path=os.path.join(app.config['DETECTION_FOLDER'], filename)
    filename2, result_dict = get_prediction(
        filepath, 
        output_path, 
        model_name="yolov5m",
        ensemble=False,
        min_conf=0.5,
        min_iou=0.65)

    return render_template("detect.html", fname=filename, fname2=filename, result_dict=result_dict)

@app.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    if not os.path.exists(DETECTION_FOLDER):
        os.makedirs(DETECTION_FOLDER, exist_ok=True)

    args = parser.parse_args()

    if args.type == 'ngrok':
        run_with_ngrok(app)
    else:
        app.run(host=args.host, port=4000, debug=True)
