#!/bin/bash
export HOME=/root/
source $HOME/.bashrc
source $HOME/conda/bin/activate
conda activate tali

cd $CODE_DIR
git pull
pip install -r $CODE_DIR/requirements.txt

source $CODE_DIR/setup_scripts/setup_base_experiment_disk.sh
source $CODE_DIR/setup_scripts/setup_wandb_credentials.sh

cd $CODE_DIR

fuser -k /dev/nvidia*; \
python $CODE_DIR/run.py \
hydra.verbose=True \
trainer=default \
resume=True \
batch_size=2 \
trainer.gpus=1 \
trainer.auto_scale_batch_size=True \
datamodule.dataset_config.rescan_paths=True \
datamodule.prefetch_factor=3 \
datamodule.num_workers=12 \
model=base_modus_prime_vi-transformer16 \
datamodule.dataset_config.dataset_size_identifier=milli \
datamodule.dataset_config.modality_config.image=True \
datamodule.dataset_config.modality_config.text=False \
datamodule.dataset_config.modality_config.audio=False \
datamodule.dataset_config.modality_config.video=True

