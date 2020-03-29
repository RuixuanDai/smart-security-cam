from picamera import PiCamera
from time import sleep,perf_counter_ns
from sys import exit
import tflite_runtime.interpreter as tflite

# interpreter = tflite.Interpreter(model_path=args.model_file)

CAMERA_WIDTH, CAMERA_HEIGHT = 640, 480

camera = PiCamera(resolution=(CAMERA_WIDTH, CAMERA_HEIGHT), framerate=30)


def capture_state():
    print("Capturing")
    global camera
    sleep(1)
    return NEW_CAM_DATA


def local_inference_state():
    print("Local Inference")
    sleep(1)
    return LOCAL_NEGATIVE
    # return LOCAL_POSITIVE


def remote_inference_state():
    raise NotImplementedError


def alert_state():
    print("ALERT!!!")
    print("ABORTING")
    camera.stop_preview()
    exit()


# STATE SIGNALS
NEW_CAM_DATA = 0
LOCAL_NEGATIVE = 1
LOCAL_POSITIVE = 2
LOCAL_UNCERTAIN = 3


state_switch = {
    NEW_CAM_DATA: local_inference_state,
    LOCAL_NEGATIVE: capture_state,
    LOCAL_POSITIVE: alert_state
}


def main():

    camera.start_preview()

    old_state = LOCAL_NEGATIVE

    iters = 0
    limit = 10

    t0 = perf_counter_ns()
    print("Starting!")

    while iters < limit:
    # while True:

        new_state = state_switch[old_state]
        signal = new_state()
        old_state = signal

        iters += 1

    t1 = perf_counter_ns()
    print("State switches: ",iters)
    delta = t1 - t0
    print("CPU time elapsed (ns): ", format(delta, '.3e'))  # CPU nano seconds elapsed (floating point)
    print("Avg ns/state: ",format(delta/iters, '.1f'))


if __name__ == '__main__':
    main()
