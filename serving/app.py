"""
If you are in the same directory as this file (app.py), you can run run the app using gunicorn:

    $ gunicorn --bind 0.0.0.0:<PORT> app:app

gunicorn can be installed via:

    $ pip install gunicorn

"""
import os
from logging.handlers import RotatingFileHandler
import logging
from flask import Flask, jsonify, request, abort
import pandas as pd
import joblib
from comet_ml import API
from dotenv import load_dotenv

app = Flask(__name__)

# Setup logging
LOG_FILE = os.environ.get("FLASK_LOG", "flask.log")
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10240, backupCount=10)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

# Setup model directory
current_script_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_script_path)
parent_dir = os.path.dirname(current_dir)
MODEL_DIR = os.path.join(parent_dir, 'data', 'models')
loaded_model = None

# Setup Comet
load_dotenv()
api = API()



@app.route("/logs", methods=["GET"])
def logs():
    """Reads data from the log file and returns them as the response"""
    try:
        with open(LOG_FILE, "r") as file:
            response = file.read()
        return jsonify(response)
    except IOError:
        abort(404, description="Log file not found.")


@app.route("/download_registry_model", methods=["POST"])
def download_registry_model():
    """
    Handles POST requests made to http://IP_ADDRESS:PORT/download_registry_model

    The comet API key should be retrieved from the ${COMET_API_KEY} environment variable.

    Recommend (but not required) json with the schema:

        {
            workspace: (required),
            model: (required),
            version: (required),
            ... (other fields if needed) ...
        }

    """
    global loaded_model

    # Get POST json data
    json = request.get_json()
    app.logger.info(json)

    model_name = json['model']
    workspace = json['workspace']
    version = json['version']

    model_path = MODEL_DIR+'\\'+model_name+'.joblib'

    if os.path.exists(model_path):  # replace with actual check
        app.logger.info("Model already downloaded.")
        loaded_model = joblib.load(model_path) # load model from joblib file
        return jsonify({"status": "Model already downloaded."})



    try:
        api.download_registry_model(workspace=workspace, registry_name=model_name, version=version,
                                    output_path=MODEL_DIR, expand=True)
        loaded_model = joblib.load(model_path)

        app.logger.info("Model downloaded and loaded successfully.")
        return jsonify({"status": "Model downloaded and loaded successfully."})
    except Exception as e:
        app.logger.error(f"Failed to download model: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/predict", methods=["POST"])
def predict():
    """
    Handles POST requests made to http://IP_ADDRESS:PORT/predict

    Returns predictions
    """
    if not loaded_model:
        abort(503, description="Model not loaded.")
    # Get POST json data
    data = request.get_json()
    app.logger.info(data)
    try:
        # Convert data to appropriate format for the model
        # For example, if your model expects a pandas DataFrame:
        if 'columns' in data and 'data' in data:
            # Create DataFrame from JSON
            df = pd.DataFrame(data['data'], columns=data['columns']).values
        else:
            return jsonify({"error": "Invalid data format"}), 400
        # Perform prediction
        prediction = loaded_model.predict(df)

        return jsonify({"prediction": prediction.tolist()})
    except Exception as e:
        app.logger.error(f"Error during prediction: {e}")
        return jsonify({"error": str(e)}), 500