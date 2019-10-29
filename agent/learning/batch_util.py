"""Utilities for batching data."""
from __future__ import annotations

from typing import List, Tuple, TYPE_CHECKING
import torch
from agent.model.modules import word_embedder

if TYPE_CHECKING:
    from agent.data import instruction_example


def batch_instructions(examples: List[instruction_example.InstructionExample],
                       instruction_embedder: word_embedder.WordEmbedder) -> Tuple[torch.Tensor, torch.Tensor]:
    """Batches instructions for a list of examples given a word embedder with a set vocabulary."""

    instructions: List[List[str]] = [example.get_instruction() for example in examples]
    instruction_batch_indices: List[List[int]] = [[instruction_embedder.get_index(tok) for tok in seq]
                                                  for seq in instructions]
    instruction_lengths: List[int] = [len(instruction) for instruction in instructions]

    instruction_index_tensor: torch.Tensor = torch.zeros((len(instructions),
                                                          max(instruction_lengths)), dtype=torch.long)
    for idx, (sequence, sequence_length) in enumerate(zip(instruction_batch_indices, instruction_lengths)):
        instruction_index_tensor[idx, :sequence_length] = torch.tensor(sequence, dtype=torch.long)
    instruction_lengths_tensor: torch.Tensor = torch.tensor(instruction_lengths, dtype=torch.long)

    return instruction_index_tensor, instruction_lengths_tensor


def bhwc_to_bchw(tensor: torch.Tensor) -> torch.Tensor:
    return tensor.permute(0, 3, 1, 2)
