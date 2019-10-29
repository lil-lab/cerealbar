# TODO: Clean this code
import torch
from torch import nn as nn
from torch.nn import functional
from agent.model.map_transformations import util

PROFILE = False


class Affine2D(nn.Module):

    def __init__(self):
        super(Affine2D, self).__init__()
        self.is_cuda = False
        self.cuda_device = None

    def cuda(self, device=None):
        nn.Module.cuda(self, device)
        self.is_cuda = True
        self.cuda_device = device
        return self

    def forward(self, image, affine_mat, out_size=None):
        """
        Applies the given batch of affine transformation matrices to the batch of images
        :param image:   batch of images to transform
        :param affine:  batch of affine matrices to apply. Specified in image coordinates (internally converted to pytorch coords)
        :return:        batch of images of same size as the input batch with the affine matrix having been applied
        """

        batch_size = image.size(0)

        # Cut off the batch and channel to get the image size as the source size
        img_size = list(image.size())[2:4]
        if out_size is None:
            out_size = img_size

        affines_pytorch = util.image_affines_to_pytorch_cpu(affine_mat, img_size, out_size)

        if self.is_cuda:
            affines_pytorch = affines_pytorch.cuda(self.cuda_device)

        # Build the affine grid
        grid = functional.affine_grid(affines_pytorch[:, [0,1], :], torch.Size((batch_size, 1, out_size[0],
                                                                       out_size[1]))).float()

        # Rotate the input image
        rot_img = functional.grid_sample(image, grid, padding_mode="zeros")

        return rot_img
