from dataclasses import dataclass, field
from typing import List, Tuple, Literal
import random
import math


@dataclass
class NoisePoint:
    x: float
    y: float
    intensity: float
    speed: float
    phase: float
    radius: float
    
    
class RadarNoise:
    def __init__(self, polygon_vertices: List[Tuple[float, float]]):
        self.vertices = polygon_vertices
        self.noise_points = []
        self.time_offset = random.uniform(0, 1000)  # Random starting time
        self.generate_noise_points()
        
    def generate_noise_points(self):
        # Find bounding box of the polygon
        min_x = min(v[0] for v in self.vertices)
        max_x = max(v[0] for v in self.vertices)
        min_y = min(v[1] for v in self.vertices)
        max_y = max(v[1] for v in self.vertices)
        
        # Calculate polygon center
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # Create dense noise points
        num_points = 50  # Increased number of points for denser effect
        for _ in range(num_points):
            # Create points with varying distances from center
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, 0.8)  # Varied distance from center
            
            x = center_x + math.cos(angle) * distance
            y = center_y + math.sin(angle) * distance
            
            # Create noise point with varying characteristics
            point = NoisePoint(
                x=x,
                y=y,
                intensity=random.uniform(0.1, 0.3),
                speed=random.uniform(1, 3),
                phase=random.uniform(0, 2 * math.pi),
                radius=random.uniform(0.02, 0.08)  # Smaller radii for more subtle effect
            )
            self.noise_points.append(point)

    def point_in_polygon(self, x: float, y: float) -> bool:
        n = len(self.vertices)
        inside = False
        j = n - 1
        for i in range(n):
            if (((self.vertices[i][1] > y) != (self.vertices[j][1] > y)) and
                (x < (self.vertices[j][0] - self.vertices[i][0]) * 
                 (y - self.vertices[i][1]) / (self.vertices[j][1] - self.vertices[i][1]) + 
                 self.vertices[i][0])):
                inside = not inside
            j = i
        return inside
        