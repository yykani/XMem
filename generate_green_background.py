import os
import cv2
import numpy as np
from datetime import datetime
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Replace non-masked regions with green background.")
    parser.add_argument('--video_name', type=str, required=True, help='Target video workspace name')
    parser.add_argument('--dilate', type=int, default=0, help='Dilate mask by N pixels')
    parser.add_argument('--blur', type=int, default=0, help='Gaussian blur kernel size (odd int, 0 for no blur)')
    parser.add_argument('--green', type=str, default='0,255,0', help='Green color RGB (comma-separated, e.g. 0,255,0)')
    return parser.parse_args()

def load_mask(mask_path, dilate=0, blur=0):
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise FileNotFoundError(f"Mask not found: {mask_path}")
    # 黒以外（0以外）をすべてマスク（255）として扱う
    _, mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)
    if dilate > 0:
        kernel = np.ones((dilate, dilate), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
    if blur > 0 and blur % 2 == 1:
        mask = cv2.GaussianBlur(mask, (blur, blur), 0)
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    return mask

def apply_green_background(image, mask, green_color):
    # green_color: tuple/list of 3 ints (BGR)
    green_img = np.full_like(image, green_color, dtype=np.uint8)
    # マスク部分は元画像、マスク以外はグリーン
    result = image.copy()
    result[mask == 0] = green_img[mask == 0]
    return result

def main():
    args = parse_args()
    base_dir = os.path.join('workspace', args.video_name)
    mask_dir = os.path.join(base_dir, 'masks')
    img_dir = os.path.join(base_dir, 'images')
    out_dir = os.path.join(base_dir, 'greenback', datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(out_dir, exist_ok=True)

    def get_frame_number(filename):
        base_name = os.path.splitext(filename)[0]
        digits = ''.join(c for c in base_name if c.isdigit())
        if digits:
            return int(digits)
        else:
            raise ValueError(f"No frame number found in {filename}")

    mask_files = sorted([f for f in os.listdir(mask_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    img_files = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])

    img_map = {}
    for img_file in img_files:
        try:
            frame_num = get_frame_number(img_file)
            img_map[frame_num] = img_file
        except ValueError:
            continue

    green_color = tuple(int(x) for x in args.green.split(','))

    total = len(mask_files)
    print(f"Processing {total} frames...")
    for i, mask_file in enumerate(mask_files):
        mask_path = os.path.join(mask_dir, mask_file)
        img_path = None
        try:
            frame_num = get_frame_number(mask_file)
            if frame_num in img_map:
                img_file = img_map[frame_num]
                img_path = os.path.join(img_dir, img_file)
            else:
                base_name = os.path.splitext(mask_file)[0]
                for ext in ['.jpg', '.jpeg', '.png']:
                    potential_img = base_name + ext
                    potential_path = os.path.join(img_dir, potential_img)
                    if os.path.exists(potential_path):
                        img_path = potential_path
                        break
                else:
                    img_path = os.path.join(img_dir, mask_file)
        except ValueError:
            base_name = os.path.splitext(mask_file)[0]
            for ext in ['.jpg', '.jpeg', '.png']:
                potential_img = base_name + ext
                potential_path = os.path.join(img_dir, potential_img)
                if os.path.exists(potential_path):
                    img_path = potential_path
                    break
            else:
                img_path = os.path.join(img_dir, mask_file)

        if not os.path.exists(img_path):
            print(f"Image not found for mask: {mask_file} (tried multiple extensions)")
            continue

        mask = load_mask(mask_path, dilate=args.dilate, blur=args.blur)
        image = cv2.imread(img_path)
        if image is None:
            print(f"Failed to load image: {img_path}")
            continue

        greenback_img = apply_green_background(image, mask, green_color)
        out_path = os.path.join(out_dir, mask_file)
        cv2.imwrite(out_path, greenback_img)

        if (i+1) % 10 == 0 or i+1 == total:
            print(f"Progress: {i+1}/{total} ({(i+1)/total*100:.1f}%)")

    print(f"Done! Green background images saved to: {out_dir}")

if __name__ == '__main__':
    main()
