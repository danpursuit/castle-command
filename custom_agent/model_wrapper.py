from PIL import Image
import json
import random
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from unsloth import FastLanguageModel
from smolagents import Model, ChatMessage, Tool
from smolagents.models import get_tool_json_schema, remove_stop_sequences, ChatMessageToolCall, ChatMessageToolCallDefinition

from transformers import StoppingCriteriaList, StoppingCriteria

# make sure version is correct
# smolagents.__version__  # '1.9.2'

# below is a reimplementation of smolagent TransformerModel, which is a wrapper around a model made with HuggingFace.from_pretrained(model)
# our implementation is a bare bones version that wraps the Unsloth FastLanguageModel

class ModelWrapper(Model):
    def __init__(
        self,
        model_id,
        max_seq_length=4096,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.model_id = model_id
        self.max_seq_length = max_seq_length

        # vlm disabled (visual model)
        self._is_vlm = False

        # our custom logic to use faster Unsloth model
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_id,
            max_seq_length=max_seq_length,
            dtype=None,
            load_in_4bit=True
        )
        FastLanguageModel.for_inference(model)
        # model.load_adapter(lora_path)  # for resuming/loading a trained model

        self.kwargs = kwargs
        self.model = model
        self.tokenizer = tokenizer

    def make_stopping_criteria(self, stop_sequences: List[str], tokenizer) -> StoppingCriteriaList:
        # unsloth code below
        class StopOnStrings(StoppingCriteria):
            def __init__(self, stop_strings: List[str], tokenizer):
                self.stop_strings = stop_strings
                self.tokenizer = tokenizer
                self.stream = ""

            def reset(self):
                self.stream = ""

            def __call__(self, input_ids, scores, **kwargs):
                generated = self.tokenizer.decode(input_ids[0][-1], skip_special_tokens=True)
                self.stream += generated
                if any([self.stream.endswith(stop_string) for stop_string in self.stop_strings]):
                    return True
                return False

        return StoppingCriteriaList([StopOnStrings(stop_sequences, tokenizer)])

    def __call__(
        self,
        messages: List[Dict[str, str]],
        stop_sequences: Optional[List[str]] = None,
        grammar: Optional[str] = None,
        tools_to_call_from: Optional[List[Tool]] = None,
        images: Optional[List[Image.Image]] = None,
        **kwargs,
    ) -> ChatMessage:
        # below is the smolagent code in case we ever want to enable vlm, tools, or more kwargs
        # however, most of this is not necessary for current unsloth models
        completion_kwargs = self._prepare_completion_kwargs(
            messages=messages,
            stop_sequences=stop_sequences,
            grammar=grammar,
            flatten_messages_as_text=(not self._is_vlm),
            **kwargs,
        )

        messages = completion_kwargs.pop("messages")
        stop_sequences = completion_kwargs.pop("stop", None)
        
        completion_kwargs['max_seq_length'] = self.max_seq_length

        if hasattr(self, "processor"):
            images = [Image.open(image) for image in images] if images else None
            prompt_tensor = self.processor.apply_chat_template(
                messages,
                tools=[get_tool_json_schema(tool) for tool in tools_to_call_from] if tools_to_call_from else None,
                return_tensors="pt",
                tokenize=True,
                return_dict=True,
                images=images,
                add_generation_prompt=True if tools_to_call_from else False,
            )
        else:
            prompt_tensor = self.tokenizer.apply_chat_template(
                messages,
                tools=[get_tool_json_schema(tool) for tool in tools_to_call_from] if tools_to_call_from else None,
                return_tensors="pt",
                return_dict=True,
                add_generation_prompt=True if tools_to_call_from else False,
            )

        prompt_tensor = prompt_tensor.to(self.model.device)
        count_prompt_tokens = prompt_tensor["input_ids"].shape[1]

        if stop_sequences:
            stopping_criteria = self.make_stopping_criteria(
                stop_sequences, tokenizer=self.processor if hasattr(self, "processor") else self.tokenizer
            )
        else:
            stopping_criteria = None
        
        out = self.model.generate(
            **prompt_tensor,
            stopping_criteria=stopping_criteria,
            # **completion_kwargs, # smolagent extra kwargs not needed by unsloth
        )
        generated_tokens = out[0, count_prompt_tokens:]
        if hasattr(self, "processor"):
            output = self.processor.decode(generated_tokens, skip_special_tokens=True)
        else:
            output = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        self.last_input_token_count = count_prompt_tokens
        self.last_output_token_count = len(generated_tokens)

        if stop_sequences is not None:
            output = remove_stop_sequences(output, stop_sequences)

        if tools_to_call_from is None:
            return ChatMessage(
                role="assistant",
                content=output,
                raw={"out": out, "completion_kwargs": completion_kwargs},
            )
        else:
            # we use code paradigm, not tool calling paradigm. below is not used
            if "Action:" in output:
                output = output.split("Action:", 1)[1].strip()
            try:
                start_index = output.index("{")
                end_index = output.rindex("}")
                output = output[start_index : end_index + 1]
            except Exception as e:
                raise Exception("No json blob found in output!") from e

            try:
                parsed_output = json.loads(output)
            except json.JSONDecodeError as e:
                raise ValueError(f"Tool call '{output}' has an invalid JSON structure: {e}")
            tool_name = parsed_output.get("name")
            tool_arguments = parsed_output.get("arguments")
            return ChatMessage(
                role="assistant",
                content="",
                tool_calls=[
                    ChatMessageToolCall(
                        id="".join(random.choices("0123456789", k=5)),
                        type="function",
                        function=ChatMessageToolCallDefinition(name=tool_name, arguments=tool_arguments),
                    )
                ],
                raw={"out": out, "completion_kwargs": completion_kwargs},
            )