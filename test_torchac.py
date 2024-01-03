from transformers import AutoTokenizer, GPT2LMHeadModel
import torch
import ac as torchac

def pmf_to_cdf(pmf):
  cdf = pmf.cumsum(dim=-1)
  spatial_dimensions = pmf.shape[:-1] + (1,)
  zeros = torch.zeros(spatial_dimensions, dtype=pmf.dtype, device=pmf.device)
  cdf_with_0 = torch.cat([zeros, cdf], dim=-1)
  # On GPU, softmax followed by cumsum can lead to the final value being 
  # slightly bigger than 1, so we clamp.
  cdf_with_0 = cdf_with_0.clamp(max=1.)
  return cdf_with_0

model = GPT2LMHeadModel.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

text = ' '.join(['binsearch'] * 200)

# batch = [text, text]

inputs = tokenizer(text, return_tensors="pt", truncation=True)
outputs = model(**inputs)

probs = outputs.logits.softmax(dim=-1)
print(probs.shape)

cdf = pmf_to_cdf(probs)
print(cdf.shape)

sym = inputs['input_ids'].to(torch.int32)

byte_stream = torchac.encode_float_cdf(cdf, sym)
print(len(byte_stream))

torchac.decode_float_cdf(cdf, byte_stream, sym)

# print(torchac.decode_float_cdf(cdf, byte_stream).shape)
# print(inputs['input_ids'].shape)