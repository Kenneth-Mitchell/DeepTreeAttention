#Test semi_supervised.py
from pytorch_lightning import Trainer
from src import semi_supervised
from src.models import Hang2020
import pytest

@pytest.fixture()
def m(dm, config, ROOT):    
    m = Hang2020.spectral_network(bands=config["bands"], classes=dm.num_classes)    
    
    return m

def test_fit(config, m, dm):
    config["semi_supervised"]["crop_dir"] = config["crop_dir"]
    dm.train = semi_supervised.create_dataframe(config, m=m)
    trainer = Trainer(fast_dev_run=False, max_epochs=1, limit_train_batches=1, enable_checkpointing=False, num_sanity_val_steps=0)
    
    #Model can be trained and validated
    trainer.fit(m)
    metrics = trainer.validate(m)