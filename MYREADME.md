# XMem 補足ユーティリティガイド

## モザイク処理ツール (mosaic.py)

動画トラッキングで作成されたマスクを使って元の画像にモザイクやぼかし等の効果を適用するツールです。

### 基本的な使い方

```bash
python mosaic.py --video_name <ビデオ名> [オプション]
```

### 必須パラメータ
- `--video_name`: 処理対象のビデオ名（workspaceフォルダ内のサブフォルダ名）

### オプションパラメータ
- `--mosaic_size`: モザイクのブロックサイズ（大きいほど粗いモザイク、デフォルト: 20）
- `--dilate`: マスク領域を膨張させるピクセル数（デフォルト: 0）
- `--blur`: マスク輪郭のぼかし度合い（奇数、0でぼかしなし、デフォルト: 0）
- `--mosaic_type`: モザイク種類（下記参照、デフォルト: 'pixel'）
- `--color`: 色指定（color タイプ使用時、形式: '255,0,0'、デフォルト: '0,0,0'）
- `--blur_strength`: ぼかし強度（blur タイプ使用時、奇数、デフォルト: 21）

### モザイク種類
- `pixel`: 標準的なピクセル化モザイク
- `blur`: ガウシアンぼかし処理
- `black`: 黒で塗りつぶし
- `color`: 指定した色で塗りつぶし
- `noise`: ランダムノイズパターン

### 使用例
```bash
# 基本的な使い方（デフォルトのピクセルモザイク）
python mosaic.py --video_name ComfyUI_00661_ --mosaic_size 30 --dilate 5 

# ぼかし効果を適用
python mosaic.py --video_name ComfyUI_00661_ --mosaic_type blur --blur_strength 31 --dilate 5

# 赤色で塗りつぶし
python mosaic.py --video_name ComfyUI_00661_ --mosaic_type color --color 255,0,0 --dilate 10

# ランダムノイズ
python mosaic.py --video_name ComfyUI_00661_ --mosaic_type noise --dilate 5
```

### 出力先
処理された画像は `workspace\<video_name>\mosaic\<日時>\` フォルダに保存されます。

---

## 画像リサイズツール (resize.py)

フォルダ内の全画像を一括でリサイズするツールです。

### 基本的な使い方

```bash
python resize.py --input_dir <入力ディレクトリ> [オプション]
```

### 必須パラメータ
- `--input_dir`: リサイズする画像が入ったディレクトリ

### オプションパラメータ
- `--scale`: リサイズ倍率（1.0で等倍、0.5で半分、2.0で倍、デフォルト: 0.5）
- `--output_dir`: 出力先ディレクトリ（指定しない場合は自動生成）

### 使用例
```bash
# 画像を80%サイズにリサイズ
python resize.py --input_dir workspace\ComfyUI_00661_\mosaic\20250622_232837 --scale 0.8

# 画像を50%サイズにリサイズして特定のフォルダに出力
python resize.py --input_dir workspace\ComfyUI_00661_\mosaic\20250622_232837 --scale 0.5 --output_dir my_resized_images
```

### 出力先
リサイズされた画像は、指定した出力ディレクトリ、または指定しない場合は `resized_[scale]x_[日時]` という名前のフォルダに保存されます。