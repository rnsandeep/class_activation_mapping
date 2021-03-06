# -*- coding: utf-8 -*-

from __future__ import print_function, division
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
import numpy as np
import torchvision
from torchvision import datasets, models, transforms
import time
import os
from PIL import Image
import copy, cv2
import sys, shutil, pickle
from sklearn.metrics import classification_report, confusion_matrix
from os import listdir
from os.path import isfile, join
import torch.nn.functional as F
import scipy.ndimage
import matplotlib.pyplot as plt

mypath = sys.argv[1]

images = [os.path.join(mypath, f) for f in listdir(mypath) if isfile(join(mypath, f))]


mean = [0.4616, 0.4006, 0.3602]
std = [0.2287, 0.2160, 0.2085]

crop_size = int(sys.argv[3])

resize_size = int(sys.argv[4])
data_transform = transforms.Compose([
        transforms.Resize(resize_size),
        transforms.CenterCrop(crop_size),
        transforms.ToTensor(),
        transforms.Normalize(mean, std)
      ])

device =  torch.device("cuda:0" if torch.cuda.is_available() else "cpu") #"cpu"
print("device found:", device)

def load_model(path):
    model = torch.load(path)
    return model

def load_inputs_outputs(dataloaders):
    phase = 'val'
    for inputs, labels in dataloaders[phase]:
        inputs = inputs.to(device)
        labels = labels.to(device)
    return inputs, labels

def convert_to_numpy(x):
    return x.data.cpu().numpy()


def load_tensor_inputs(path, data_transforms):
    loader = data_transforms['test']
    image = Image.open(path[0])
    return loader(image)

def cv2_to_pil(img):
        """Returns a handle to the decoded JPEG image Tensor"""
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        im_pil = Image.fromarray(img)
        return im_pil

def eval_model(model, image):
    model.eval()   # Set model to evaluate mode
    inputs = image #np.zeros((299, 299, 3), np.uint8)
    inputs = cv2_to_pil(inputs)
    inputs = data_transform(inputs)
    image_shape = inputs.size()
    inputs = inputs.reshape((1, 3, image_shape[1], image_shape[2])).to(device)
    with torch.no_grad():
       outputs, cam = model(inputs)
    outputs = F.softmax(outputs, dim=1)
    cls_idx =  torch.argmax(outputs).item()
    return cls_idx, cam

def eval_all(images, model, flatten_weights, output_dir):
    for image in images:
        try:  
          image_np = cv2.imread(image)
          cls_idx, cam = eval_model(model, image_np)

          cam  = torch.squeeze(cam).permute(1,2,0) # reshape activation map from 2048x8x8 to 8x8x2048
          cam = convert_to_numpy(cam)
          fw = flatten_weights.data.cpu().numpy()[cls_idx]
          mat_for_mult = scipy.ndimage.zoom(cam, (32, 32, 1), order=1) # resize activation map to size of normal image to visualize.
          final_output = np.dot(mat_for_mult.reshape((224*224, 2048)), fw).reshape(224,224) # get the final activation map.

          image_224 = cv2.resize(image_np, (224,224))

          plt.imshow(image_224, alpha=0.5)
          plt.imshow(final_output, cmap='jet', alpha=0.5)
          plt.colorbar()
          plt.savefig(os.path.join(output_dir, os.path.basename(image)))
          plt.close()
        except Exception as ex:
            print(ex)
            print("reading failed for :", image)
        
    
def load_inception_model(model_path, num_classes):
    model_ft = models.resnet50(pretrained=True)
    num_ftrs = model_ft.fc.in_features
    model_ft.fc = nn.Linear(num_ftrs,num_classes)
    model = model_ft.to(device)
    checkpoint = load_model(model_path)
    model.load_state_dict(checkpoint['state_dict'])
    flatten_weights = model.fc.weight
    return model, flatten_weights


if __name__=="__main__":
    model_path = sys.argv[2]
    num_classes = int(sys.argv[5])
    output_dir = sys.argv[6]
    if not  os.path.exists(output_dir):
        os.makedirs(output_dir)

    model, flatten_weights = load_inception_model(model_path, num_classes)    

    since = time.time()
    eval_all(images, model, flatten_weights, output_dir)
              
    last = time.time()
    total_time = last-since
#    print("total time taken to process;", total_time, "per image:", total_time*1.0/len(cls_dict.keys()))
