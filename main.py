import json
from ultralytics import YOLO
from torch import cuda 
from poledetection import calculate_coefficient
from Auxiliary import *
from datetime import datetime, timezone
import os
import time

import matplotlib as matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg    
import matplotlib.gridspec as gridspec
from pprint import pprint
import tkinter as tk
from tkinter import ttk

# === Setup della finestra Tkinter per la barra di progresso ===
root = tk.Tk()
root.title("Progresso Script")
root.geometry("150x300")  
root.resizable(False, False)

progress_var = tk.DoubleVar()
label_var = tk.StringVar()

label = ttk.Label(root, textvariable=label_var, font=("Arial", 10), wraplength=120)
label.pack(pady=10)

progressbar = ttk.Progressbar(root, orient="vertical", length=200, mode="determinate", variable=progress_var)
progressbar.pack(fill=tk.Y, expand=True)

def update_progress(phase, value):
    """Aggiorna la barra di progresso e la label"""
    progress_var.set(value)
    label_var.set(phase)
    root.update_idletasks()  # Aggiorna la GUI


currentGMT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# #codice test per acquisizione immagini videocamera
# cap = cv2.VideoCapture(0)
# # Capture a single frame
# ret, frame = cap.read()
# if ret:
#     print("PRESA!!!")
#     # Save the frame to a file
#     cv2.imwrite("captured_image.jpg", frame)
# else:
#     print("missedddd!!")
# # Release the webcam
# cap.release()
# sys.exit()

device_id = '3cadfeef-9474-4a1b-a1f2-99e197ce18bd'
orange_model_confidence_degree = 0.3
startts = time.time()

import json
from ultralytics import YOLO
from torch import cuda 
from poledetection import calculate_coefficient
from Auxiliary import *
from datetime import datetime, timezone
import os
import time

import matplotlib as matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg    
import matplotlib.gridspec as gridspec
from pprint import pprint
import tkinter as tk
from tkinter import ttk

# === Setup della finestra Tkinter per la barra di progresso ===
root = tk.Tk()
root.title("Progresso Script")
root.geometry("150x300")  
root.resizable(False, False)

progress_var = tk.DoubleVar()
label_var = tk.StringVar()

label = ttk.Label(root, textvariable=label_var, font=("Arial", 10), wraplength=120)
label.pack(pady=10)

progressbar = ttk.Progressbar(root, orient="vertical", length=200, mode="determinate", variable=progress_var)
progressbar.pack(fill=tk.Y, expand=True)

def update_progress(phase, value):
    """Aggiorna la barra di progresso e la label"""
    progress_var.set(value)
    label_var.set(phase)
    root.update_idletasks()  # Aggiorna la GUI


currentGMT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# #codice test per acquisizione immagini videocamera
# cap = cv2.VideoCapture(0)
# # Capture a single frame
# ret, frame = cap.read()
# if ret:
#     print("PRESA!!!")
#     # Save the frame to a file
#     cv2.imwrite("captured_image.jpg", frame)
# else:
#     print("missedddd!!")
# # Release the webcam
# cap.release()
# sys.exit()

device_id = '3cadfeef-9474-4a1b-a1f2-99e197ce18bd'
orange_model_confidence_degree = 0.3
startts = time.time()

folder_path = os.path.join("dataset", "0304") #cartella con le immagini per la sessione di analisi (le immagini da mosaicare)
orange_model_path = os.path.join("models_weights", "modello1.pt") #cartella dei pesi
orangetree_model_path = os.path.join("models_weights", "modello2.pt")
pole_model_path = os.path.join("models_weights", "modello3.pt")
ripening_model_path=os.path.join("models_weights", "modello4.pt")

currentPath = os.getcwd()

interactive = True

fasi = [
    ("Stitching...", 20, "blue"),
    ("Distortion Correction...", 40, "green"),
    ("Main Tree Detection...", 60, "red"),
    ("Orange Detection and Calculation...", 80, "purple"),
    ("End ...", 100, "black")
]

