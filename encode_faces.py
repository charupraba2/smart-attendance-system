import cv2
import face_recognition
import pickle
import os

# Path to the dataset of images
dataset_path = 'images'
# Path to save encodings
encodings_file = 'encodings.pickle'
# Detection method: 'hog' or 'cnn' (cnn is more accurate but requires GPU)
detection_method = 'hog' 

knownEncodings = []
knownNames = []

print("[INFO] quantifying faces...")
imagePaths = [os.path.join(dataset_path, f) for f in os.listdir(dataset_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

if not imagePaths:
    print(f"[WARNING] No images found in '{dataset_path}'. Please add images of people (e.g., 'john_doe.jpg').")

for (i, imagePath) in enumerate(imagePaths):
    print(f"[INFO] processing image {i + 1}/{len(imagePaths)}")
    name = os.path.splitext(os.path.basename(imagePath))[0]
    
    # Load image and convert to RGB (OpenCV uses BGR)
    image = cv2.imread(imagePath)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Detect the (x, y)-coordinates of the bounding boxes corresponding to each face
    boxes = face_recognition.face_locations(rgb, model=detection_method)
    
    # Compute the facial embedding for the face
    encodings = face_recognition.face_encodings(rgb, boxes)
    
    # Loop over the encodings
    for encoding in encodings:
        knownEncodings.append(encoding)
        knownNames.append(name)

print("[INFO] serializing encodings...")
data = {"encodings": knownEncodings, "names": knownNames}
with open(encodings_file, "wb") as f:
    f.write(pickle.dumps(data))
print(f"[INFO] encodings saved to '{encodings_file}'")
