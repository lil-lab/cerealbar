import numpy as np
from torch import nn as nn

from agent.model.map_transformations import affine_2d
from agent.model.map_transformations import pose
from agent.model.map_transformations import util

PROFILE = False
CONCURRENT = False


class MapAffine(nn.Module):
    def __init__(self, source_map_size, dest_map_size, world_size_px, world_size_m):
        super(MapAffine, self).__init__()
        self._is_cuda = False
        self._cuda_device = None
        self._source_map_size_px = source_map_size
        self._dest_map_size_px = dest_map_size
        self._world_in_map_size_px = world_size_px
        self._world_size_m = world_size_m

        self._affine_2d = affine_2d.Affine2D()

        pos = np.asarray([self._source_map_size_px / 2, self._source_map_size_px / 2])
        rot = np.asarray([0])
        self._canonical_pose_src = pose.Pose(pos, rot)

        pos = np.asarray([self._dest_map_size_px / 2, self._dest_map_size_px / 2])
        rot = np.asarray([0])
        self._canonical_pose_dst = pose.Pose(pos, rot)

    def cuda(self, device=None):
        nn.Module.cuda(self, device)
        self._is_cuda = True
        self._cuda_device = device
        self._affine_2d.cuda(device)
        return self

    def get_affine_matrices(self, map_poses, cam_poses, batch_size):
        if map_poses is not None:
            map_poses = map_poses.numpy()
            map_poses_img = util.poses_m_to_px(map_poses,
                                               self._source_map_size_px,
                                               [self._world_in_map_size_px, self._world_in_map_size_px],
                                               self._world_size_m,
                                               batch_dim=True)
        else:
            map_poses_img = self._canonical_pose_src.repeat_np(batch_size)

        if cam_poses is not None:
            cam_poses = cam_poses.numpy()
            cam_poses_img = util.poses_m_to_px(cam_poses,
                                               self._dest_map_size_px,
                                               [self._world_in_map_size_px, self._world_in_map_size_px],
                                               self._world_size_m,
                                               batch_dim=True)
        else:
            cam_poses_img = self._canonical_pose_dst.repeat_np(batch_size)

        # Get the affine transformation matrix to transform the map to the new camera pose
        affines = self.get_old_to_new_pose_matrices(map_poses_img, cam_poses_img)

        return affines

    def get_old_to_new_pose_matrices(self, old_pose, new_pose):
        old_t_inv = util.poses_2d_to_matrix(old_pose, self._source_map_size_px, inverse=True)
        new_t = util.poses_2d_to_matrix(new_pose, self._dest_map_size_px, inverse=False)
        matrix = np.matmul(new_t, old_t_inv)
        mat_t = util.np_to_tensor(matrix, insert_batch_dim=False, cuda=False)
        return mat_t

    def forward(self, maps, current_poses, new_poses):
        batch_size = maps.size(0)
        affine_matrices_cpu = self.get_affine_matrices(current_poses, new_poses, batch_size)

        # Apply the affine transformation on the map
        # The affine matrices should be on CPU (if not, they'll be copied to CPU anyway!)
        maps_out = self._affine_2d(maps, affine_matrices_cpu, out_size=[self._dest_map_size_px, self._dest_map_size_px])

        return maps_out
