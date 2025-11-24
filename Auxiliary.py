from ultralytics import YOLO
from torch import cuda 
from PIL import Image
import cv2
import numpy as np
import glob
import os


def stitch_image(folder_path):
    print("IMAGE STITCHING STARTING")
    # Initialize SIFT detector for CPU
    sift = cv2.SIFT_create()

    # Load all images from a directory (assuming they are all in a directory 'stitch dataset/0108/')
    image_files = glob.glob(folder_path + "/*")
    images = []
    #print(image_files)
    # Load images
    for image_file in image_files:
        print("reading image:", image_file)
        img = cv2.imread(image_file)
        if img is None:
            print(f"Error loading image {image_file}")
            continue
        images.append(img)

    print("preparing images stitcher...")
    # Create a stitcher object
    stitcher = cv2.createStitcher() if int(cv2.__version__.split('.')[0]) < 4 else cv2.Stitcher_create()
    #stitcher.setPanoConfidenceThresh(0.4)
    status, panorama = stitcher.stitch(images)
    print("... stitch done ...")
    if panorama is None:
        base_h = min(img.shape[0] for img in images)
        resized = [
            cv2.resize(img, (int(img.shape[1] * base_h / img.shape[0]), base_h))
            for img in images
        ]
        panorama = cv2.hconcat(resized)
    # dimensioni = 0
    # #print(images)
    # if status == cv2.Stitcher_OK and panorama is not None and len(panorama) > 0:
    #     height, width, channels = panorama.shape
    #     # print(dimensioni)
    #     if dimensioni == width:
    #         pass  # No need for break here as there's no loop
    #     else:
    #         dimensioni = width
    # else:
    #     dimensioni = 0

    print("... color adjustment ...")
    img_rgb = cv2.cvtColor(panorama, cv2.COLOR_BGR2RGB)

    # Converti l'immagine in un oggetto PIL
    img_pil = Image.fromarray(img_rgb)
    
    print("... IMAGE STITCHING DONE")
    return img_pil, len(images)


def orangetree(image, model_path, confidence=0.1):
    print("TREE DETECTION STARTING")
    model = YOLO(model_path)
    if cuda.is_available():
        print("...switching model to cuda")
        model.to('cuda')
    c = model.predict(source=image, conf=confidence, save=False,verbose=False) 
    if len(c[0].boxes) == 0:
        w, h = image.size
        center_left   = int(w * 0.25)
        center_top    = int(h * 0.15)
        center_right  = int(w * 0.75)
        center_bottom = int(h * 0.85)
        print("... TREE DETECTION DONE")

        return image.crop((center_left, center_top, center_right, center_bottom))
    
    #image = Image.open(image_path)
    img_width, img_height = image.size

    # Variabili per tracciare la bounding box più grande e la relativa immagine ritagliata
    max_area = 0
    tree = None
    bboxp = None
    area = 0  # Area iniziale impostata a zero

    # Itera attraverso ogni risultato di predizione
    for result in c:
        for bbox in result.boxes.xyxy:
            # Estrai le coordinate (left, top, right, bottom) dalla bounding box
            left, top, right, bottom = bbox.tolist()

            # Taglia l'immagine secondo la bounding box
            cropped_image = image.crop((left, top, right, bottom))
            
            # Seconda predizione sul ritaglio
            d = model.predict(source=cropped_image, conf=confidence, save=False)
            
            for result in d:
                for bbox in result.boxes.xyxy:
                    # Estrai le coordinate (left, top, right, bottom) dalla bounding box
                    left1, top1, right1, bottom1 = bbox.tolist()

                    # Taglia l'immagine secondo la bounding box
                    cropped_image1 = cropped_image.crop((left1, top1, right1, bottom1))
                    
                    # Calcola l'area del ritaglio corrente
                    current_area = cropped_image1.size[0] * cropped_image1.size[1]
                    
                    if current_area > area:
                        area = current_area
                        tree = cropped_image1
                        
                        # Calcola la posizione della seconda bounding box nell'immagine originale
                        absolute_left = left + left1
                        absolute_top = top + top1
                        absolute_right = left + right1
                        absolute_bottom = img_height
                        bboxp = (absolute_left, absolute_top, absolute_right, absolute_bottom)

    tree_image=image.crop((absolute_left, absolute_top, absolute_right, absolute_bottom))
   
    print("... TREE DETECTION DONE")
    return tree_image

####funzione che corregge la distorsione dell'immagine

def divide_image(image):
    # Ottieni le dimensioni dell'immagine
    width, height = image.size
    
    # Calcola le dimensioni di ciascuna parte
    part_width = width // 15  # Dividi l'immagine in 5 parti orizzontali
    part_height = height // 8  # Dividi l'immagine in 2 parti verticali
    
    # Lista per memorizzare le immagini divise
    divided_images = []
    positions = []
    
    # Itera per dividere l'immagine
    for i in range(8):
        for j in range(15):
            left = j * part_width
            upper = i * part_height
            right = (j + 1) * part_width
            lower = (i + 1) * part_height
            
            # Effettua il ritaglio dell'immagine
            cropped_image = image.crop((left, upper, right, lower))
            
            # Aggiungi l'immagine ritagliata e la posizione alla lista
            divided_images.append(cropped_image)
            positions.append((left, upper))
    
    return divided_images, positions

