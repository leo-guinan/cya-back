import functools
from typing import Callable, Any
from decouple import config
from openai import OpenAI
import ell
from pydantic import BaseModel, Field

from prelo.events import record_prelo_event

MAX_ATTEMPTS = 3

class ValidatedOutput(BaseModel):
    valid: bool = Field(description="Whether the output is valid")
    reason: str = Field(description="The reason the output is valid or not")

@ell.complex(model='gpt-4o-mini', client=OpenAI(api_key=config('OPENAI_API_KEY')), response_format=ValidatedOutput)
def validate_output(input_data: str, output: str, validation_prompt: str, previous_attempts: list) -> ValidatedOutput:
    """
    You are a quality assurance expert for AI-generated content. Your task is to evaluate whether the given output
    meets the quality requirements specified in the validation prompt. Consider the input data and any previous
    attempts when making your decision.

    Return True if the output meets the requirements, and False if it does not.
    """
    return f"""
    Input data: {input_data}
    Output: {output}
    Validation prompt: {validation_prompt}
    Previous attempts: {previous_attempts}

    Does this output meet the quality requirements? Respond with True or False.
    """

def validator(validation_func: Callable[[str, str], str]):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            previous_attempts = []
            while attempts < MAX_ATTEMPTS:
                result = func(*args, **kwargs)
                validation_prompt = validation_func(*args, **kwargs)
                validated_output = validate_output(str(args), result, validation_prompt, previous_attempts)
                if validated_output.parsed.valid:
                    record_prelo_event(
                        {
                            "event": "prelovc_output_validation",
                            "message": "success",
                            "output": result,
                            "reason": validated_output.parsed.reason,
                            "attempts": attempts,
                            "function": func.__name__,
                        }
                    )
                    return result
                record_prelo_event(
                    {
                        "event": "prelovc_output_validation",
                        "message": "error",
                        "output": result,
                        "reason": validated_output.parsed.reason,
                        "attempts": attempts,
                        "function": func.__name__,
                    }
                )
                previous_attempts.append(result)
                attempts += 1

            record_prelo_event(
                {
                    "event": "prelovc_output_validation",
                    "message": "failed",
                    "function": func.__name__,
                    "attempts": attempts,
                }
            )
            return "There was an error generating the output. Please try again."
        return wrapper
    return decorator
