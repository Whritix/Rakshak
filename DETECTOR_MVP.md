# Satellite image object detector (hackathon MVP)

This is a real, trainable image detector using the xView annotations already in
`train_images/` and `train_labels/xView_train.geojson`. It groups xView's detailed
labels into four classes for a manageable first demo: **Vessel, Aircraft,
Vehicle, Infrastructure**. It does not need Indian AIS to detect objects.

## Run it

Use Python 3.10–3.13. In
PowerShell, from this project folder:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-detector.txt
python satellite_detector.py prepare
python satellite_detector.py train --device 0
python satellite_detector.py detect "train_images\109.tif"
```

Use `--device cpu` if no CUDA GPU is available. Training downloads the small
YOLO11 nano starting weights the first time if they are not already cached.
The trained checkpoint is saved under `runs/train/xview_hackathon/weights/best.pt`.
The detection command writes a sibling `*_detections.jpg` with boxes, class names,
and confidence scores; pass `--output path.jpg` to choose another location.

To preview a scene before detection, use the existing dataset explorer. Training
tiles are generated under `runs/xview_yolo/`; the preparation step keeps positive
tiles and a limited sample of empty tiles to control disk use. It keeps scenes
together when making the train/validation split.

## What to expect

## Current trained checkpoint

An initial 8-epoch GPU training run is available at
`runs/train/xview_hackathon/weights/best.pt`. It used 3,502 positive training
tiles and 855 positive validation tiles (plus sampled empty tiles), at 640 px,
starting from YOLO11n pretrained weights. The held-out split contains separate
source scenes. The overall validation metrics were precision **0.426**, recall
**0.357**, mAP@50 **0.332**, and mAP@50:95 **0.160**. Per-class mAP@50 was Vessel
**0.027**, Aircraft **0.588**, Vehicle **0.236**, Infrastructure **0.480**.
These are an early, short-run xView result, not operational accuracy. Vessel
performance is weak; do not use this checkpoint as a reliable boat detector.
See [TRAINING_REPORT.md](TRAINING_REPORT.md) for the full run details and an
example annotated validation scene.

## Improved vessel focused checkpoint

A separate YOLO11n vessel-only model has now been trained using 897 training
tiles and 183 held-out validation tiles. The current checkpoint is
`runs/train/xview_vessel_1024_extended/weights/best.pt`. Its best-epoch xView
metrics are precision **0.389**, recall **0.347**, mAP@50 **0.277**, and
mAP@50:95 **0.115**. This improves on the earlier four-class model's vessel
mAP@50 of 0.027, but recall remains low. It is a hackathon demonstration, not a
dependable detector. The model runs in the browser xView explorer through the
**Run vessel model** button; cyan is ground truth and amber is model output.
See [VESSEL_TRAINING_REPORT.md](VESSEL_TRAINING_REPORT.md) for the training
details, a held-out scene check, commands, and scope limits.

- xView imagery is much higher resolution than the supplied Sentinel-2 bands, so
  it is the right starting point for learning small objects such as boats, cars,
  and aircraft.
- Sentinel-2's 10 m bands can show coastlines, ports, and large changes, but not
  reliably identify small individual objects. This first model is trained on
  xView imagery and should not be described as a validated Sentinel-2 detector.
- The 378 local xView training TIFFs are only a subset of the labels: 469 labeled
  image IDs have no matching local training TIFF. The included validation TIFFs
  do not have labels, so this workflow creates its own held-out validation split
  from the labeled training scenes. Report its metrics as an initial demo result,
  not as a benchmark score.
- xView scenes are not India-specific. For dependable results on India imagery,
  add high-resolution India scenes with reviewed object boxes and test on a
  geographically separate India holdout. Indian AIS remains optional for object
  detection and becomes useful later for vessel-track association/evaluation.
- Predictions are visual suggestions for a human reviewer, not threat
  determinations or navigation guidance.

Class IDs are grouped using the original xView class list published by DIUx-xView:
[xView class labels](https://github.com/DIUx-xView/data_utilities/blob/master/xview_class_labels.txt).