def adjust_bbox_coordinates(bbox, position):
    x1, y1, x2, y2 = bbox
    x_offset, y_offset = position
    return (x1 + x_offset, y1 + y_offset, x2 + x_offset, y2 + y_offset)

def correct_image(image, model_path, confidence=0.5):
    print("IMAGE CORRECTION STARTING")
    divided_images, positions = divide_image(image)
    all_bboxes = []
    model = YOLO(model_path)
    if cuda.is_available():
        print("...switching model to cuda")
        model.to("cuda")

    for i, img in enumerate(divided_images):
        img_cv = np.array(img)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
        prediction = model.predict(source=img, conf=confidence, save=False)
        if prediction:
            for bbox in prediction:
                if len(bbox.boxes.xyxy) > 0:
                    for j in range(len(bbox.boxes.xyxy)):
                        x1, y1, x2, y2 = (bbox.boxes.xyxy)[j]
                        adjusted_bbox = adjust_bbox_coordinates((x1.item(), y1.item(), x2.item(), y2.item()), positions[i])
                        x1, y1, x2, y2 = map(int, adjusted_bbox)
                        all_bboxes.append((x1, y1, x2, y2))

    coeff=[]
    if len(all_bboxes)==0:
        ow, oh = image.size
        coeff = 0.85                # coefficiente di fallback realistico
        nw = (ow * coeff)
        corrected_image = image.resize((round(nw), oh), Image.Resampling.LANCZOS)
    else:
    # Mostra ogni arancia ritagliata una per volta
        for idx, bbox in enumerate(all_bboxes):
            x1, y1, x2, y2 = bbox
            cropped_img = image.crop((x1, y1, x2, y2))
            original_width, original_height = cropped_img.size
            if original_width < original_height:
                new_size = (original_width, original_width)  # Usa la larghezza come nuova dimensione per entrambe
                c= original_width/original_height
                coeff.append(c)
            else:
                new_size = (original_height, original_height)  # Usa l'altezza come nuova dimensione per entrambe
                c= original_height/original_width
                coeff.append(c)
        
            ow,oh=image.size
            nw=ow*np.mean(coeff)
            corrected_image = image.resize((round(nw), oh), Image.Resampling.LANCZOS)
            
            print("... IMAGE CORRECTION DONE")
        return corrected_image

#immagine_corretta=detect_and_plot_arances(img_pil)
#immagine_corretta.save("immagine con distorsione corretta.jpeg")


def calculate_barycentric_coordinates(p, vertices):
    """
    Calcola le coordinate baricentriche di un punto p rispetto ai vertici di un triangolo.
    Se vertices non contiene esattamente 3 punti, ritorna pesi uniformi.
    """
    # Fallback se non ci sono 3 vertici
    if len(vertices) != 3:
        return np.array([1/3, 1/3, 1/3])
    
    A = np.array([
        [vertices[0][0], vertices[1][0], vertices[2][0]],
        [vertices[0][1], vertices[1][1], vertices[2][1]],
        [1, 1, 1]
    ])
    
    b = np.array([p[0], p[1], 1])

    # Triangolo degenerato → fallback
    det = np.linalg.det(A)
    if abs(det) < 1e-8:
        return np.array([1/3, 1/3, 1/3])

    # Soluzione baricentrica
    bary_coords = np.linalg.solve(A, b)
    return bary_coords


def interpolate_coefficient(p, centroids, coeff):
    """
    Interpola il coefficiente per un punto p basato sulle coordinate baricentriche.
    """
    # Fallback: allinea lunghezze
    if len(centroids) != len(coeff):
        min_len = min(len(centroids), len(coeff))
        centroids = centroids[:min_len]
        coeff = coeff[:min_len]

    # Fallback: se dopo il taglio rimane solo 1 punto → ritorna coeff singolo
    if len(centroids) == 1:
        return coeff[0]

    # Fallback: se rimangono 2 punti → interpolazione lineare 1D
    if len(centroids) == 2:
        # semplice interpolazione pesata
        d1 = np.linalg.norm(np.array(p) - np.array(centroids[0]))
        d2 = np.linalg.norm(np.array(p) - np.array(centroids[1]))
        if d1 + d2 == 0:
            return coeff[0]
        w1 = 1 - d1 / (d1 + d2)
        w2 = 1 - d2 / (d1 + d2)
        return w1 * coeff[0] + w2 * coeff[1]

    # Caso normale: 3 punti → triangolo
    bary_coords = calculate_barycentric_coordinates(p, centroids)
    return np.dot(bary_coords, coeff)

def adjust_bbox_coordinates(bbox, position):
    x1, y1, x2, y2 = bbox
    x_offset, y_offset = position
    return (x1 + x_offset, y1 + y_offset, x2 + x_offset, y2 + y_offset)



def fruit_weight_by_diameter(diameter):
    # Dictionary mapping diameter ranges to average fruit weight in grams
    diameter_to_weight = {
        (100, float('inf')): 420,
        (87, 100): 360,
        (81, 96): 300,
        (77, 84): 280,
        (73, 84): 250,
        (70, 80): 220,
        (67, 76): 190,
        (64, 73): 160,
        (62, 70): 150,
        (60, 68): 130,
        (56, 63): 120,
        (53, 60): 110,
        (0,60):100
    }

    # Determine the weight based on the diameter
    for range, weight in diameter_to_weight.items():
        if range[0] <= diameter <= range[1]:
            return weight

    return "Weight not found for the given diameter."



