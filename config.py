import os
import tensorflow as tf

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MIXPRECISION = False
BACKBONE = "mobilenetv2"
RANDOM_SEED = 1234
IMG_SIZE = 550
PROTO_OUTPUT_SIZE = 138

# Adding any backbone u want as long as the output size are: (69, 69), (35, 35), (18, 18) [if using 550 as img size]
backbones_objects = dict({
    "resnet50": tf.keras.applications.ResNet50(input_shape=(IMG_SIZE, IMG_SIZE, 3),
                                               include_top=False,
                                               layers=tf.keras.layers,
                                               weights='imagenet'),
    "resnet101": tf.keras.applications.ResNet101(input_shape=(IMG_SIZE, IMG_SIZE, 3),
                                                 include_top=False,
                                                 layers=tf.keras.layers,
                                                 weights='imagenet'),

    "mobilenetv2": tf.keras.applications.MobileNetV2(input_shape=(IMG_SIZE, IMG_SIZE, 3),
                                                     include_top=False,
                                                     layers=tf.keras.layers,
                                                     weights='imagenet'),

    "efficientNet-B0": tf.keras.applications.EfficientNetB0(input_shape=(IMG_SIZE, IMG_SIZE, 3),
                                                            include_top=False,
                                                            weights='imagenet')

})

# Extract the layer have following: (69, 69), (35, 35), (18, 18) [if using 550 as img size]
# I just randomly choose layers for efficeintNet and MobilNetV2 just to get same shape
backbones_extracted = dict({
    "resnet50": ['conv3_block4_out', 'conv4_block6_out', 'conv5_block3_out'],
    "resnet101": ['conv3_block4_out', 'conv4_block23_out', 'conv5_block3_out'],
    "mobilenetv2": ['block_5_add', 'block_7_add', 'block_14_add'],
    "efficientNet-B0": ['block3b_add', 'block4c_add', 'block6d_add']
})

# RGB values of color for drawing nice bounding boxes
COLORS = ((244, 67, 54),
          (233, 30, 99),
          (156, 39, 176),
          (103, 58, 183),
          (63, 81, 181),
          (33, 150, 243),
          (3, 169, 244),
          (0, 188, 212),
          (0, 150, 136),
          (76, 175, 80),
          (139, 195, 74),
          (205, 220, 57),
          (255, 235, 59),
          (255, 193, 7),
          (255, 152, 0),
          (255, 87, 34),
          (121, 85, 72),
          (158, 158, 158),
          (96, 125, 139))

# Class names for COCO dataset
COCO_CLASSES = ('person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
                'train', 'truck', 'boat', 'traffic light', 'fire hydrant',
                'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog',
                'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe',
                'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
                'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat',
                'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
                'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
                'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot',
                'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
                'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
                'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven',
                'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase',
                'scissors', 'teddy bear', 'hair drier', 'toothbrush')

# mapping coco classes labels from 90 to 80
COCO_LABEL_MAP = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8,
                  9: 9, 10: 10, 11: 11, 13: 12, 14: 13, 15: 14, 16: 15, 17: 16,
                  18: 17, 19: 18, 20: 19, 21: 20, 22: 21, 23: 22, 24: 23, 25: 24,
                  27: 25, 28: 26, 31: 27, 32: 28, 33: 29, 34: 30, 35: 31, 36: 32,
                  37: 33, 38: 34, 39: 35, 40: 36, 41: 37, 42: 38, 43: 39, 44: 40,
                  46: 41, 47: 42, 48: 43, 49: 44, 50: 45, 51: 46, 52: 47, 53: 48,
                  54: 49, 55: 50, 56: 51, 57: 52, 58: 53, 59: 54, 60: 55, 61: 56,
                  62: 57, 63: 58, 64: 59, 65: 60, 67: 61, 70: 62, 72: 63, 73: 64,
                  74: 65, 75: 66, 76: 67, 77: 68, 78: 69, 79: 70, 80: 71, 81: 72,
                  82: 73, 84: 74, 85: 75, 86: 76, 87: 77, 88: 78, 89: 79, 90: 80}

