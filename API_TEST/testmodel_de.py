from keras.models import load_model
import sys
import numpy as np
import glob
import os
import matplotlib.image as img
import matplotlib.pyplot as plt
import cv2
import airsim

if ('PythonClient/' not in sys.path):
    sys.path.insert(0, 'PythonClient/')

# from AirSimClient import *

# << Set this to the path of the model >>
# If None, then the model with the lowest validation loss from training will be used
MODEL_PATH = None
if (MODEL_PATH == None):
    models = glob.glob('model/models/*.h5')
    best_model = max(models, key=os.path.getctime)
    MODEL_PATH = best_model

print('Using model {0} for testing.'.format(MODEL_PATH))

model = load_model(MODEL_PATH)
client = airsim.CarClient()
client.confirmConnection()
client.enableApiControl(True)
car_controls = airsim.CarControls()
print('Connection established!')

car_controls.steering = 0
car_controls.throttle = 0
car_controls.brake = 0

image_buf = np.zeros((1, 59, 255, 3))
state_buf = np.zeros((1, 4))
print("* image_buf.shape ", image_buf.shape)
print("* state_buf.shape: ", state_buf.shape)
print("")

def get_image():
    # uncompressed RGB array bytes
    # image_responses = client.simGetImages([ImageRequest(0, airsim.ImageType.Scene, False, False)])#[0]
    image_responses = client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)])
    image_response = image_responses[0]
    png_image = client.simGetImage("0", airsim.ImageType.Scene)

    print("* image_response.height : ", image_response.height)
    print("* image_response.width : ", image_response.width)
    print("* len(image_response.image_data_uint8) : ", len(image_response.image_data_uint8))
    print("")

    image1d = np.fromstring(image_response.image_data_uint8, dtype=np.uint8)

    print("* image1d: ", image1d)
    print("* image1d.shape: ", image1d.shape)
    print("")
    image_rgb = image1d.reshape(image_response.height, image_response.width, 3)
    print("* image_rgb: ", image_rgb.shape)
    return image_rgb[76:135, 0:255, 0:3].astype(float)

# get_image()
car_state = client.getCarState()
image_buf[0] = get_image()
state_buf[0] = np.array([car_controls.steering, car_controls.throttle, car_controls.brake, car_state.speed])
print("* image_buf[0]: ", image_buf[0])
print("* state_buf[0]: ", state_buf[0])
print("")

model_output = model.predict([image_buf, state_buf])

while (True):
    car_state = client.getCarState()
    if (car_state.speed < 5):
        car_controls.throttle = 1.0
    else:
        car_controls.throttle = 0.0

    image_buf[0] = get_image()
    state_buf[0] = np.array([car_controls.steering-3, car_controls.throttle, car_controls.brake, car_state.speed])
    model_output = model.predict([image_buf, state_buf])
    car_controls.steering = round(0.5 * float(model_output[0][0]), 2)

    print('Sending steering = {0}, throttle = {1}'.format(car_controls.steering, car_controls.throttle))

    client.setCarControls(car_controls)