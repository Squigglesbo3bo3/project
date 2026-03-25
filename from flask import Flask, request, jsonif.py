from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from PIL import Image
import numpy as np
import io

app = Flask(__name__)
CORS(app)

model = tf.keras.models.load_model('pneumonia_model.h5')

def prepare_image(img):
    img = img.resize((224, 224))
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
        
    file = request.files['image']
    img = Image.open(io.BytesIO(file.read())).convert('RGB')
    processed_img = prepare_image(img)
    
    prediction = model.predict(processed_img)
    
    probability = float(prediction[0][0])
    result = "Pneumonia" if probability > 0.5 else "Normal"
    confidence = probability if result == "Pneumonia" else 1 - probability
    
    return jsonify({
        'status': result,
        'confidence': f"{confidence*100:.2f}%"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)