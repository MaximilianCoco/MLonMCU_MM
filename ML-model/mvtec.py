from torchvision import transforms
from perlin import perlin_mask
from enum import Enum

import numpy as np
import pandas as pd

import PIL
import torch
import os


_CLASSNAMES = [
    "can", "fabric", "fruit_jelly", "rice",
    "sheet_metal", "vial", "wallplugs", "walnuts"
]

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class DatasetSplit(Enum):
    TRAIN = "train"
    TEST = "test_public"


class MVTecDataset(torch.utils.data.Dataset):

    def __init__(
        self,
        source,
        anomaly_source_path=None,
        dataset_name='mvtec',
        classname='can',
        resize=288,
        imagesize=288,
        split=DatasetSplit.TRAIN,
        rotate_degrees=0,
        translate=0,
        brightness_factor=0,
        contrast_factor=0,
        saturation_factor=0,
        gray_p=0,
        h_flip_p=0,
        v_flip_p=0,
        distribution=0,
        mean=0.5,
        std=0.1,
        fg=0,
        rand_aug=1,
        downsampling=8,
        scale=0,
        contamination_rate=0.0,
        **kwargs
    ):

        super().__init__()

        self.source = source
        self.split = split
        self.classname = classname
        self.dataset_name = dataset_name

        self.resize = resize
        self.imgsize = imagesize

        self.mean = mean
        self.std = std
        self.rand_aug = rand_aug
        self.downsampling = downsampling

        self.contamination_rate = contamination_rate if split == DatasetSplit.TRAIN else 0.0

        # SAFE: no external dataset required
        self.anomaly_source_paths = []

        self.imgpaths_per_class, self.data_to_iterate = self.get_image_data()

        # -------------------------
        # IMAGE TRANSFORM
        # -------------------------
        self.transform_img = transforms.Compose([
            transforms.Resize(self.resize),
            transforms.ColorJitter(brightness_factor, contrast_factor, saturation_factor),
            transforms.RandomHorizontalFlip(h_flip_p),
            transforms.RandomVerticalFlip(v_flip_p),
            transforms.RandomGrayscale(gray_p),
            transforms.RandomAffine(
                rotate_degrees,
                translate=(translate, translate),
                scale=(1.0 - scale, 1.0 + scale),
                interpolation=transforms.InterpolationMode.BILINEAR
            ),
            transforms.CenterCrop(self.imgsize),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])

        self.transform_mask = transforms.Compose([
            transforms.Resize(self.resize),
            transforms.CenterCrop(self.imgsize),
            transforms.ToTensor(),
        ])
    def __len__(self):
        return len(self.data_to_iterate)
    # ----------------------------------------------------------
    # SAFE AUGMENTER (PIL ONLY, NEVER TENSOR INPUT)
    # ----------------------------------------------------------
    def rand_augmenter(self):

        ops = [
            transforms.ColorJitter(contrast=(0.8, 1.2)),
            transforms.ColorJitter(brightness=(0.8, 1.2)),
            transforms.ColorJitter(saturation=(0.8, 1.2), hue=(-0.2, 0.2)),
            transforms.RandomHorizontalFlip(p=1),
            transforms.RandomVerticalFlip(p=1),
            transforms.RandomGrayscale(p=1),
            transforms.RandomAutocontrast(p=1),
            transforms.RandomEqualize(p=1),
            transforms.RandomAffine(degrees=(-45, 45)),
        ]

        idx = np.random.choice(len(ops), 3, replace=False)

        return transforms.Compose([
            transforms.Resize(self.resize),
            ops[idx[0]],
            ops[idx[1]],
            ops[idx[2]],
            transforms.CenterCrop(self.imgsize),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])

    # ----------------------------------------------------------
    # GET ITEM (FULLY SAFE)
    # ----------------------------------------------------------
    def __getitem__(self, idx):

        classname, anomaly, image_path, mask_path = self.data_to_iterate[idx]

        image_pil = PIL.Image.open(image_path).convert("RGB")
        image = self.transform_img(image_pil)

        # defaults
        aug_image = torch.zeros_like(image)
        mask_s = torch.zeros(1, self.imgsize, self.imgsize)

        # -------------------------
        # TRAIN
        # -------------------------
        if self.split == DatasetSplit.TRAIN:

            # safe fallback
            if len(self.anomaly_source_paths) > 0:
                aug_pil = PIL.Image.open(
                    np.random.choice(self.anomaly_source_paths)
                ).convert("RGB")
            else:
                aug_pil = image_pil.copy()

            if self.rand_aug:
                aug = self.rand_augmenter()(aug_pil)
            else:
                aug = self.transform_img(aug_pil)

            mask_fg = torch.ones(1, self.imgsize, self.imgsize)

            mask_all = perlin_mask(
                image.shape,
                self.imgsize // self.downsampling,
                0, 6,
                mask_fg,
                1
            )

            mask_s = torch.from_numpy(mask_all[0]).float()
            mask_l = torch.from_numpy(mask_all[1]).float()

            beta = np.clip(
                np.random.normal(self.mean, self.std),
                0.2, 0.8
            )

            aug_image = (
                image * (1 - mask_l)
                + (1 - beta) * aug * mask_l
                + beta * image * mask_l
            )

        # -------------------------
        # TEST MASK
        # -------------------------
        if self.split == DatasetSplit.TEST and mask_path is not None:
            mask_gt = PIL.Image.open(mask_path).convert("L")
            mask_gt = self.transform_mask(mask_gt)
        else:
            mask_gt = torch.zeros((1, self.imgsize, self.imgsize))

        return {
            "image": image,
            "aug": aug_image,
            "mask_s": mask_s,
            "mask_gt": mask_gt,
            "is_anomaly": int(anomaly != "good"),
            "image_path": image_path,
        }

    # ----------------------------------------------------------
    # DATA LOADING (FIXED FOR test_public)
    # ----------------------------------------------------------
    def get_image_data(self):
        imgpaths_per_class = {}
        maskpaths_per_class = {}

        train_path = os.path.join(self.source, self.classname, "train")
        test_path = os.path.join(self.source, self.classname, "test_public")
        gt_path = os.path.join(self.source, self.classname, "test_public", "ground_truth")

        imgpaths_per_class[self.classname] = {}
        maskpaths_per_class[self.classname] = {}

        # -----------------------
        # TRAIN (good + anomaly folders)
        # -----------------------
        for anomaly in os.listdir(train_path):
            anomaly_dir = os.path.join(train_path, anomaly)

            if not os.path.isdir(anomaly_dir):
                continue

            files = [
                os.path.join(anomaly_dir, f)
                for f in os.listdir(anomaly_dir)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
            ]

            if len(files) == 0:
                continue

            imgpaths_per_class[self.classname][anomaly] = files

        # -----------------------
        # TEST (IMPORTANT FIX)
        # -----------------------
        for anomaly in os.listdir(test_path):
            anomaly_dir = os.path.join(test_path, anomaly)

            if not os.path.isdir(anomaly_dir):
                continue

            # ❗ skip ground_truth folder completely
            if "ground_truth" in anomaly_dir:
                continue

            files = [
                os.path.join(anomaly_dir, f)
                for f in os.listdir(anomaly_dir)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
            ]

            if len(files) == 0:
                continue

            imgpaths_per_class[self.classname][anomaly] = files

            # -----------------------
            # GT HANDLING (MVTec2 style)
            # -----------------------
            gt_dir = os.path.join(gt_path, anomaly)

            if os.path.exists(gt_dir) and os.path.isdir(gt_dir):
                gt_files = [
                    os.path.join(gt_dir, f)
                    for f in os.listdir(gt_dir)
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
                ]
                maskpaths_per_class[self.classname][anomaly] = gt_files
            else:
                maskpaths_per_class[self.classname][anomaly] = None

        # -----------------------
        # FLATTEN
        # -----------------------
        data_to_iterate = []

        for anomaly, img_dict in imgpaths_per_class[self.classname].items():

            for i, image_path in enumerate(img_dict):

                # sanity check (VERY IMPORTANT)
                if not os.path.isfile(image_path):
                    continue

                item = [self.classname, anomaly, image_path]

                if (
                    self.split == DatasetSplit.TEST
                    and anomaly != "good"
                    and maskpaths_per_class[self.classname].get(anomaly) is not None
                ):
                    gt_list = maskpaths_per_class[self.classname][anomaly]
                    if i < len(gt_list):
                        item.append(gt_list[i])
                    else:
                        item.append(None)
                else:
                    item.append(None)

                data_to_iterate.append(item)

        # -----------------------
        # FINAL SAFETY CHECK (IMPORTANT)
        # -----------------------
        data_to_iterate = [
            x for x in data_to_iterate
            if os.path.isfile(x[2])
        ]

        return imgpaths_per_class, data_to_iterate