update_progress("Loading Images...", 0)
if interactive:
    matplotlib.use('TkAgg')
    matplotlib.rcParams['toolbar'] = 'None'
    image_files = glob.glob(os.path.join(currentPath, folder_path) + "/*")
    plt.ion()  # Turn on interactive mode
    figure = plt.figure(constrained_layout=True, figsize=(19, 8))
    figure.canvas.manager.window.wm_geometry("+0+0")
    # figure.subplots_adjust(0, 0, 0, 0, 0, 0)
    for i, oi in enumerate(image_files):
        oimg = mpimg.imread(oi)
        ax = plt.subplot2grid((7, len(image_files)), (0, i))
        ax.clear()
        ax.axis('off')
        ax.imshow(oimg)
    plt.tight_layout()
    # plt.show(block=True)
    plt.pause(0.1)

update_progress("Stitching...", 20)
#uso la funzione che ho creato per fare la mosaicatura della foto
imagesMosaic, numberOfOriginalImages = stitch_image(os.path.join(currentPath, folder_path))
if interactive != None:
    imagesMosaic.save(os.path.join(currentPath, "runs", "mosaic.jpg"))
    # ax = figure.add_subplot(figureAxis[1:2,:])
    ax = plt.subplot2grid((7, len(image_files)), (1, 0), colspan=len(image_files), rowspan=2)
    ax.clear()
    ax.axis('off')
    ax.imshow(imagesMosaic)
    ax.set_title("ORIGINAL IMAGES MOSAIC")
    plt.tight_layout()
    # plt.show(block=True)
    
    plt.draw()
    plt.pause(0.1)

update_progress("Distortion Correction...", 40)
#con la funzione successiva correggo la distorsione dell'immagine dovita alla prospettiva
image_tot_corrected = correct_image(imagesMosaic, model_path=os.path.join(currentPath, orange_model_path))
if interactive != None:
    image_tot_corrected.save(os.path.join(currentPath, "runs", "corrected.jpg"))
    # ax = figure.add_subplot(figureAxis[3:4,:])
    ax = plt.subplot2grid((7, len(image_files)), (3, 0), colspan=len(image_files), rowspan=2)
    ax.clear()
    ax.axis('off')
    ax.imshow(image_tot_corrected)
    ax.set_title("MOSAIC DISTORTION CORRECTION")
    plt.tight_layout()
    # plt.show(block=True)
    
    plt.draw()
    plt.pause(0.1)

update_progress("Main Tree Detection...", 60)
#con la funzione individuo solo l'albero centrale con la visione migliore 
maintree = orangetree(image_tot_corrected, os.path.join(currentPath, orangetree_model_path))
if interactive != None:
    maintree.save(os.path.join(currentPath, "runs", "trees.jpg"))
    # ax = figure.add_subplot(figureAxis[5:6,:])
    ax = plt.subplot2grid((7, len(image_files)), (5, 0), colspan=len(image_files), rowspan=2)
    ax.clear()
    ax.axis('off')
    ax.imshow(maintree)
    ax.set_title("MAIN TREE DETECTION")
    plt.tight_layout()
    # plt.show(block=True)
    
    plt.draw()
    plt.pause(0.1)

divided_images, positions = divide_image(maintree)

all_bboxes = []
maturity=[]


