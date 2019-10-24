# TODO: Clean this code.

import numpy as np
import torch
from torch.autograd import Variable


class Pose:
    def __init__(self, position, orientation):
        self._position = position
        self._orientation = orientation

    def __eq__(self, other):
        if other is None:
            return False

        poseq = self._position == other._position
        roteq = self._orientation == other._orientation
        # For numpy arrays, torch ByteTensors and variables containing ByteTensors
        if hasattr(poseq, "all"):
            poseq = poseq.all()
            roteq = roteq.all()
        return poseq and roteq

    def __getitem__(self, i):
        if type(i) in [torch.ByteTensor, torch.cuda.ByteTensor]:
            pos = self._position[i[:, np.newaxis].expand_as(self._position)].view([-1, 3])
            rot = self._orientation[i[:, np.newaxis].expand_as(self._orientation)].view([-1, 4])
            return Pose(pos, rot)
        else:
            return Pose(self._position[i], self._orientation[i])

    def cuda(self, device=None):
        self._position = self._position.cuda(device)
        self._orientation = self._orientation.cuda(device)
        return self

    def to_torch(self):
        _position = torch.from_numpy(self._position)
        _orientation = torch.from_numpy(self._orientation)
        return Pose(_position, _orientation)

    def to_var(self):
        _position = Variable(self._position)
        _orientation = Variable(self._orientation)
        return Pose(_position, _orientation)

    def repeat_np(self, batch_size):
        _position = np.tile(self._position[np.newaxis, :], [batch_size, 1])
        _orientation = np.tile(self._orientation[np.newaxis, :], [batch_size, 1])
        return Pose(_position, _orientation)

    def numpy(self):
        pos = self._position
        rot = self._orientation
        if isinstance(pos, Variable):
            pos = pos.data
            rot = rot.data
        if hasattr(pos, "cuda"):
            pos = pos.cpu().numpy()
            rot = rot.cpu().numpy()
        return Pose(pos, rot)

    def __len__(self):
        if self._position is None:
            return 0
        return len(self._position)

    def __str__(self):
        return "Pose " + str(self._position) + " : " + str(self._orientation)
