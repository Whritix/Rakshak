# Vessel focused model and explorer demo

## What changed

The prototype now includes a vessel-only YOLO11n checkpoint trained on
the xView imagery already in this project. This addresses the original model's
class imbalance: the four-class model saw far fewer vessel boxes than
infrastructure boxes. Vessel training keeps the scene-level train/validation
separation from the prepared xView dataset, uses vessel-positive tiles plus a
sample of hard-negative tiles, and trains at 1024 px to preserve more small
object detail.

The xView browser at `http://127.0.0.1:8765/` now has a **Run vessel model**
action and confidence selector. Cyan boxes are supplied xView annotations;
amber boxes are predictions from the trained model. Inference runs locally on
the selected TIFF using 1024 px windows with 256 px overlap and global
duplicate suppression. The model loads the first time the button is used.

## Training record

- Current checkpoint: `runs/train/xview_vessel_1024_extended/weights/best.pt`
  (about 5.3 MiB).
- Training set: 897 tiles (299 vessel-positive and 598 sampled negatives).
- Validation set: 183 tiles (61 vessel-positive and 122 sampled negatives),
  with 449 vessel instances.
- Initial run: 30 epochs maximum, early stopping patience 8, 1024 px, batch 2,
  CUDA device 0; best checkpoint at epoch 25. It scored precision **0.469**,
  recall **0.238**, mAP@50 **0.210**, and mAP@50:95 **0.098**.
- Extended fine-tuning: initialized from the initial vessel checkpoint, 50
  epochs maximum and patience 12; early stopped at epoch 13. Its best checkpoint
  at epoch 1 scored precision **0.389**, recall **0.347**, mAP@50 **0.277**, and
  mAP@50:95 **0.115**. This is the current browser model.
- The prior four-class model's vessel mAP@50 was **0.027** on the same prepared
  xView validation split. The new model improves held-out tile metrics, but
  recall remains too low to call the detector dependable.

For a concrete held-out source-scene check, scene `109.tif` has 43 xView vessel
labels. At a low 0.05 confidence threshold, the model returned 25 candidates;
7 matched a vessel label at IoU >= 0.5 (precision 0.28, recall 0.16). This single
scene check is illustrative, not a substitute for a full independent evaluation.
At the UI's default 0.25 threshold, the initial model returned 11 candidates,
5 matches (precision 0.45, recall 0.12); the current extended model returned 9
candidates, 5 matches (precision 0.56, recall 0.12). At 0.05, the current model
returned 33 candidates, 8 matches (precision 0.24, recall 0.19). These are
single-scene comparisons. The model may miss vessels and produce false
positives; adjust the confidence threshold to review the precision/recall
tradeoff. Confidence is not a calibrated probability.

## Reproduce or run inference

From the project folder in PowerShell:

```powershell
# Rebuild the vessel-only subset if needed (uses the existing prepared tiles)
python satellite_detector.py prepare-vessel

# Train another run; the completed checkpoint is already available locally
python satellite_detector.py train --data .\runs\xview_vessel\data.yaml --name xview_vessel_1024 --weights .\yolo11n.pt --epochs 30 --imgsz 1024 --batch 2 --patience 8 --device 0

# Continue from the initial vessel model; this produced the current checkpoint
python satellite_detector.py train --data .\runs\xview_vessel\data.yaml --name xview_vessel_1024_extended --weights .\runs\train\xview_vessel_1024\weights\best.pt --epochs 50 --imgsz 1024 --batch 2 --patience 12 --device 0

# Run on an individual TIFF
python satellite_detector.py detect .\train_images\train_images\109.tif --model .\runs\train\xview_vessel_1024_extended\weights\best.pt --imgsz 1024 --conf 0.25

# Launch the browser demo
python dataset_explorer.py
```

The project virtual environment can be used with
`.\.venv\Scripts\python.exe` instead of `python`.

## Limits and next data needed

This checkpoint is trained on xView overhead imagery. It is **not** trained or
validated on Sentinel-2 pixels, Pipe V4 detections, or India-specific vessel
imagery. xView's held-out tiles come from the supplied xView scenes; a complete
geographic and temporal holdout is still needed. Sentinel-2's 10 m pixels
generally do not resolve individual small vessels, so this model must not be
presented as a Sentinel-2 vessel detector. The Pipe V4 CSV explorer remains a
separate published-detection overlay and does not label predictions from this
model.

Next useful resources are reviewed high-resolution India coastal satellite
chips with vessel bounding boxes and hard negatives; the same scenes with
acquisition timestamps; and a held-out region/month for independent evaluation.
Raw AIS tracks are useful later for time-and-location association, but are not
required to run image object detection. Provide provenance, usage rights,
coordinate reference, and class definitions with any new data. Keep reviewer
confirmation in the loop; candidate boxes are not threat assessments.
