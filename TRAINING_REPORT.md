# Initial xView detector training report

## Run summary

- Model: YOLO11n, initialized from the public pretrained `yolo11n.pt` weights.
- Training device: NVIDIA GeForce RTX 4060 Laptop GPU (CUDA 12.8).
- Dataset: local xView TIFFs and `train_labels/xView_train.geojson`.
- Input size: 640 px; batch size: 4; epochs completed: 8.
- Split: scene-level 80/20 split, seed 42; 376 labeled source scenes were usable
  for the selected classes.
- Prepared tiles: 3,502 positive training tiles and 855 positive validation
  tiles, plus sampled empty tiles (4,377 training and 1,068 validation images
  total).
- Best checkpoint: `runs/train/xview_hackathon/weights/best.pt`.
- Training curves and logs: `runs/train/xview_hackathon/results.csv` and the
  accompanying plots in that folder.

## Validation results

| Class | Precision | Recall | mAP@50 | mAP@50:95 |
|---|---:|---:|---:|---:|
| All classes | 0.429 | 0.358 | 0.333 | 0.160 |
| Vessel | 0.091 | 0.087 | 0.027 | 0.012 |
| Aircraft | 0.628 | 0.593 | 0.588 | 0.358 |
| Vehicle | 0.390 | 0.328 | 0.236 | 0.058 |
| Infrastructure | 0.608 | 0.422 | 0.480 | 0.211 |

This is an initial short-run result, not a benchmark claim. Vessel scores are
especially poor, so the model should not be presented as a dependable vessel
detector. xView is not India-specific and is higher-resolution than Sentinel-2;
these metrics do not measure accuracy on the project’s Sentinel-2 imagery.
The 732 predictions on the example validation scene at confidence 0.35 are
inference output, not 732 confirmed objects.

## Example inference

The sliding-window detector was run on xView scene `1141.tif`, a held-out source
scene. Its annotated output is
`runs/train/xview_hackathon/validation_scene_1141_detections.jpg`.

Run inference on another xView TIFF:

```powershell
python satellite_detector.py detect "train_images\train_images\109.tif" --model "runs\train\xview_hackathon\weights\best.pt"
```

## Next improvement

Train longer at a larger input size, review the class mapping and tile labels,
and prioritize vessel examples and hard negatives. Before claiming India or
Sentinel-2 performance, assemble reviewed labels for a geographically separate
India holdout and evaluate it independently. The Sentinel-2 explorer currently
shows published Pipe V4 provider detections; it does not call this YOLO model.
