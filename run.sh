export PYTHONPATH=/home/sumin/projects/aue8088:$PYTHONPATH
# yolov12s_kaist-rgbt.yaml
CUDA_VISIBLE_DEVICES=6 python train_simple.py \
  --img 640 \
  --batch-size 16 \
  --epochs 40 \
  --data data/kaist-rgbt.yaml \
  --cfg models/yolov12s_withTransformer.yaml \
  --weights 'yolov5x.pt' \
  --workers 16 \
  --optimizer SGD \
  --cos-lr \
  --hyp data/hyps/hyp.scratch-low.yaml \
  --name yolov12s_withTransformer \
  --entity $WANDB_ENTITY \
  --rgbt \
  --single-cls