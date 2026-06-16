import os
from PIL import Image

def convert_images():
    for filename in os.listdir("registered_faces"):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                img_path = os.path.join("registered_faces", filename)
                with Image.open(img_path) as img:
                    # Convert to RGB if not already
                    if img.mode != 'RGB':
                        rgb_img = img.convert('RGB')
                        rgb_img.save(img_path)
                        print(f"Converted {filename} to RGB")
            except Exception as e:
                print(f"Failed {filename}: {str(e)}")

if __name__ == "__main__":
    convert_images()