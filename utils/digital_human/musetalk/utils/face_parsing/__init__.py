import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image

from .model import BiSeNet


class FaceParsing:
    def __init__(self, resnet_path, face_model_pth):
        self.resnet_path = resnet_path
        self.model_pth = face_model_pth

        self.net = self.model_init()
        self.preprocess = self.image_preprocess()

    def model_init(self):
        net = BiSeNet(self.resnet_path)
        if torch.cuda.is_available():
            net.cuda()
            net.load_state_dict(torch.load(self.model_pth))
        else:
            net.load_state_dict(torch.load(self.model_pth, map_location=torch.device("cpu")))
        net.eval()
        return net

    def image_preprocess(self):
        return transforms.Compose(
            [
                transforms.ToTensor(),
                transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
            ]
        )

    def __call__(self, image, size=(512, 512)):
        if isinstance(image, str):
            image = Image.open(image)

        width, height = image.size
        with torch.no_grad():
            image = image.resize(size, Image.BILINEAR)
            img = self.preprocess(image)
            if torch.cuda.is_available():
                img = torch.unsqueeze(img, 0).cuda()
            else:
                img = torch.unsqueeze(img, 0)
            out = self.net(img)[0]
            parsing = out.squeeze(0).cpu().numpy().argmax(0)
            parsing[np.where(parsing > 13)] = 0
            parsing[np.where(parsing >= 1)] = 255
        parsing = Image.fromarray(parsing.astype(np.uint8))
        return parsing


if __name__ == "__main__":
    fp = FaceParsing()
    segmap = fp("154_small.png")
    segmap.save("res.png")
