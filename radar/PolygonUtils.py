from dataclasses import dataclass, field
from typing import List, Tuple, Literal, Dict, Any
import math
from OpenGL.GL import *  # Add this import at the top


PolygonType = Literal[
    'реджекция',
    'ветер',
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
            'реджекция': (1.0, 0.0, 0.0),    # Red
            'ветер': (0.0, 0.0, 1.0),               # Blue
            'sco_signal': (0.0, 1.0, 0.0),         # Green
            'mfd': (1.0, 1.0, 0.0),                # Yellow
            'bkp': (1.0, 0.5, 0.0),                # Orange
            'ppz': (0.5, 0.0, 0.5),                # Purple
            'pbl': (0.0, 1.0, 1.0),                # Cyan
            'varu': (1.0, 0.0, 1.0)                # Magenta
        }
        self.color = type_colors.get(self.type, self.color)


class Sector:
    def __init__(self, id: int, distance: float, angle: float, type: str, max_distance_km: float, distance_circles):
        """
        Initialize a sector with given parameters
        
        Args:
            id: Unique identifier for the sector
            distance: The distance (in km) based on radius
            angle: Central angle of the sector (in degrees)
            type: Type of the sector
            max_distance_km: The maximum distance in kilometers
        """
        self.id = id
        self.distance = distance  # Distance in kilometers
        self.angle = angle  # Central angle of the sector
        self.type = type
        self.width = 35  # Width of sector in degrees
        self.fill_color = (0.8, 0.8, 0.8, 0.3)  # RGBA
        self.border_color = (0.6, 0.6, 0.6, 0.8)  # Slightly darker border
        self.center_radius = 0.3  # Radius of the central red circle
        self.max_distance_km = max_distance_km
        
        # Define the distance circles scale
        self.distance_circles = distance_circles
        
    def get_scaled_distance(self):
        """
        Convert kilometers to scaled distance based on predefined distance circles.
        
        Returns:
            float: Scaled distance for drawing the sector
        """
        # Find the appropriate distance circle for the current distance
        for i, circle in enumerate(self.distance_circles):
            if self.distance <= circle['distance']:
                # If it's the first circle, use its radius directly
                if i == 0:
                    return circle['radius']
                
                # Interpolate between the previous and current circle
                prev_circle = self.distance_circles[i-1]
                
                # Calculate the proportion of distance between previous and current circles
                proportion = (self.distance - prev_circle['distance']) / \
                             (circle['distance'] - prev_circle['distance'])
                
                # Linear interpolation of radius
                scaled_radius = prev_circle['radius'] + \
                                proportion * (circle['radius'] - prev_circle['radius'])
                
                return scaled_radius
        
        # If distance is beyond the last circle, use the last circle's radius
        return self.distance_circles[-1]['radius']

    def draw(self):
        # Получаем корректированное расстояние в км
        distance = self.get_scaled_distance()

        # Устанавливаем начальный и конечный угол
        start_angle = 90  # Начинаем с вертикальной линии сверху
        end_angle = start_angle - self.angle  # Уменьшаем угол для поворота против часовой стрелки
        
        # Убедимся, что контекст правильно открыт
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Начало рисования
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(*self.fill_color)

        glVertex2f(0.0, 0.0)  # Центр

        # Рисуем дугу сектора
        num_segments = 32
        for i in range(num_segments + 1):
            # Вычисляем угол для текущего сегмента
            angle = math.radians(start_angle + (end_angle - start_angle) * i / num_segments)
            
            # Координаты точки сектора, ограниченные радиусом
            x = distance * math.cos(angle)
            y = distance * math.sin(angle)
            
            glVertex2f(x, y)

        # Завершаем рисование
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

    
    def create_sector(self, distance_km, angle, type, max_distance_km, distance_circles) -> Sector:
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
        sector = Sector(self.next_sector_number, distance_km, angle, type, max_distance_km, distance_circles)
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