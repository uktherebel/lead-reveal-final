from src.workers.question_workers import (
    CognitiveLoad1Worker, CognitiveLoad2Worker, CognitiveLoad3Worker,
    CognitiveLoad4Worker, CognitiveLoad5Worker,
)

WORKERS: dict[int, object] = {
    1: CognitiveLoad1Worker(),
    2: CognitiveLoad2Worker(),
    3: CognitiveLoad3Worker(),
    4: CognitiveLoad4Worker(),
    5: CognitiveLoad5Worker(),
}