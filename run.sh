
CUDA_VISIBLE_DEVICES=2 python train_simple.py \
  --img 640 \
  --batch-size 8 \
  --epochs 80 \
  --data data/kaist-rgbt.yaml \
  --cfg models/yolov12_kaist-rgbt.yaml \
  --weights yolov5n.pt \
  --workers 16 \
  --optimizer AdamW \
  --cos-lr \
  --name yolov12x_mosaic_mixup \
  --entity $WANDB_ENTITY \
  --rgbt \
  --single-cls