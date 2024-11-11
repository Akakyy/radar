from dataclasses import dataclass, field
from typing import List, Tuple, Literal


PolygonType = Literal[
    'signal_rejection',
    'wind',
    'sco_signal',
    'mfd',
    'bkp',
    'ppz',
    'pbl',
    'varu'
]


@dataclass
class Polygon:
    id: int
    vertices: List[Tuple[float, float]]
    type: PolygonType
    color: Tuple[float, float, float] = (0.7, 0.7, 0.7)  # Light grey default color

    def __post_init__(self):
        # Define colors for different types
        type_colors = {
            'signal_rejection': (1.0, 0.0, 0.0),    # Red
            'wind': (0.0, 0.0, 1.0),               # Blue
            'sco_signal': (0.0, 1.0, 0.0),         # Green
            'mfd': (1.0, 1.0, 0.0),                # Yellow
            'bkp': (1.0, 0.5, 0.0),                # Orange
            'ppz': (0.5, 0.0, 0.5),                # Purple
            'pbl': (0.0, 1.0, 1.0),                # Cyan
            'varu': (1.0, 0.0, 1.0)                # Magenta
        }
        self.color = type_colors.get(self.type, self.color)
    

class PolygonManager:
    def __init__(self):
        self.polygons: List[Polygon] = []
        self.next_number: int = 1
        self.polygon_types: List[PolygonType] = [
            'signal_rejection',
            'wind',
            'sco_signal',
            'mfd',
            'bkp',
            'ppz',
            'pbl',
            'varu'
        ]
    
    def remove_polygon(self, number: int) -> bool:
      for polygon in self.polygons:
          if polygon.id == number:
              self.polygons.remove(polygon)
              return True
      return False
        

    def add_polygon(self, polygon):
        # Randomly select a polygon type
        self.polygons.append(polygon)
        self.next_number += 1

        
    def get_polygons(self) -> List[Polygon]:
        return self.polygons
