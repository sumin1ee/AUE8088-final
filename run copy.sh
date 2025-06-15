export PYTHONPATH=/home/sumin/projects/aue8088:$PYTHONPATH

CUDA_VISIBLE_DEVICES=0 python train_simple.py \
  --img 640 \
  --batch-size 16 \
  --epochs 30 \
  --data data/kaist-rgbt.yaml \
  --cfg models/yolov8n_kaist-rgbt_withAnchor.yaml \
  # --weights yolov5n.pt \
  --workers 16 \
  --optimizer SGD \
  --cos-lr \
  --hyp data/hyps/hyp.scratch-low.yaml \
  --name yolov8n_kaist-rgbt_withAnchor_noweights \
  --entity $WANDB_ENTITY \
  --rgbt \
  --single-cls