import re

import yaml
from langchain_openai import ChatOpenAI
from api.utils.tracing import get_langfuse_handler


def preprocess_yaml(input_text):
    """Extract the YAML block from the input text."""
    # Extract the YAML block
    yaml_block_start_index = input_text.find("```yaml")
    if yaml_block_start_index == -1:
        raise ValueError("No YAML block found")
    yaml_block_start_index = yaml_block_start_index + len("```yaml")

    # find the last ``` in the text
    yaml_block_end_index = input_text.rfind("```")

    if yaml_block_end_index != -1:
        yaml_text = input_text[yaml_block_start_index:yaml_block_end_index]
    else:
        raise ValueError("No valid YAML block found")

    return yaml_text


def postprocess_yaml(yaml_text):
    """Fix issues with the YAML text before parsing."""
    # Fix issues with improper quotes and mappings
    yaml_text = re.sub(
        r':\s*["\'](.+?)["\']', r": \1", yaml_text
    )  # Remove quotes around values
    return re.sub(
        r'(["\'])([a-zA-Z0-9_]+)\1:', r"\2:", yaml_text
    )  # Remove quotes around keys


REFORMAT_YAML_PROMPT = """
This is a YAML block:
```yaml
{yaml_text}
```

This YAML block is not valid. It outputs the following error when trying to parse it:
```
{error}
```

Rewrite the YAML block to fix the error. ONLY provide one YAML block in the response.
"""


def parse_yaml_response_content(
    content, attempt_num=0, max_attempts=3, remove_quotes=False, config=None
):
    """
    Parse the YAML block from the input text. If the YAML block is not valid,
    reformat it using a language model.
    """
    yaml_text = preprocess_yaml(content)
    if remove_quotes:
        yaml_text = postprocess_yaml(yaml_text)

    try:
        output = yaml.safe_load(yaml_text)
        if output is None:
            msg = f"YAML block is empty. Content:\n{content}"
            raise ValueError(msg)
        return output
    except yaml.YAMLError as e:
        if attempt_num >= max_attempts:
            msg = f"Error parsing YAML: {e}"
            raise ValueError(msg)

        print(f"Error parsing YAML: {e}")
        # Use a language model to reformat the YAML block
        model = ChatOpenAI(
            temperature=0.0, model_name="gpt-4o-mini", max_tokens=16384
        )
        prompt = REFORMAT_YAML_PROMPT.format(yaml_text=yaml_text, error=e)
        print(f"Reformatting YAML block using a language model: {prompt}")
        response = model.invoke(
            REFORMAT_YAML_PROMPT.format(
                yaml_text=yaml_text,
                error=e,
            ),
            config=config,
        )
        print(f"Response: {response.content}")
        return parse_yaml_response_content(response.content, attempt_num + 1)
