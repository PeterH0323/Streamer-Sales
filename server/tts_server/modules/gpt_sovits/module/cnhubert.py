import logging

import torch.nn as nn
from transformers import HubertModel, Wav2Vec2FeatureExtractor

logging.getLogger("numba").setLevel(logging.WARNING)


class CNHubert(nn.Module):
    def __init__(self, cnhubert_base_path):
        super().__init__()
        self.model = HubertModel.from_pretrained(cnhubert_base_path)
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(cnhubert_base_path)

    def forward(self, x):
        input_values = self.feature_extractor(x, return_tensors="pt", sampling_rate=16000).input_values.to(x.device)
        feats = self.model(input_values)["last_hidden_state"]
        return feats


def get_model(cnhubert_base_path):
    model = CNHubert(cnhubert_base_path)
    model.eval()
    return model
