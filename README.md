# class_activation_mapping
Visualise Class activation mapping.

Visualize the maps using inception v3 model trained on own data.


Usage: python3 inceptionv3_cam.py path/to/images_folder path/to/inception_checkpoint.pth.tar 299 299 num_classes folder/to/saveImages

changes to the original torch vision inception.py.


Thanks to https://alexisbcook.github.io/2017/global-average-pooling-layers-for-object-localization/
