from pydantic import BaseModel, Field
from typing import List, Optional, Any


# LLM main output structure
class llm_output(BaseModel):

    text: Optional[str] = Field(
        default=None,
        description="Plain text output from LLM"
    )

    obj: Optional[Any] = Field(
        default=None,
        description="Structured output object from LLM"
    )

    logprob: Optional[float] = Field(
        default=None,
        description="Sequence perplexity/logprob estimation"
    )
    
    
# extract rubric items
class RubricOutputItem(BaseModel):
    points: float = Field(description="Points of the one rubric item.")
    content: str = Field(description="Content of the one rubric item.")


class RubricOutput(BaseModel):
    rubrics: List[RubricOutputItem]
    

# feedback post-process part
class FeedbackPostProcessOutput(BaseModel):
    text: str
    flag: int
    

# segmentation part
class VerticalSplitOutput(BaseModel):
    splits: List[List[int]] = Field(
        description="Vertical page split ranges in percentages"
    )
    

# image post-process part
class ImagePostProcessOutput(BaseModel):
    text: str
    flag: int
    
    
# grading part
class JudgeOutput(BaseModel):
    score: float
    reasoning: str


class FullScoreOutput(BaseModel):
    score: float