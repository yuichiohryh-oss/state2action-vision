# PROJECT_STATE

## ゴール
- v0 (MVP): jsonl データセットIO、ROI preset、補助特徴抽出（リソースゲージ、候補UI可用性/内容、時間UI）、多クラス行動分類、action mask と NOOP penalty を用いた top-k 推論、CLIツール、スモークテスト。
- v1: 候補UIの内容推定強化（テンプレ段階から学習へ）、評価レポート、解像度別 preset、データセットのバージョニングとスキーマ検証。
- v2: 推論品質の改善、キャリブレーション、運用監視の整備。

## データフロー
video -> events -> dataset -> train -> predict
- video: 縦長画面録画。
- events: 人手ラベルの行動と時刻。
- dataset: フレームパス + ラベル + 補助特徴の jsonl。
- train: 行動分類器の学習。
- predict: action mask とペナルティを含む top-k 提案。

## 主要モジュール
- `src/state2action_vision/config`: preset 読み込み、スキーマ検証、既定値。
- `src/state2action_vision/dataset`: jsonl IO、フレーム抽出、ラベルマッピング。
- `src/state2action_vision/vision`: ROI抽出、テンプレ処理、補助特徴推定。
- `src/state2action_vision/learning`: モデル、損失、学習ループ、指標。
- `src/state2action_vision/inference`: top-k、action mask、NOOP penalty。
- `src/state2action_vision/utils`: ログ、シード、IO補助。

## ツール
- `tools/build_dataset.py`: raw動画+events からフレームと補助特徴を生成し dataset jsonl を出力。
- `tools/train_policy.py`: 分類器を学習し `data/models/` に保存。
- `tools/predict_policy.py`: 単一入力で top-k 提案を出力。
- `tools/inspect_roi.py`: ROI とグリッド preset の検証。
- `tools/export_frames.py`: ラベル作成/QA用のフレーム書き出し。
- `tools/validate_jsonl.py`: events/dataset の jsonl バリデーション。

## 優先度
- P0: データセットスキーマ、preset駆動ROI、ベースライン分類器、推論の action mask、スモークテスト。
- P1: 候補UI内容推定の改善、評価レポート、preset検証の自動化。
- P2: スケール対応、監視、モデル軽量化、ツール整備。

## 直近ToDo
- `events.jsonl` と `dataset.jsonl` のスキーマ定義とバリデータ実装。
- ROI preset 読み込みと `inspect_roi` の可視化。
- データセット生成（フレーム抽出、補助特徴、jsonl 出力）。
- ベースライン分類器と top-k 推論、action mask の実装。
- `tests/test_dataset_io.py` と CLI スモークテスト追加。

## 計測と評価
- Baseline: 多数派クラス、ランダム top-k。
- 分類指標: macro F1、混同行列、top-k 精度。
- 破綻率: action mask + NOOP penalty 適用後の無効提案率。
- 安定性: 解像度 preset 別、候補UI可用性別の精度。

## 将来拡張（今やらない）
- 今やらない: 盤面の物体検出/追跡のフル導入。
- 今やらない: 候補UI内容の完全な end-to-end 学習。
- 今やらない: 相手側リソース推定や長期計画。

## Repository layout
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

## Repository Layout Rules
- `assets/` は追跡対象で、再利用可能かつ識別不能なテンプレ/ドキュメントのみ。
- `data/` はローカル専用で、`data/README.md` 以外はコミットしない。
- ROI/グリッド変更時は `configs/presets/` に新しい preset YAML を追加し、必要ならスキーマも更新。
- `inspect_roi` で検証し、本ファイルの「ROI/Grid検証メモ」に短い検証メモを残す。

## ROI/Grid検証メモ
- （preset 変更時に記入）