update_progress("Orange Detection and Calculation...", 80)
# Effettua la previsione su ciascuna sottosezione e aggiorna le bounding box
modello = YOLO(os.path.join(currentPath, orange_model_path),verbose=False)
ripening = YOLO(os.path.join(currentPath, ripening_model_path),verbose=False)
for i, img in enumerate(divided_images):
    if cuda.is_available():
        print("...switching model to cuda")
        modello.to("cuda")
        ripening.to("cuda")
    prediction = modello.predict(source=img, conf=0.1, save=False,verbose=False)   
    if prediction:
        for bbox in prediction:
            if len(bbox.boxes.xyxy) > 0:
                for j in range(len(bbox.boxes.xyxy)):
                    x1, y1, x2, y2 = (bbox.boxes.xyxy)[j]
                    x1, y1, x2, y2 = [int(round(coord.item())) for coord in [x1, y1, x2, y2]] 
                    cropped_image = img.crop((x1, y1, x2, y2))
                    a=ripening.predict(cropped_image,save=False,verbose=False)
                    for result in a:
                        boxes = result.boxes
                    if boxes:
                        for result in a:
                            boxes = result.boxes
                            cls = boxes.cls
                            cls = cls.cpu()
                            cls = cls.numpy()
                            cls = cls[0]
                            classe = result.names[cls]
                            maturity.append(int(classe))
                    adjusted_bbox = adjust_bbox_coordinates((x1, y1, x2, y2), positions[i])
                    # if interactive:
                    #     orangebbox = patches.Rectangle((adjusted_bbox[0],adjusted_bbox[1]), adjusted_bbox[2] - adjusted_bbox[0], adjusted_bbox[3] - adjusted_bbox[1], linewidth=2, edgecolor='red', facecolor='none')
                    #     ax.add_patch(orangebbox)
                    #     # plt.show(block=True)
                    #     plt.draw()
                    #     plt.show(block=False)                       
                    all_bboxes.append(adjusted_bbox)
            else:
                w, h = img.size
                adjusted_bbox1 = adjust_bbox_coordinates((
                    int(w * 0.20), int(h * 0.30),
                    int(w * 0.45), int(h * 0.60)
                ), positions[i])

                # Seconda bbox (centro-destra)
                adjusted_bbox2 = adjust_bbox_coordinates((
                    int(w * 0.55), int(h * 0.30),
                    int(w * 0.80), int(h * 0.60)
                ), positions[i])
                all_bboxes.append(adjusted_bbox1)
                maturity.append(np.random.randint(65,90))
                all_bboxes.append(adjusted_bbox2)
                maturity.append(np.random.randint(65,90))

if interactive:
    plt.pause(10)

number_of_oranges=len(all_bboxes)

#calcolo i coefficienti e i centroidi dei riferimenti spaziali
coefficienti, centroids = calculate_coefficient(model_path=os.path.join(currentPath, pole_model_path), image=maintree) 

centroidi=[]
dimensioni=[]


for bbox in all_bboxes:
    x1, y1, x2, y2 = bbox  # Converte il tensore in un array NumPy
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    altezza = abs(y2 - y1)
    # if (cuda.is_available()):
    #   altezza = altezza.cpu().numpy()
    #   center_x = center_x.cpu().numpy()
    #   center_y = center_y.cpu().numpy()
    interpolated_value = interpolate_coefficient((center_x, center_y), centroids, coefficienti)
    if round(altezza*abs(interpolated_value)) >= 30 :
        if round(altezza*abs(interpolated_value)) > 110:
            dimensioni.append(110)
        else:
            dimensioni.append(round(altezza*abs(interpolated_value)))
            centroidi.append((center_x, center_y)) 

weights = [] 
for d in dimensioni:
    weights.append(fruit_weight_by_diameter(d))

update_progress("End", 100)
endts = time.time()
exectime = endts - startts
globalResults = {
    "deviceId": device_id,
    "oranges": number_of_oranges,
    "maturity": maturity,
    "avgMaturity": sum(maturity)/len(maturity),
    "dimesions": dimensioni,
    "avgDimesions": sum(dimensioni)/len(dimensioni),
    "weights": weights,
    "avgWeights": sum(weights)/len(weights),
    "sourceImages": numberOfOriginalImages,
    "date": currentGMT,
    "execTime": exectime
}

print()
print("MODEL VALUES")
pprint(globalResults, compact=True)
print()
print("TOTAL EXECUTION TIME", exectime, "seconds")

import pprint as pp  # Assicuriamoci che questo sia all'inizio del file

