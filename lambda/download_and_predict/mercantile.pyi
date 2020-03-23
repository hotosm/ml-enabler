from typing import Tuple, Any, Callable

class Tile():
    @property
    def x(self) -> int: ...
    @property
    def y(self) -> int: ...
    @property
    def z(self) -> int: ...

quadkey = Callable[[Any], str]
