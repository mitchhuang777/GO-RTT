import pytesseract
from pytesseract import Output
import PIL.Image
import cv2

custom_config = r'-c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz --tessdata-dir "C:\Users\Mitch\AppData\Local\Programs\Tesseract-OCR\tessdata" --psm 11 --oem 3'


img = cv2.imread("test1.png")
height, width, _ = img.shape

data = pytesseract.image_to_data(img, config = custom_config, output_type = Output.DICT)

amount_boxes = len(data['text'])
for i in range(amount_boxes):
    # if float(data['conf'][i]) > 50:
    (x, y, width, height) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
    img = cv2.rectangle(img, (x, y), (x+width, y+height), (0, 255, 0), 2)
    img = cv2.putText(img, data['text'][i], (x, y+height+20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

cv2.imshow("img", img)
cv2.waitKey(0)


