from pydantic import BaseModel


class CreateStreamRequest(BaseModel):
    name: str
    description: str
    dataset: str
    top_k: int
    metrics: list[str]
    timestamp_split_start: str
    window_size: int


class CreateStreamResponse(BaseModel):
    stream_job_id: int
    status: str


class AlgorithmWithParams(BaseModel):
    id: int | None = None
    name: str
    params: dict = {}


class AddAlgorithmsRequest(BaseModel):
    algorithms: list[AlgorithmWithParams]


class AddAlgorithmsResponse(BaseModel):
    message: str
    stream_job_id: int
    status: str
