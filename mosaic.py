import os
import cv2
import numpy as np
from datetime import datetime
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Apply mosaic to masked regions of images.")
    parser.add_argument('--video_name', type=str, required=True, help='Target video workspace name')
    parser.add_argument('--mosaic_size', type=int, default=20, help='Mosaic block size (pixel size)')
    parser.add_argument('--dilate', type=int, default=0, help='Dilate mask by N pixels')
    parser.add_argument('--blur', type=int, default=0, help='Gaussian blur kernel size (odd int, 0 for no blur)')
    parser.add_argument('--mosaic_type', type=str, default='pixel', 
                        choices=['pixel', 'blur', 'black', 'color', 'noise'],
                        help='Type of mosaic effect: pixel (default), blur, black, color, noise')
    parser.add_argument('--color', type=str, default='0,0,0', 
                        help='RGB color for color mosaic type (comma-separated, e.g. 255,0,0 for red)')
    parser.add_argument('--blur_strength', type=int, default=21,
                        help='Blur strength for blur mosaic type (odd number)')
    parser.add_argument('--output_video', action='store_true',
                        help='Additionally create MP4 video from the output images')
    parser.add_argument('--fps', type=float, default=16.0,
                        help='Frames per second for output video (default: 16)')
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

def apply_mosaic(image, mask, mosaic_size, mosaic_type='pixel', color_str='0,0,0', blur_strength=21):
    # Mosaic only masked area
    mosaic_img = image.copy()
    idx = np.where(mask == 255)
    if len(idx[0]) == 0:
        return image  # No mask, return original
    
    # Create color array from string if needed
    if mosaic_type == 'color':
        try:
            color = [int(c) for c in color_str.split(',')]
            if len(color) != 3:
                print("Invalid color format. Using black.")
                color = [0, 0, 0]
        except:
            print("Invalid color format. Using black.")
            color = [0, 0, 0]
    
    # Get bounding box of mask area
    x_min, x_max = np.min(idx[1]), np.max(idx[1])
    y_min, y_max = np.min(idx[0]), np.max(idx[0])
    roi = mosaic_img[y_min:y_max+1, x_min:x_max+1]
    mask_roi = mask[y_min:y_max+1, x_min:x_max+1]
    
    # Height and width of ROI
    h, w = roi.shape[:2]
    if h < 1 or w < 1:
        return image
    
    # Process based on mosaic type
    if mosaic_type == 'pixel':
        # Standard pixel mosaic
        roi_small = cv2.resize(roi, (max(1, w // mosaic_size), max(1, h // mosaic_size)), interpolation=cv2.INTER_LINEAR)
        roi_mosaic = cv2.resize(roi_small, (w, h), interpolation=cv2.INTER_NEAREST)
        for c in range(3):
            roi[..., c][mask_roi == 255] = roi_mosaic[..., c][mask_roi == 255]
    
    elif mosaic_type == 'blur':
        # Make blur strength odd
        if blur_strength % 2 == 0:
            blur_strength += 1
        # Gaussian blur
        roi_blur = cv2.GaussianBlur(roi, (blur_strength, blur_strength), 0)
        for c in range(3):
            roi[..., c][mask_roi == 255] = roi_blur[..., c][mask_roi == 255]
    
    elif mosaic_type == 'black':
        # Black fill
        for c in range(3):
            roi[..., c][mask_roi == 255] = 0
    
    elif mosaic_type == 'color':
        # Custom color fill
        for c in range(3):
            roi[..., c][mask_roi == 255] = color[c]
    
    elif mosaic_type == 'noise':
        # Random noise
        noise = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8)
        for c in range(3):
            roi[..., c][mask_roi == 255] = noise[..., c][mask_roi == 255]
    
    mosaic_img[y_min:y_max+1, x_min:x_max+1] = roi
    return mosaic_img

def main():
    args = parse_args()
    base_dir = os.path.join('workspace', args.video_name)
    mask_dir = os.path.join(base_dir, 'masks')
    img_dir = os.path.join(base_dir, 'images')
    out_dir = os.path.join(base_dir, 'mosaic', datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(out_dir, exist_ok=True)
    
    # ファイル名と拡張子のパターン抽出関数
    def get_frame_number(filename):
        # ファイル名からフレーム番号を抽出（例: 0000079.png -> 79, frame_0079.jpg -> 79）
        base_name = os.path.splitext(filename)[0]
        # 数字だけを抽出
        digits = ''.join(c for c in base_name if c.isdigit())
        if digits:
            return int(digits)
        else:
            raise ValueError(f"No frame number found in {filename}")
    
    # マスクと画像のファイルをそれぞれ取得
    mask_files = sorted([f for f in os.listdir(mask_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    img_files = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    
    print(f"Found {len(mask_files)} mask files and {len(img_files)} image files")
    
    # 画像のフレーム番号をマッピング
    img_map = {}
    for img_file in img_files:
        try:
            frame_num = get_frame_number(img_file)
            img_map[frame_num] = img_file
        except ValueError:
            continue
    
    total = len(mask_files)
    print(f"Processing {total} frames...")
    
    for i, mask_file in enumerate(mask_files):
        mask_path = os.path.join(mask_dir, mask_file)
        
        # マスクのフレーム番号を取得して対応する画像を検索
        img_path = None
        try:
            frame_num = get_frame_number(mask_file)
            if frame_num in img_map:
                img_file = img_map[frame_num]
                img_path = os.path.join(img_dir, img_file)
            else:
                # 拡張子を変更して試行
                base_name = os.path.splitext(mask_file)[0]
                for ext in ['.jpg', '.jpeg', '.png']:
                    potential_img = base_name + ext
                    potential_path = os.path.join(img_dir, potential_img)
                    if os.path.exists(potential_path):
                        img_path = potential_path
                        break
                else:
                    # 同じ名前で試行 (最後の手段)
                    img_path = os.path.join(img_dir, mask_file)
        except ValueError:
            # 拡張子を変更して試行
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
            
        mosaic_img = apply_mosaic(
            image, 
            mask, 
            args.mosaic_size, 
            mosaic_type=args.mosaic_type,
            color_str=args.color,
            blur_strength=args.blur_strength
        )
        out_path = os.path.join(out_dir, mask_file)
        cv2.imwrite(out_path, mosaic_img)
          # Progress update
        if (i+1) % 10 == 0 or i+1 == total:
            print(f"Progress: {i+1}/{total} ({(i+1)/total*100:.1f}%)")
            
    print(f"Done! Mosaic images saved to: {out_dir}")
    
    # MP4ビデオの作成（オプション）
    if args.output_video:
        try:
            video_path = os.path.join(os.path.dirname(out_dir), f"mosaic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
            print(f"Creating video file: {video_path}")
            
            # 画像ファイルを番号順にソート
            processed_files = sorted([f for f in os.listdir(out_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
            
            if processed_files:
                # 最初のフレームからビデオサイズを取得
                first_frame = cv2.imread(os.path.join(out_dir, processed_files[0]))
                height, width = first_frame.shape[:2]
                
                # VideoWriterの初期化
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video = cv2.VideoWriter(video_path, fourcc, args.fps, (width, height))
                
                # 各フレームをビデオに追加
                for i, img_file in enumerate(processed_files):
                    img_path = os.path.join(out_dir, img_file)
                    frame = cv2.imread(img_path)
                    if frame is not None:
                        video.write(frame)
                    
                    # 進捗表示
                    if (i+1) % 30 == 0 or i+1 == len(processed_files):
                        print(f"Video progress: {i+1}/{len(processed_files)} frames ({(i+1)/len(processed_files)*100:.1f}%)")
                
                video.release()
                print(f"Video created successfully: {video_path}")
            else:
                print("No image files found to create video")
        except Exception as e:
            print(f"Error creating video: {e}")

if __name__ == '__main__':
    main()
