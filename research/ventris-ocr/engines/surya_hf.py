"""Run Surya 2.5 (surya-ocr 0.23.0) on this PC without docker/vllm/llama-server.

Surya's own predictors talk to a Backend that returns raw model text. The stock backends need vllm (docker) or the
llama.cpp `llama-server` binary; neither is installed here. This Backend loads the same checkpoint
(datalab-to/surya-ocr-2.5, a Qwen3.5-based 0.69B vision-language model) with transformers, uses Surya's own prompts,
image scaling, parsers and RecognitionPredictor, and returns the raw text with special tokens kept (as llama-server
--special does). Greedy decoding (temperature 0), bfloat16, on the GPU.
"""
from __future__ import annotations

import time
from typing import List

import torch
from transformers import AutoModelForImageTextToText, AutoProcessor

from surya.inference import SuryaInferenceManager
from surya.inference.backends.base import Backend, ServerHandle
from surya.inference.prompts import PROMPT_MAPPING
from surya.inference.schema import BatchInputItem, BatchOutputItem
from surya.inference.util import scale_to_fit
from surya.settings import settings

_END = ("<|im_end!>", "<|im_end|>", "<|endoftext|>")


def decode_ids(tok, ids):
    """Decode token ids, keeping single-character Latin-1 tokens (the quarter and half fractions, section sign, degree
    sign) as the characters they are. The tokenizer's ByteLevel decoder turns such a lone token into U+FFFD, although
    the model emitted the right token; every other run of tokens is decoded by the tokenizer as usual."""
    lit = {}
    for t in set(ids):
        s = tok.convert_ids_to_tokens(t)
        if isinstance(s, str) and len(s) == 1 and 0xA1 <= ord(s) <= 0xFF and "�" in tok.decode([t]):
            lit[t] = s
    out, run = [], []
    for t in ids:
        if t in lit:
            if run:
                out.append(tok.decode(run, skip_special_tokens=False))
                run = []
            out.append(lit[t])
        else:
            run.append(t)
    if run:
        out.append(tok.decode(run, skip_special_tokens=False))
    return "".join(out)


class HFBackend(Backend):
    name = "transformers"

    def __init__(self, device="cuda"):
        self.device = device
        self.processor = None
        self.model = None
        self.handle = ServerHandle(base_url="local", model_name=settings.SURYA_MODEL_CHECKPOINT, spawned_by_us=False)

    def start(self):
        if self.model is None:
            self.processor = AutoProcessor.from_pretrained(settings.SURYA_MODEL_CHECKPOINT)
            self.model = AutoModelForImageTextToText.from_pretrained(
                settings.SURYA_MODEL_CHECKPOINT, dtype=torch.bfloat16).to(self.device).eval()
        return self.handle

    def stop(self):
        pass

    def capacity(self):
        return 1

    @torch.inference_mode()
    def generate(self, batch: List[BatchInputItem]) -> List[BatchOutputItem]:
        self.start()
        outs = []
        for item in batch:
            prompt = item.prompt or PROMPT_MAPPING[item.prompt_type]
            image = scale_to_fit(item.image)
            msgs = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}]}]
            inputs = self.processor.apply_chat_template(msgs, add_generation_prompt=True, tokenize=True,
                                                        return_dict=True, return_tensors="pt").to(self.device)
            max_new = item.max_tokens or settings.SURYA_MAX_TOKENS_FULL_PAGE
            gen = self.model.generate(**inputs, max_new_tokens=max_new, do_sample=False)
            new = gen[0, inputs["input_ids"].shape[1]:]
            text = decode_ids(self.processor.tokenizer, new.tolist()).rstrip()
            for m in _END:
                if text.endswith(m):
                    text = text[: -len(m)].rstrip()
            finish = "length" if new.shape[0] >= max_new else "stop"
            outs.append(BatchOutputItem(raw=text, token_count=int(new.shape[0]), error=False, finish_reason=finish,
                                        metadata=item.metadata))
        return outs


def make_manager():
    mgr = SuryaInferenceManager.__new__(SuryaInferenceManager)
    mgr.method = "transformers"
    mgr.backend = HFBackend()
    return mgr
