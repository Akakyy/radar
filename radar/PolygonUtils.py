from dataclasses import dataclass, field
from typing import List, Tuple, Literal
import math


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
   

@dataclass
class Sector(Polygon):
    distance: float = 0.0
    azimuth: float = 0.0

    def __post_init__(self):
        super().__post_init__()
        self.create_sector()

    def create_sector(self):
        radius = self.distance
        vertices = []

        start_angle = math.radians(self.azimuth - 30)
        end_angle = math.radians(self.azimuth + 30)
        for i in range(11):
            angle = start_angle + i * (end_angle - start_angle) / 10
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertices.append((x, y))

        self.vertices = vertices
        self.color = self.color  # Assign the same color as the corresponding Polygon
        
        
class PolygonManager:
    def __init__(self):
        self.polygons: List[Polygon] = []
        self.sectors: List[Sector] = []
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

    
    def create_sector(self, distance: float, azimuth: float, polygon_type: PolygonType) -> Sector:
        """Create a sector polygon based on the given distance, azimuth, and polygon type."""
        sector = Sector(id=self.next_number, vertices=[], type=polygon_type)
        sector.distance = distance
        sector.azimuth = azimuth
        self.sectors.append(sector)
        self.next_number += 1
        return sector
        
    
    def remove_polygon(self, number: int) -> bool:
        for polygon in self.polygons:
            if polygon.id == number:
                self.polygons.remove(polygon)
                return True
        for sector in self.sectors:
            if sector.id == number:
                self.sectors.remove(sector)
                return True
        return False
        
    def get_sectors(self) -> List[Sector]:
        return self.sectors
        
        
    def add_polygon(self, polygon):
        # Randomly select a polygon type
        self.polygons.append(polygon)
        self.next_number += 1

        
    def get_polygons(self) -> List[Polygon]:
        return self.polygons
