"""
config.py
read config from config.yaml
"""
import yaml
from tools.paths import app_path

class Config:
    def __init__(self):
        with open(app_path("config.yaml"), 'r') as f:
            config = yaml.safe_load(f)
        for i in config:
            setattr(self, i, config[i])


config = Config()
