
CUDA_VISIBLE_DEVICES=3 python train_simple.py \
  --img 640 \
  --batch-size 8 \
  --epochs 20 \
  --data data/kaist-rgbt.yaml \
  --cfg models/yolov5x_kaist-rgbt.yaml \
  --weights yolov5n.pt \
  --workers 16 \
  --name yolov5n-rgbt \
  --entity $WANDB_ENTITY \
  --rgbt \
  --single-cls
