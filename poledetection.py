
import ultralytics
from ultralytics import YOLO
import PIL
from PIL import Image,ImageDraw
import matplotlib.pyplot as plt
import cv2
import numpy as np
import os
import cv2
import matplotlib.patches as patches


def expand_bbox(x1, y1, x2, y2, expansion_ratio=0.25):
    bbox_width = x2 - x1
    bbox_height = y2 - y1
    expansion_x = int(bbox_width * expansion_ratio)
    expansion_y = int(bbox_height * expansion_ratio)
    x1_expanded = max(x1 - expansion_x, 0)
    y1_expanded = max(y1 - expansion_y, 0)
    x2_expanded = x2 + expansion_x
    y2_expanded = y2 + expansion_y
    return x1_expanded, y1_expanded, x2_expanded, y2_expanded

def divide_image_horizontally(image, patch_width):
    patches = []
    img_width, img_height = image.size
    for x in range(0, img_width, patch_width):
        box = (x, 0, min(x + patch_width, img_width), img_height)
        patch = image.crop(box)
        patches.append((patch, x))
    return patches

def calculate_coefficient(model_path, image):
    model = YOLO(model_path)

    # Larghezza della patch (ad esempio, 640)
    patch_width = 640

    # Dividi l'immagine in patch lungo la larghezza
    patches = divide_image_horizontally(image, patch_width)

    # Itera su ciascuna patch e esegui la rilevazione
    all_detections = []
    for patch, x_offset in patches:
        # Converti la patch in un array numpy
        patch_array = np.array(patch)

        # Esegui il modello YOLO sulla patch
        results = model.predict(patch_array,conf=0.075,verbose=False)
        if len(results[0].boxes)==0:
            pw, ph = patch.size
            fx1 = pw//2 - 5
            fx2 = pw//2 + 5
            fy1 = int(ph * 0.15)
            fy2 = int(ph * 0.85)
            all_detections.append((fx1 + x_offset, fy1, fx2 + x_offset, fy2))
        else:
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Estrai coordinate della bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    # Aggiungi l'offset per ottenere le coordinate originali
                    x1 += x_offset
                    x2 += x_offset
                    # Amplia la bounding box
                    x1, y1, x2, y2 = expand_bbox(x1, y1, x2, y2)
                    # Salva la bounding box con le coordinate originali
                    all_detections.append((x1, y1, x2, y2))

    # Seconda fase di rilevazione sulle immagini croppate dalle bounding box
    second_detections = []
    for x1, y1, x2, y2 in all_detections:
        # Croppa l'immagine originale usando la bounding box amplificata
        cropped_image = image.crop((x1, y1, x2, y2))
        cropped_array = np.array(cropped_image)
        second_results = model.predict(cropped_array,conf=0.075,verbose=False)
        if len(second_results[0].boxes)==0:
                cw, ch = cropped_image.size
                sx1 = x1 + cw//2 - 4
                sx2 = x1 + cw//2 + 4
                sy1 = y1 + int(ch * 0.20)
                sy2 = y1 + int(ch * 0.80)
                second_detections.append((sx1, sy1, sx2, sy2))
        for second_result in second_results:
            second_boxes = second_result.boxes
            for second_box in second_boxes:
                # Estrai coordinate della seconda bounding box
                sx1, sy1, sx2, sy2 = map(int, second_box.xyxy[0])
                # Trasforma le coordinate rispetto all'immagine originale
                sx1 += x1
                sy1 += y1
                sx2 += x1
                sy2 += y1
                # Salva la bounding box con le coordinate originali
                second_detections.append((sx1, sy1, sx2, sy2))

    bounding_boxes=second_detections

    # Funzione per verificare se una bounding box è contenuta in un'altra
    def is_contained(inner, outer):
        return inner[0] >= outer[0] and inner[1] >= outer[1] and inner[2] <= outer[2] and inner[3] <= outer[3]

    # Filtra le bounding box per rimuovere quelle contenute in altre bounding box
    filtered_bounding_boxes = []
    for i, box in enumerate(bounding_boxes):
        contained = False
        for j, other_box in enumerate(bounding_boxes):
            if i != j and is_contained(box, other_box):
                contained = True
                break
        if not contained:
            filtered_bounding_boxes.append(box)


    heights = [abs(y2 - y1) for _, y1, _, y2 in filtered_bounding_boxes]

    #calcolo il coefficiente per ogni bbox 1000 mm
    coeff = [round(1000 / x,2) for x in heights]
    centroids = [((x1 + x2) / 2, (y1 + y2) / 2) for x1, y1, x2, y2 in filtered_bounding_boxes]

    return coeff,centroids