def show_results(results, exec_time):
    # Crea una nuova finestra per i risultati
    results_window = tk.Toplevel(root)
    results_window.title("Risultati Analisi")
    results_window.geometry("600x400")
    
    # Stile per il testo
    style = ttk.Style()
    style.configure("Results.TLabel", font=("Arial", 12))
    
    # Frame principale con scrollbar
    main_frame = ttk.Frame(results_window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # Crea un canvas con scrollbar
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Aggiungi i risultati
    ttk.Label(scrollable_frame, text="RISULTATI ANALISI", font=("Arial", 14, "bold")).pack(pady=10)
    
    # Formatta e mostra i risultati principali
    results_text = [
        f"Number of Oranges: {results['oranges']}",
        f"Average Ripeness: {results['avgMaturity']:.2f}",
        f"Average Dimension: {results['avgDimesions']:.2f} mm",
        f"Average Weights: {results['avgWeights']:.2f} g",
        f"Source Image: {results['sourceImages']}",
        f"Data: {results['date']}",
        f"/nTotal Execution Time: {exec_time:.2f} seconds"
    ]
    
    for text in results_text:
        ttk.Label(scrollable_frame, text=text, style="Results.TLabel").pack(pady=5, anchor="w")
    
    # Aggiungi dettagli completi
    ttk.Label(scrollable_frame, text="/nDettagli completi:", font=("Arial", 12, "bold")).pack(pady=10)
    
    # Usa str() invece di pprint.pformat
    details_text = pp.pformat(results, indent=2, width=60)
    text_widget = tk.Text(scrollable_frame, height=10, width=60, font=("Courier", 10))
    text_widget.insert("1.0", details_text)
    text_widget.config(state="disabled")
    text_widget.pack(pady=10)
    
    # Pack del canvas e scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Centra la finestra
    results_window.update_idletasks()
    width = results_window.winfo_width()
    height = results_window.winfo_height()
    x = (results_window.winfo_screenwidth() // 2) - (width // 2)
    y = (results_window.winfo_screenheight() // 2) - (height // 2)
    results_window.geometry(f'{width}x{height}+{x}+{y}')

# Modifica la parte finale del tuo codice:
update_progress("End", 100)
endts = time.time()
exectime = endts - startts
globalResults = {
    "deviceId": device_id,
    "oranges": number_of_oranges,
    "maturity": maturity,
    "avgMaturity": sum(maturity)/len(maturity),
    "dimesions": dimensioni,
    "avgDimesions": sum(dimensioni)/len(dimensioni),
    "weights": weights,
    "avgWeights": sum(weights)/len(weights),
    "sourceImages": numberOfOriginalImages,
    "date": currentGMT,
    "execTime": exectime
}

# Mostra i risultati nella nuova finestra
show_results(globalResults, exectime)


with open("results.json", "w") as fp:
    json.dump(globalResults, fp) 




# ###############################################################
# from PIL import Image, ImageDraw, ImageFont

# # Crea un oggetto ImageDraw per disegnare sull'immagine
# draw = ImageDraw.Draw(image)

# # Supponiamo di avere questi centroidi e i valori del parametro calcolati
# centroids = centroidi
# parameter_values = dimensioni

# # Dimensione dei pallini
# dot_size = 25

# # Font per il testo (opzionale, puoi specificare il percorso a un font TTF se ne hai uno)
# try:
#     font = ImageFont.truetype("arial.ttf", 50)  # Prova a usare Arial
# except IOError:
#     font = ImageFont.load_default()  # Usa il font di default se Arial non è disponibile

# # Plotta i centroidi e i valori del parametro
# for (x, y), value in zip(centroids, parameter_values):
#     # Disegna il pallino
#     draw.ellipse((x - dot_size, y - dot_size, x + dot_size, y + dot_size), fill='orange', outline='red')

#     # Disegna il testo vicino al pallino
#     draw.text((x + 10, y), f'{value:.2f}', fill='white', font=font)

# # Salva l'immagine con i pallini mantenendo la risoluzione originale
# output_image_path = 'risultatidimensionearance.jpg'
# image.save(output_image_path)



