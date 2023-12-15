from typing import TypedDict

import pandas as pd


class LogMetadata(TypedDict):
    index: str
    path: str
    algorithm: str
    difficulty: str


class LogData(TypedDict):
    metadata: LogMetadata
    laser_data: pd.DataFrame
    position_data: pd.DataFrame
    obstacle_data: pd.DataFrame
