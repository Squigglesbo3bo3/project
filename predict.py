import tensorflow as tf
import numpy as np
import cv2
import matplotlib.pyplot as plt



model = tf.keras.models.load_model("pneumonia_model.h5")



img_path = r"C:\Users\Squiggles PC\Documents\WhatsApp Image 2026-03-08 at 01.29.44.jpeg"

original = cv2.imread(img_path)
original = cv2.resize(original, (224, 224))

img = original / 255.0
input_img = np.expand_dims(img, axis=0)



prediction = model.predict(input_img)[0][0]

confidence = prediction * 100

threshold = 0.65
if prediction > threshold:
    diagnosis = "Possible Pneumonia"
else:
    diagnosis = "Normal"


base_model = model.get_layer("densenet121")
last_conv_layer = base_model.get_layer("conv5_block16_concat")

grad_model = tf.keras.Model(
    inputs=base_model.input,
    outputs=[
        last_conv_layer.output,
        base_model.output
    ]
)

with tf.GradientTape() as tape:
    conv_outputs, predictions = grad_model(input_img)
    loss = predictions[:, 0]

grads = tape.gradient(loss, conv_outputs)

pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

conv_outputs = conv_outputs[0]

heatmap = tf.reduce_sum(conv_outputs * pooled_grads, axis=-1)

heatmap = np.maximum(heatmap.numpy(), 0)

if np.max(heatmap) != 0:
    heatmap = heatmap / np.max(heatmap)

heatmap = cv2.resize(heatmap, (224, 224))



heatmap_uint8 = np.uint8(255 * heatmap)
heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

overlay = cv2.addWeighted(original, 0.6, heatmap_color, 0.4, 0)



region = None

if prediction > 0.5:
    h, w = heatmap_color.shape[:2]

    left = np.sum(heatmap_color[:, :w//2])
    right = np.sum(heatmap_color[:, w//2:])

    top = np.sum(heatmap_color[:h//2, :])
    bottom = np.sum(heatmap_color[h//2:, :])

    region = ""
    region += "Upper " if top > bottom else "Lower "
    region += "Left Lung" if left > right else "Right Lung"



print("\nDiagnosis Report")
print("----------------------------")

print(f"Patient Status: {diagnosis}")
print(f"Confidence: {confidence:.2f}%")

if region is not None:
    print(f"Affected Region: {region}")

print("\nRecommendation:")

if prediction > 0.5:
    print("Consult a radiologist immediately.")
else:
    print("No pneumonia detected. Maintain regular health checkups.")



plt.figure(figsize=(12, 4))

plt.subplot(1, 3, 1)
plt.title("Original X-ray")
plt.imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
plt.axis("off")

plt.subplot(1, 3, 2)
plt.title("Heatmap")
plt.imshow(heatmap, cmap="jet")
plt.axis("off")

plt.subplot(1, 3, 3)
plt.title("Affected Area")
plt.imshow(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB))
plt.axis("off")

plt.tight_layout()
plt.show()