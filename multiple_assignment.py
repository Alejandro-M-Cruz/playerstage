from dataclasses import dataclass


@dataclass
class Log:
    time: float
    host: int
    robot: int
    interface: str
    index: int
    type: int
    subtype: int
    payload: list[str]


string = "0000000000.000 16777343 6665 laser 00 004 001  +0.030  +0.000   0.000   0.140   0.140"

header, *payload = string.split("  ")

print(header.split(" "))
print(payload)

log = Log(*header.split(" "), payload=payload)
print(log)


