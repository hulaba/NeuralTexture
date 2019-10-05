import argparse
import numpy as np
import os
import sys
import torch
from torch.utils.data import DataLoader
import torchvision.transforms as transforms

import config
from dataset.eval_dataset import EvalDataset
from model.renderer import Renderer

parser = argparse.ArgumentParser()
parser.add_argument('--pyramidw', type=int, default=config.PYRAMID_W)
parser.add_argument('--pyramidh', type=int, default=config.PYRAMID_H)
parser.add_argument('--data', type=str, default=config.TEST_DATA_DIR, help='directory to data')
parser.add_argument('--test', default=config.TEST_SET, help='index list of test uv_maps')
parser.add_argument('--save', type=str, default=config.SAVE_DIR, help='save directory')
parser.add_argument('--checkpoint', type=str, default=config.CHECKPOINT_DIR, help='directory to save checkpoint')
parser.add_argument('--load', type=str, default=config.TEST_LOAD, help='checkpoint name')
parser.add_argument('--batch', type=int, default=config.BATCH_SIZE)
args = parser.parse_args()


if __name__ == '__main__':

    checkpoint_file = os.path.join(args.checkpoint, args.load)
    if not os.path.exists(checkpoint_file):
        print('checkpoint not exists!')
        sys.exit()

    if not os.path.exists(args.save):
        os.makedirs(args.save)

    dataset = EvalDataset(args.data, args.test)
    dataloader = DataLoader(dataset, batch_size=args.batch, shuffle=False, num_workers=4, collate_fn=EvalDataset.collect_fn)

    model = Renderer(args.pyramidw, args.pyramidh)
    model = model.to('cuda')
    model.texture.layer1 = model.texture.layer1.cuda()
    model.texture.layer2 = model.texture.layer2.cuda()
    model.texture.layer3 = model.texture.layer3.cuda()
    model.texture.layer4 = model.texture.layer4.cuda()
    model.load(checkpoint_file)
    model.eval()
    torch.set_grad_enabled(False)

    print('Evaluating started')
    for samples in dataloader:
        uv_maps, masks, idxs = samples
        preds = model(uv_maps.cuda()).cpu()
        preds.masked_fill_(masks, 0) # fill invalid with 0
        for i in range(len(idxs)):
            image = transforms.ToPILImage()(preds[i])
            image.save(os.path.join(args.save, '{}_render.png'.format(idxs[i])))