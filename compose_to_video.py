import os
import cv2
import argparse
import glob

def parse_args():
    parser = argparse.ArgumentParser(description="Compose PNG images in a folder into a video.")
    parser.add_argument('--input_dir', type=str, required=True, help='Directory containing PNG images')
    parser.add_argument('--output', type=str, default=None, help='Output video file (default: input_dir.mp4)')
    parser.add_argument('--fps', type=int, default=30, help='Frames per second (default: 30)')
    return parser.parse_args()

def main():
    args = parse_args()
    input_dir = args.input_dir
    fps = args.fps
    output = args.output
    if not os.path.isdir(input_dir):
        print(f"Input directory does not exist: {input_dir}")
        return
    png_files = sorted(glob.glob(os.path.join(input_dir, '*.png')))
    if not png_files:
        print(f"No PNG files found in {input_dir}")
        return
    # 出力ファイル名の決定
    if not output:
        base = os.path.basename(os.path.normpath(input_dir))
        output = base + '.mp4'
    # 最初の画像でサイズ決定
    first_img = cv2.imread(png_files[0])
    if first_img is None:
        print(f"Failed to read first image: {png_files[0]}")
        return
    height, width = first_img.shape[:2]
    size = (width, height)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output, fourcc, fps, size)
    print(f"Writing video: {output} ({len(png_files)} frames, {fps} fps, size={size})")
    for i, img_path in enumerate(png_files, 1):
        img = cv2.imread(img_path)
        if img is None:
            print(f"Warning: failed to read {img_path}, skipping.")
            continue
        if img.shape[:2] != (height, width):
            img = cv2.resize(img, size)
        out.write(img)
        if i % 50 == 0 or i == len(png_files):
            print(f"Progress: {i}/{len(png_files)} frames")
    out.release()
    print(f"Done! Video saved to: {output}")

if __name__ == '__main__':
    main()
