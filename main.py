import cv2  # Important !!! pip install opencv-contrib-python

from LineDetector import LineDetector

def main():
    cap = cv2.VideoCapture("/Users/arsenyzharkoy/PycharmProjects/Mrstearn2.0/Video_20260210_092539_458.mp4")

    lineDetector = LineDetector()

    while(cap.isOpened()):
        ret, frame = cap.read()

        processed_frame = lineDetector.process_frame(frame)

        cv2.imshow('frame', processed_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()