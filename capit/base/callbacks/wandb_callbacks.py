import os
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pytorch_lightning
from omegaconf import DictConfig
from pytorch_lightning import Callback, LightningModule, Trainer
from pytorch_lightning.callbacks import ModelSummary
from pytorch_lightning.loggers import LoggerCollection, WandbLogger
from pytorch_lightning.utilities import rank_zero_only
from torch.optim import Optimizer

import wandb
from capit.base import utils

logger = utils.get_logger(__name__)


def get_wandb_logger(trainer: Trainer) -> WandbLogger:
    """Safely get Weights&Biases logger from Trainer."""

    if trainer.fast_dev_run:
        raise ValueError(
            "Cannot use wandb callbacks since pytorch lightning disables loggers in "
            "`fast_dev_run=true` mode."
        )

    if isinstance(trainer.logger, WandbLogger):
        return trainer.logger

    if isinstance(trainer.logger, LoggerCollection):
        for logger in trainer.logger:
            if isinstance(logger, WandbLogger):
                return logger

    raise ValueError(
        "You are using wandb related callback, but WandbLogger was not found for "
        "some reason..."
    )


class UploadCodeAsArtifact(Callback):
    """Upload all code files to wandb as an artifact, at the beginning of the run."""

    def __init__(self, code_dir: str):
        """

        Args:
            code_dir: the code directory
            use_git: if using git, then upload all files that are not ignored by git.
            if not using git, then upload all '*.py' file
        """
        self.code_dir = code_dir

    @rank_zero_only
    def on_train_start(self, trainer: Trainer, pl_module: LightningModule):
        logger = get_wandb_logger(trainer=trainer)
        experiment = logger.experiment

        code = wandb.Artifact("project-source", type="code")

        for path in Path(self.code_dir).resolve().rglob("*.py"):
            code.add_file(str(path), name=str(path.relative_to(self.code_dir)))

        experiment.log_artifact(code)


class LogConfigInformation(Callback):
    """Logs a validation batch and their predictions to wandb.
    Example adapted from:
        https://wandb.ai/wandb/wandb-lightning/reports/Image-Classification-using-PyTorch-Lightning--VmlldzoyODk1NzY
    """

    def __init__(self, exp_config: DictConfig = None):
        super().__init__()
        self.done = False
        self.exp_config = exp_config

    @rank_zero_only
    def on_batch_start(self, trainer: Trainer, pl_module: LightningModule) -> None:
        if not self.done:
            logger = get_wandb_logger(trainer=trainer)

            trainer_hparams = trainer.__dict__.copy()

            hparams = {
                "trainer": trainer_hparams,
                "config": self.exp_config,
            }

            logger.log_hyperparams(hparams)
            self.done = True
