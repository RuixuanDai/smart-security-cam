from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import io
import re
import time
from annotation import Annotator
from picamera import PiCamera
from time import sleep,perf_counter_ns
from sys import exit

from tflite_runtime.interpreter import Interpreter, load_delegate

import numpy as np
from PIL import Image
import cloud_functions as cf
from datetime import datetime
import time

# Using globals, may refactor to passing args
args = None
camera = None
interpreter = None
annotator = None
labels = None
stream = None # This is especially problematic style wise, its dynamic
input_width = None
input_height = None
alert_meta = {"type": None, "confidence": 0.0, "time": None}
last_alert = None # Same here
debounce_time = 0.3*(10**9)

# Camera Config
CAMERA_HEIGHT = 240
CAMERA_WIDTH = round(CAMERA_HEIGHT*1.33)

# FSM Constants
LOCAL_NEGATIVE = 1
LOCAL_POSITIVE = 2
LOCAL_UNCERTAIN = 3
ALERT_COMPLETE = 4
CLOUD_INFERENCE_COMPLETE = 5

LOCAL_ALERT = 9
CLOUD_ALERT = 10


def local_inference_state():

    global alert_meta

    camera.capture(stream, format='jpeg')

    stream.seek(0)

    image = Image.open(stream).convert('RGB').resize((input_width, input_height), Image.ANTIALIAS)
    start_time = perf_counter_ns()
    results = detect_objects(interpreter, image, args['base_thresh'])
    elapsed_ns = perf_counter_ns() - start_time
    print("Local inference (ns): ", format(elapsed_ns, '.3e'))  # CPU nano seconds elapsed (floating point)

    annotator.clear()
    annotate_objects(annotator, results, labels)
    annotator.text([5, 0], '%.1fms' % (elapsed_ns * (1000000 ** -1)))
    annotator.update()

    for obj in results:
        if labels[obj['class_id']] == 'person':

            if obj['score'] >= args["local_thresh"]:
                stream.seek(0)
                stream.truncate()
                alert_meta["type"] = LOCAL_ALERT
                alert_meta["confidence"] = obj['score']
                return LOCAL_POSITIVE
            else:
                return LOCAL_UNCERTAIN

    stream.seek(0)
    stream.truncate()
    return LOCAL_NEGATIVE


def cloud_inference_state():
    global args

    stream.seek(0)
    cf.AWS_detect_labels(stream, args["cloud_thresh"])
    stream.seek(0)
    stream.truncate()
    return CLOUD_INFERENCE_COMPLETE


def alert_state():

    global last_alert
    global alert_meta
    global annotator
    global debounce_time

    print("ALERT!!!")

    annotator.text([100, 100], 'INTRUDER DETECTED', alert=True)
    annotator.update()

    stamp = datetime.fromtimestamp(time.time())

    if (perf_counter_ns() - last_alert) > debounce_time:

        alert_meta["time"] = stamp.strftime("%m-%d-%Y %H:%M:%S")
        cf.send_Alert_Email("INTRUDER ALERT "+str(alert_meta))

        last_alert = perf_counter_ns()

    return ALERT_COMPLETE

    # print("ABORTING")
    # camera.stop_preview()
    # exit()


# FSM Switch
state_switch = {
    LOCAL_NEGATIVE: local_inference_state,
    LOCAL_POSITIVE: alert_state,
    LOCAL_UNCERTAIN: cloud_inference_state,
    ALERT_COMPLETE: local_inference_state,
    CLOUD_INFERENCE_COMPLETE: local_inference_state
}



def load_labels(path):
  """Loads the labels file. Supports files with or without index numbers."""
  with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    labels = {}
    for row_number, content in enumerate(lines):
      pair = re.split(r'[:\s]+', content.strip(), maxsplit=1)
      if len(pair) == 2 and pair[0].strip().isdigit():
        labels[int(pair[0])] = pair[1].strip()
      else:
        labels[row_number] = pair[0].strip()
  return labels


def set_input_tensor(interpreter, image):
  """Sets the input tensor."""
  tensor_index = interpreter.get_input_details()[0]['index']
  input_tensor = interpreter.tensor(tensor_index)()[0]
  input_tensor[:, :] = image


def get_output_tensor(interpreter, index):
  """Returns the output tensor at the given index."""
  output_details = interpreter.get_output_details()[index]
  tensor = np.squeeze(interpreter.get_tensor(output_details['index']))
  return tensor


def detect_objects(interpreter, image, threshold):
  """Returns a list of detection results, each a dictionary of object info."""
  set_input_tensor(interpreter, image)

  # start_time = perf_counter_ns()
  interpreter.invoke()
  # elapsed_ns = perf_counter_ns() - start_time
  # print("Interpreter Invocation (ns): ", format(elapsed_ns, '.3e'))  # CPU nano seconds elapsed (floating point)

  # Get all output details
  boxes = get_output_tensor(interpreter, 0)
  classes = get_output_tensor(interpreter, 1)
  scores = get_output_tensor(interpreter, 2)
  count = int(get_output_tensor(interpreter, 3))

  results = []
  for i in range(count):
    if scores[i] >= threshold:
      result = {
          'bounding_box': boxes[i],
          'class_id': classes[i],
          'score': scores[i]
      }
      results.append(result)
  return results


def annotate_objects(annotator, results, labels):
  """Draws the bounding box and label for each object in the results."""
  for obj in results:
    # Convert the bounding box figures from relative coordinates
    # to absolute coordinates based on the original resolution
    ymin, xmin, ymax, xmax = obj['bounding_box']
    xmin = int(xmin * CAMERA_WIDTH)
    xmax = int(xmax * CAMERA_WIDTH)
    ymin = int(ymin * CAMERA_HEIGHT)
    ymax = int(ymax * CAMERA_HEIGHT)

    # Overlay the box, label, and score on the camera preview
    annotator.bounding_box([xmin, ymin, xmax, ymax])
    annotator.text([xmin, ymin],
                   '%s\n%.2f' % (labels[obj['class_id']], obj['score']))


def main():

    global args
    global camera
    global interpreter
    global annotator
    global labels
    global stream
    global input_width
    global input_height
    global last_alert

    new_state = LOCAL_NEGATIVE
    last_alert = perf_counter_ns()

    iters = 0
    limit = 80

    t0 = perf_counter_ns()
    print("Starting!")

    args = {}

    # args['model'] = 'model/detect.tflite'
    args['model'] = 'model/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite'

    args['labels'] = 'model/coco_labels.txt'
    args['base_thresh'] = 0.5
    args['local_thresh'] = 0.68
    args['cloud_thresh'] = 90

    labels = load_labels(args['labels'])

    # interpreter = Interpreter(args['model'])
    interpreter = Interpreter(args['model'],
                              experimental_delegates=[load_delegate('libedgetpu.so.1.0')])

    interpreter.allocate_tensors()
    _, input_height, input_width, _ = interpreter.get_input_details()[0]['shape']

    camera = PiCamera(resolution=(CAMERA_WIDTH, CAMERA_HEIGHT), framerate=30)
    camera.start_preview()

    stream = io.BytesIO()
    annotator = Annotator(camera)

    while iters < limit:
    # while True:

        curr_state_func = state_switch[new_state]
        new_state = curr_state_func()

        iters += 1

    t1 = perf_counter_ns()
    print("State switches: ",iters)
    delta = t1 - t0
    print("CPU time elapsed (ns): ", format(delta, '.3e'))  # CPU nano seconds elapsed (floating point)
    print("Avg ns/state: ",format(delta/iters, '.1f'))

if __name__ == '__main__':
    main()
