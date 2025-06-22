import os
import cv2
import argparse
import glob
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description="Resize all images in a folder by scale factor.")
    parser.add_argument('--input_dir', type=str, required=True, help='Directory containing images')
    parser.add_argument('--scale', type=float, default=0.5, help='Scale factor (e.g. 0.8 for 80% of original size)')
    parser.add_argument('--output_dir', type=str, default=None, 
                        help='Output directory (default: input_dir/resized_[scale]x_[datetime])')
    return parser.parse_args()

def resize_images(input_dir, output_dir, scale):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Get all image files with common extensions
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
        image_files.extend(glob.glob(os.path.join(input_dir, ext)))
        image_files.extend(glob.glob(os.path.join(input_dir, ext.upper())))
    
    if not image_files:
        print(f"No image files found in {input_dir}")
        return

    print(f"Found {len(image_files)} images")
    for i, img_path in enumerate(sorted(image_files), 1):
        try:
            # Read image
            img = cv2.imread(img_path)
            if img is None:
                print(f"Could not open image: {img_path}")
                continue
            
            # Calculate new size
            height, width = img.shape[:2]
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Resize
            resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Save
            filename = os.path.basename(img_path)
            output_path = os.path.join(output_dir, filename)
            cv2.imwrite(output_path, resized)
            
            # Progress report
            if i % 10 == 0 or i == len(image_files):
                print(f"Processed {i}/{len(image_files)} images")
        
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

def main():
    args = parse_args()
    input_dir = args.input_dir
    scale = args.scale
    
    if not os.path.isdir(input_dir):
        print(f"Input directory does not exist: {input_dir}")
        return
    
    # Create output directory name if not provided
    if not args.output_dir:
        parent_dir = os.path.dirname(input_dir)
        folder_name = f"resized_{scale:.1f}x_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir = os.path.join(parent_dir, folder_name)
    else:
        output_dir = args.output_dir
    
    print(f"Resizing images in {input_dir} to {scale:.1f}x of original size")
    print(f"Output directory: {output_dir}")
    
    resize_images(input_dir, output_dir, scale)
    print("Resize complete!")

if __name__ == '__main__':
    main()