# Class names for Pascal dataset
PASCAL_CLASSES = ("aeroplane", "bicycle", "bird", "boat", "bottle",
                  "bus", "car", "cat", "chair", "cow", "diningtable",
                  "dog", "horse", "motorbike", "person", "pottedplant",
                  "sheep", "sofa", "train", "tvmonitor")

TRAIN_ITER = dict({
    "coco": 800000,
    "pascal": 10000,
    "your_custom_dataset": 0
})

NUM_CLASSES = dict({
    "coco": 81,
    "pascal": 21,
    "your_custom_dataset": 0
})

LR_STAGE = dict({
    "coco": {'warmup_steps': 500,
             'warmup_lr': 1e-4,
             'initial_lr': 1e-3,
             'stages': [280000, 600000, 700000, 750000],
             'stage_lrs': [1e-3, 1e-4, 1e-5, 1e-6, 1e-7]},

    "pascal": {'warmup_steps': 500,
               'warmup_lr': 1e-4,
               'initial_lr': 1e-3,
               'stages': [60000, 100000],
               'stage_lrs': [1e-3, 1e-4, 1e-5]},

    "your_custom_dataset": {}
})

ANCHOR = dict({
    "coco": {"img_size": IMG_SIZE,
             "feature_map_size": [69, 35, 18, 9, 5],
             "aspect_ratio": [1, 0.5, 2],
             "scale": [24, 48, 96, 192, 384]},

    "pascal": {"img_size": IMG_SIZE,
               "feature_map_size": [69, 35, 18, 9, 5],
               "aspect_ratio": [1, 0.5, 2],
               "scale": [24 * (4 / 3), 48 * (4 / 3), 96 * (4 / 3), 192 * (4 / 3), 384 * (4 / 3)]},

    "your_custom_dataset": {}
})

LABEL_MAP = dict({
    "coco": COCO_LABEL_MAP,
    "pascal": None,
    "your_custom_dataset": None
})


def get_params(dataset_name):
    parser_params = {
        "output_size": IMG_SIZE,
        "proto_out_size": PROTO_OUTPUT_SIZE,
        "num_max_padding": 100,
        "augmentation_params": {
            # These are in RGB and are for ImageNet
            "mean": (0.407, 0.457, 0.485),
            "std": (0.225, 0.224, 0.229),
            "output_size": IMG_SIZE,
            "proto_output_size": PROTO_OUTPUT_SIZE,
            "discard_box_width": 4. / 550.,
            "discard_box_height": 4. / 550.,
        },
        "matching_params": {
            "threshold_pos": 0.5,
            "threshold_neg": 0.4,
            "threshold_crowd": 0.7
        },
        "label_map": LABEL_MAP[dataset_name]
    }

    detection_params = {
        "num_cls": NUM_CLASSES[dataset_name],
        "label_background": 0,
        "top_k": 200,
        "conf_threshold": 0.05,
        "nms_threshold": 0.5,
    }

    loss_params = {
        "loss_weight_cls": 1,
        "loss_weight_box": 1.5,
        "loss_weight_mask": 6.125,
        "loss_weight_seg": 1,
        "neg_pos_ratio": 3,
        "max_masks_for_train": 100
    }

    lrs_schedule_params = LR_STAGE[dataset_name]
    anchor_params = ANCHOR[dataset_name]

    model_params = {
        "backbone": BACKBONE,
        "fpn_channels": 256,
        "num_class": NUM_CLASSES[dataset_name],
        "num_mask": 32,
        "anchor_params": anchor_params,
        "detect_params": detection_params,
    }

    return TRAIN_ITER[dataset_name], IMG_SIZE, NUM_CLASSES[dataset_name], \
           lrs_schedule_params, loss_params, parser_params, model_params
