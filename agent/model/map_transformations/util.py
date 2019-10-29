"""TODO: Documentation for this script.

This code is adapted from Blukis et al. 2018.
"""
import numpy as np
import torch
from torch import autograd
from transforms3d import euler

from agent.model.map_transformations import pose


def pos_m_to_px(as_coords, img_size_px, world_size_m, world_size_px=None, world_origin=None):
    img_size_px = np.asarray(img_size_px)
    # Be default, assume that the image is of the entire environment
    if world_size_px is None:
        world_size_px = img_size_px
    # By default assume that the image is a picture of the entire environment
    if world_origin is None:
        world_origin = np.array([0.0, 0.0])

    if type(world_size_px) not in [int, float]:
        world_size_px = np.asarray(world_size_px)
    world_origin = np.asarray(world_origin)

    scale = world_size_px / world_size_m

    if hasattr(as_coords, "is_cuda"):
        world_origin = torch.from_numpy(world_origin).float()
        as_coords = as_coords.float()
        if as_coords.is_cuda:
            world_origin = world_origin.cuda()
        if type(as_coords) is autograd.Variable:
            world_origin = autograd.Variable(world_origin)

    out_coords = as_coords * scale
    out_coords = out_coords + world_origin

    return out_coords


def poses_m_to_px(as_pose, img_size_px, world_size_px, world_size_m, batch_dim=False):
    world_size_px = np.asarray(world_size_px)
    pos = as_pose.position
    rot = as_pose.orientation

    # Turn into numpy
    if hasattr(pos, "is_cuda"):
        pos = pos.data.cpu().numpy()
        rot = rot.data.cpu().numpy()

    if len(pos.shape) == 1:
        pos = pos[np.newaxis, :]

    pos_img = pos_m_to_px(pos[:, 0:2], img_size_px, world_size_m, world_size_px)

    yaws = []
    if batch_dim:
        for i in range(rot.shape[0]):
            # Manual quat2euler
            yaw = rot[i]
            yaws.append(yaw)
    else:
        roll, pitch, yaw = euler.quat2euler(rot)
        yaws.append(yaw)
        pos_img = pos_img[0]

    if batch_dim:
        # Add additional axis so that orientation becomes Bx1 instead of just B,
        out = pose.Pose(pos_img, np.asarray(yaws)[:, np.newaxis])
    else:
        out = pose.Pose(pos_img, yaws[0])

    return out


def np_to_tensor(np_tensor, insert_batch_dim=True, var=True, cuda=False):
    if isinstance(np_tensor, np.ndarray):
        tensor = torch.from_numpy(np_tensor).float()
    else:  # Probably a lone float
        tensor = torch.FloatTensor([np_tensor])

    if insert_batch_dim:
        tensor = torch.unsqueeze(tensor, 0)
    if cuda:
        tensor = tensor.cuda()
    if var:
        tensor = autograd.Variable(tensor)
    return tensor


def get_affine_translation_2d(trans_vec, batch=False):
    if batch:
        out1 = np.eye(3)
        out = np.tile(out1, [len(trans_vec), 1, 1])
        out[:, 0:2, 2] = trans_vec[:, 0:2]
    else:
        out = np.eye(3)
        out[0:2, 2] = trans_vec[0:2]
    return out


def get_affine_rotation_2d(yaw, batch=False):
    if batch:
        out1 = np.eye(3)
        out = np.tile(out1, [len(yaw), 1, 1])
        c = np.cos(yaw)[:, 0]
        s = np.sin(yaw)[:, 0]
        out[:, 0, 0] = c
        out[:, 1, 1] = c
        out[:, 0, 1] = -s
        out[:, 1, 0] = s
    else:
        out = np.eye(3)
        c = np.cos(yaw)
        s = np.sin(yaw)
        out[0, 0] = c
        out[1, 1] = c
        out[0, 1] = -s
        out[1, 0] = s
    return out


def poses_2d_to_matrix(pose_2d, map_size, inverse=False):
    pos = np.asarray(pose_2d.position)
    yaw = np.asarray(pose_2d.orientation)

    t1 = get_affine_translation_2d(-pos, batch=True)

    yaw = -yaw
    t2 = get_affine_rotation_2d(-yaw, batch=True)

    t3 = get_affine_translation_2d(np.asarray([map_size / 2, map_size / 2]), batch=False)

    t21 = np.matmul(t2, t1)
    mat = np.matmul(t3, t21)

    # Swap x and y axes (because of the BxCxHxW a.k.a BxCxYxX convention)
    swapmat = mat[:, [1, 0, 2], :]
    mat = swapmat[:, :, [1, 0, 2]]

    if inverse:
        mat = np.linalg.inv(mat)

    return mat


def get_pytorch_to_image_matrix(image_size, inverse=False):
    """
    Returns an affine transformation matrix that takes an image in coordinate range [-1,1] and turns it
    into an image of coordinate range [W,H]
    """
    # First move the image so that the origin is in the top-left corner
    # (in pytorch, the origin is in the center of the image)
    """
    t1 = np.asarray([
        [1.0, 0, 1.0],
        [0, 1.0, 1.0],
        [0, 0, 1.0]
    ])

    # Then scale the image up to the required size
    scale_w = img_size[0] / 2
    scale_h = img_size[1] / 2
    t2 = np.asarray([
        [scale_h, 0, 0],
        [0, scale_w, 0],
        [0, 0, 1]
    ])
    """

    # First scale the image to pixel coordinates
    scale_w = image_size[0] / 2
    scale_h = image_size[1] / 2

    t1 = np.asarray([
        [scale_h, 0, 0],
        [0, scale_w, 0],
        [0, 0, 1]
    ])

    # Then move it such that the corner is at the origin
    t2 = np.asarray([
        [1.0, 0, scale_h],
        [0, 1.0, scale_w],
        [0, 0, 1.0]
    ])

    result = np.dot(t2, t1)

    if inverse:
        result = np.linalg.inv(result)

    result_tensor = np_to_tensor(result, cuda=False)

    return result_tensor


def image_affines_to_pytorch_cpu(image_affines, image_in_size, out_size):
    source_transform = get_pytorch_to_image_matrix(image_in_size, inverse=False)
    destination_transform = get_pytorch_to_image_matrix(out_size, inverse=True)

    # Convert pytorch-coord image to imgage pixel coords, apply the transformation, then convert the result back.
    batch_size = image_affines.size(0)
    source_transform = source_transform.repeat(batch_size, 1, 1)
    destination_transform = destination_transform.repeat(batch_size, 1, 1)

    # Convert pytorch coords to pixel coords and apply the transformation
    x = torch.bmm(image_affines, source_transform)

    # Convert the transformation back to pytorch coords
    pyt_affines = torch.bmm(destination_transform, x)

    inverses = [torch.inverse(affine) for affine in pyt_affines]

    pyt_affines_inv = torch.stack(inverses, dim=0)

    return pyt_affines_inv
