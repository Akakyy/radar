from dataclasses import dataclass, field
from typing import List, Tuple, Literal
import math
from OpenGL.GL import *  # Add this import at the top


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


class Sector:
    def __init__(self, id: int, distance: float, angle: float, type: str):
        """
        Initialize a sector with given parameters
        
        Args:
            id: Unique identifier for the sector
            distance: Distance from center (in radar units)
            angle: Central angle of the sector (in degrees)
            type: Type of the sector (same as polygon types)
        """
        self.id = id
        self.distance = distance
        self.angle = angle
        self.type = type
        self.width = 35  # Width of sector in degrees
        # Light grey color with alpha
        self.fill_color = (0.8, 0.8, 0.8, 0.3)  # RGBA
        self.border_color = (0.6, 0.6, 0.6, 0.8)  # Slightly darker border
        
        
    def draw(self):
        """
        Draw the sector using OpenGL
        
        Args:
        
        """
        # Calculate the start and end angles for the sector
        start_angle = self.angle - self.width/2
        end_angle = self.angle + self.width/2
        
        # Draw filled sector
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Fill
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(*self.fill_color)
        
        # Center point
        glVertex2f(0.0, 0.0)
        
        # Draw arc segments
        num_segments = 32
        for i in range(num_segments + 1):
            angle = math.radians(start_angle + (end_angle - start_angle) * i / num_segments)
            x = self.distance * math.cos(angle)
            y = self.distance * math.sin(angle)
            glVertex2f(x, y)
            
        glEnd()
        
        # Draw border
        glBegin(GL_LINE_LOOP)
        glColor4f(*self.border_color)
        
        # Draw from center
        glVertex2f(0.0, 0.0)
        
        # Draw arc border
        for i in range(num_segments + 1):
            angle = math.radians(start_angle + (end_angle - start_angle) * i / num_segments)
            x = self.distance * math.cos(angle)
            y = self.distance * math.sin(angle)
            glVertex2f(x, y)
            
        glEnd()
        
        # Draw radial lines
        glBegin(GL_LINES)
        glColor4f(*self.border_color)
        
        # Start radial line
        start_x = self.distance * math.cos(math.radians(start_angle))
        start_y = self.distance * math.sin(math.radians(start_angle))
        glVertex2f(0.0, 0.0)
        glVertex2f(start_x, start_y)
        
        # End radial line
        end_x = self.distance * math.cos(math.radians(end_angle))
        end_y = self.distance * math.sin(math.radians(end_angle))
        glVertex2f(0.0, 0.0)
        glVertex2f(end_x, end_y)
        
        glEnd()
        
        
        
class PolygonManager:
    def __init__(self):
        self.polygons: List[Polygon] = []
        self.next_number: int = 1
        self.next_sector_number = 0
        self.sectors: List[Sector] = []
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

    
    def create_sector(self, distance: float, angle: float, type: str) -> Sector:
        """
        Create a new sector and add it to the manager
        
        Args:
            distance: Distance from center (in radar units)
            angle: Central angle of the sector (in degrees)
            type: Type of the sector
            
        Returns:
            Sector: The newly created sector
        """
        # Create new sector with unique ID
        sector = Sector(self.next_sector_number, distance, angle, type)
        self.sectors.append(sector)
        self.next_sector_number += 1
        return sector
        
    def remove_sector(self, sector_id: int) -> bool:
        """Remove a sector by its ID"""
        for sector in self.sectors:
            if sector.id == sector_id:
                self.sectors.remove(sector)
                return True
        return False
        
    def get_sectors(self) -> List[Sector]:
        """Get all sectors"""
        return self.sectors