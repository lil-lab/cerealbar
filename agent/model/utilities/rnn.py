import torch
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence


def fast_run_rnn(seq_lens_tensor: torch.Tensor, rnn_input: torch.Tensor, rnn: torch.nn.RNN) -> torch.Tensor:
    max_length: int = rnn_input.size(1)

    # Sort the lengths and get the old indices
    sorted_lengths, permuted_indices = seq_lens_tensor.sort(0, descending=True)

    # Resort the input
    sorted_input: torch.Tensor = rnn_input[permuted_indices]

    # Pack the input
    packed_input = pack_padded_sequence(sorted_input, sorted_lengths.cpu().numpy(), batch_first=True)

    # Run the RNN
    rnn.flatten_parameters()
    packed_output: torch.Tensor = rnn(packed_input)[0]

    output: torch.Tensor = pad_packed_sequence(packed_output, batch_first=True, total_length=max_length)[0]

    _, unpermuted_indices = permuted_indices.sort(0)

    # Finally, sort back to original state
    hidden_states: torch.Tensor = output[unpermuted_indices]

    return hidden_states
