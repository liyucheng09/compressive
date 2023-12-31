from transformers import AutoTokenizer, GPT2LMHeadModel, AutoModelForCausalLM
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

model = AutoModelForCausalLM.from_pretrained("/mnt/fast/nobackup/scratch4weeks/yl02706/models/Llama-2-7B", device_map='auto', trust_remote_code=True)
tokenizer = AutoTokenizer.from_pretrained("/mnt/fast/nobackup/scratch4weeks/yl02706/models/Llama-2-7B", use_fast=False, trust_remote_code=True)

text = ' '.join(['pytorch'] * 300)

inputs = tokenizer(text, return_tensors="pt", truncation=True).to(model.device)
outputs = model(**inputs)

probs = outputs.logits.softmax(dim=-1)
print(probs.shape)

cdf = pmf_to_cdf(probs)
print(cdf.shape)

cdf = cdf.detach().cpu()

sym_32 = inputs['input_ids'].to(torch.int32).detach().cpu()
sym_16 = inputs['input_ids'].to(torch.int16).detach().cpu()

byte_stream_32 = torchac.encode_float_cdf(cdf, sym_32, precision=32)
print(len(byte_stream_32))

byte_stream_16 = torchac.encode_float_cdf(cdf, sym_16, precision=16)
print(len(byte_stream_16))

d = torchac.decode_float_cdf(cdf, byte_stream_32, sym_32, precision=32)
# print(len(byte_stream_32))
print('=========================')

assert sym_32.equal(d)

# print(torchac.decode_float_cdf(cdf, byte_stream).shape)
# print(inputs['input_ids'].shape)