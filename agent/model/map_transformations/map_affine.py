import numpy as np
from torch import nn as nn

from agent.model.map_transformations import pose
from agent.model.map_transformations import affine_2d

from concurrent.futures import ProcessPoolExecutor

PROFILE = False
CONCURRENT = False


class MapAffine(nn.Module):
    # TODO: Cleanup unused run_params
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

        self._executor = ProcessPoolExecutor(max_workers=10)

    def cuda(self, device=None):
        nn.Module.cuda(self, device)
        self._is_cuda = True
        self._cuda_device = device
        self._affine_2d.cuda()
        return self

    def forward(self):
        # TODO: Take the old implementation
        pass
