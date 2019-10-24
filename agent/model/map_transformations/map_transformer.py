"""Module that rotates and transforms a map to a particular configuration.

From Blukis et al. 2018.
"""
from agent.model.map_transformations import map_affine
from agent.model.map_transformations import cuda_module


class MapTransformer(cuda_module.CudaModule):

    def __init__(self, source_map_size, world_size_px, world_size_m, dest_map_size=None):
        super(MapTransformer, self).__init__()

        if dest_map_size is None:
            dest_map_size = source_map_size

        self._map_affine = map_affine.MapAffine(
            source_map_size=source_map_size,
            dest_map_size=dest_map_size,
            world_size_px=world_size_px,
            world_size_m=world_size_m)

    def init_weights(self):
        pass

    def cuda(self, device=None):
        cuda_module.CudaModule.cuda(self, device)
        self._map_affine.cuda(device)
        return self

    def forward(self, maps, map_poses, new_map_poses):
        maps = self._map_affine(maps, map_poses, new_map_poses)
        return maps, new_map_poses
