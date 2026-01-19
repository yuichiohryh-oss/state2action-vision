# state2action-vision

## 概要
state2action-vision は、縦長のプレイ動画から画面状態（盤面領域、候補UIスロット、リソースゲージ、時間UIなど）を抽出し、次の行動を多クラス分類として予測する模倣学習パイプラインです。推論は top-k 提案を返し、action mask と NOOP penalty で無効な提案を抑制します。用語は一般化し、固有名詞は使いません。

## セットアップ
- Python: 3.11
- OS: 開発は Windows、CI は Linux
- 依存: ffmpeg を PATH に追加、OpenCV でフレーム処理

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

## クイックスタート（想定CLI名）
```powershell
s2a-build-dataset `
  --videos data/raw/videos `
  --events data/raw/events/events.jsonl `
  --preset configs/presets/vertical_720p.yaml `
  --frames-out data/derived/frames `
  --out data/derived/datasets/dataset.jsonl

s2a-train-policy `
  --dataset data/derived/datasets/dataset.jsonl `
  --out data/models/policy.ckpt

s2a-predict-policy `
  --checkpoint data/models/policy.ckpt `
  --input data/derived/frames/v001/00012345.png `
  --topk 5
```

## データ形式
events.jsonl（人手ラベル）:
```json
{"video_id":"v001","t_ms":12345,"action_id":17,"tap_xy_rel":[0.52,0.73],"candidate_slot":2}
{"video_id":"v001","t_ms":12780,"action_id":3,"tap_xy_rel":[0.31,0.81],"candidate_slot":0}
```

dataset.jsonl（フレーム+ラベル+補助特徴）:
```json
{"image_path":"data/derived/frames/v001/00012345.png","action_id":17,"tap_xy_rel":[0.52,0.73],"candidate_mask":[1,0,1,1],"resource_gauge":0.64,"time_remaining_s":52.3,"grid_id":"vertical_720p:v1"}
{"image_path":"data/derived/frames/v001/00012780.png","action_id":3,"tap_xy_rel":[0.31,0.81],"candidate_mask":[1,1,0,1],"resource_gauge":0.21,"time_remaining_s":49.8,"grid_id":"vertical_720p:v1"}
```

## ROIとグリッド設計
- ROI座標は 0..1 の相対値で保存し、解像度差に強くする。
- preset YAML に ROI矩形、スロット配置、レイアウト情報をまとめる。
- `inspect_roi` で新規 preset を検証してからデータ生成する。

## 評価
- Baseline: 多数派クラス、ランダム top-k。
- 指標: top-k 精度、macro F1、混同行列。
- 破綻率: action mask と NOOP penalty 適用後の無効提案率。

## トラブルシュート
- events とフレームの時刻ズレ: FPS と `t_ms` 変換を確認。
- ROIずれ: preset YAML と ROIオーバーレイを再検証。
- 空フレーム: ffmpeg 抽出と crop 範囲を確認。
- 候補UI無効: 可用性マスクの判定を確認。
- リソースゲージが不安定: 正規化条件を preset ごとに見直す。

## Directory Layout
```
repo/
  README.md
  PROJECT_STATE.md
  AGENTS.md
  pyproject.toml
  src/
    state2action_vision/
      __init__.py
      config/
      dataset/
      vision/
      learning/
      inference/
      utils/
  tools/
    build_dataset.py
    train_policy.py
    predict_policy.py
    inspect_roi.py
    export_frames.py
  tests/
    test_dataset_io.py
    test_model_forward.py
    test_cli_smoke.py
  configs/
    presets/
      vertical_720p.yaml
      vertical_1080p.yaml
    schemas/
  assets/
    templates/
      candidates_ui/
        README.md
        v1/
          slot_0.png
          slot_1.png
    docs/
  data/
    README.md
    raw/
      videos/
      events/
    derived/
      datasets/
      frames/
      caches/
    models/
    reports/
```
templates は `assets/templates/`、raw videos/events は `data/raw/`、datasets/frames は `data/derived/`、checkpoints は `data/models/`、評価レポートは `data/reports/` に置きます。

## assets/templates のルール
`slot_0.png`、`slot_1.png` のように命名し、`assets/templates/candidates_ui/vN/` 配下でバージョン管理します。既存バージョンは上書きせず、新規バージョンを追加して preset 側の参照を更新し、再現性を維持します。

## 版権/データ取り扱い
固有名詞や識別可能な素材は扱わない方針です。raw動画とイベントラベルは非公開前提とし、`data/` の内容は `data/README.md` 以外コミットしません。
