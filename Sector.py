from typing import Optional, List, Tuple
import math
import pygame
from pygame.locals import *
from OpenGL.GL import *
from PolygonUtils import Polygon


class SectorInput:
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = pygame.font.SysFont('Arial', 20)
        
        # Input fields
        self.fields = {
            'distance': {'value': '', 'active': False, 'rect': pygame.Rect(10, screen_height - 90, 100, 30)},
            'azimuth': {'value': '', 'active': False, 'rect': pygame.Rect(120, screen_height - 90, 100, 30)},
            'type': {'value': 'signal_rejection', 'active': False, 'rect': pygame.Rect(230, screen_height - 90, 150, 30)}
        }
        
        # Create button
        self.create_button = pygame.Rect(390, screen_height - 90, 100, 30)
        
        # Dropdown for polygon types
        self.type_dropdown = False
        self.polygon_types = [
            'signal_rejection', 'wind', 'sco_signal', 'mfd',
            'bkp', 'ppz', 'pbl', 'varu'
        ]
        self.dropdown_rects = []
        for i, _ in enumerate(self.polygon_types):
            self.dropdown_rects.append(
                pygame.Rect(230, screen_height - 90 + 30 * (i + 1), 150, 30)
            )
            
    def handle_event(self, event) -> Optional[dict]:
        if event.type == MOUSEBUTTONDOWN:
            # Check input fields
            mouse_pos = pygame.mouse.get_pos()
            for field_name, field in self.fields.items():
                if field['rect'].collidepoint(mouse_pos):
                    self.activate_field(field_name)
                    return None
                    
            # Check type dropdown
            if self.fields['type']['active']:
                for i, rect in enumerate(self.dropdown_rects):
                    if rect.collidepoint(mouse_pos):
                        self.fields['type']['value'] = self.polygon_types[i]
                        self.fields['type']['active'] = False
                        return None
                        
            # Check create button
            if self.create_button.collidepoint(mouse_pos):
                try:
                    distance = float(self.fields['distance']['value'])
                    azimuth = float(self.fields['azimuth']['value'])
                    poly_type = self.fields['type']['value']
                    
                    # Return sector data
                    return {
                        'distance': distance,
                        'azimuth': azimuth,
                        'type': poly_type
                    }
                except ValueError:
                    print("Invalid input values")
                return None
                
            # Deactivate all fields if clicked elsewhere
            self.deactivate_all_fields()
            
        elif event.type == KEYDOWN:
            # Handle text input
            for field in self.fields.values():
                if field['active']:
                    if event.key == K_BACKSPACE:
                        field['value'] = field['value'][:-1]
                    elif event.key == K_RETURN:
                        field['active'] = False
                    else:
                        if event.unicode.isnumeric() or event.unicode == '.':
                            field['value'] += event.unicode
                            
        return None
        
    def activate_field(self, field_name: str):
        for name, field in self.fields.items():
            field['active'] = (name == field_name)
            
    def deactivate_all_fields(self):
        for field in self.fields.values():
            field['active'] = False
            
    def draw(self, surface):
        # Draw input fields
        for field_name, field in self.fields.items():
            color = (200, 200, 200) if field['active'] else (150, 150, 150)
            pygame.draw.rect(surface, color, field['rect'])
            
            # Draw field label
            label = self.font.render(field_name, True, (0, 0, 0))
            surface.blit(label, (field['rect'].x, field['rect'].y - 20))
            
            # Draw field value
            text = self.font.render(str(field['value']), True, (0, 0, 0))
            surface.blit(text, (field['rect'].x + 5, field['rect'].y + 5))
            
        # Draw create button
        pygame.draw.rect(surface, (100, 200, 100), self.create_button)
        button_text = self.font.render('Create', True, (0, 0, 0))
        surface.blit(button_text, (self.create_button.x + 20, self.create_button.y + 5))
        
        # Draw type dropdown if active
        if self.fields['type']['active']:
            for i, rect in enumerate(self.dropdown_rects):
                pygame.draw.rect(surface, (180, 180, 180), rect)
                type_text = self.font.render(self.polygon_types[i], True, (0, 0, 0))
                surface.blit(type_text, (rect.x + 5, rect.y + 5))

def create_sector_polygon(distance: float, azimuth: float, sector_width: float = 30.0) -> List[Tuple[float, float]]:
    """Create vertices for a sector polygon"""
    # Convert to radians
    azimuth_rad = math.radians(azimuth)
    half_width_rad = math.radians(sector_width / 2)
    
    # Calculate vertices
    vertices = [(0, 0)]  # Center point
    
    # Convert distance to radar units (assuming max radar distance is 30km)
    radar_distance = (distance / 30.0) * 1.9  # 1.9 is the border radius
    
    # Add arc points
    arc_points = 10
    start_angle = azimuth_rad - half_width_rad
    end_angle = azimuth_rad + half_width_rad
    
    for i in range(arc_points + 1):
        angle = start_angle + (end_angle - start_angle) * i / arc_points
        x = radar_distance * math.cos(angle)
        y = radar_distance * math.sin(angle)
        vertices.append((x, y))
        
    return vertices

def modify_polygon_with_sector(polygon: Polygon, sector_vertices: List[Tuple[float, float]]) -> Optional[Polygon]:
    """Modify existing polygon by removing sector area"""
    # Implementation of polygon clipping algorithm would go here
    # This is a complex geometric operation that requires a proper polygon clipping library
    # For now, we'll just return a modified version of the polygon
    # You might want to use libraries like Shapely for proper polygon operations
    
    # Placeholder implementation - returns None if modification fails
    try:
        # Here you would implement actual polygon clipping
        # For now, we'll just return the original polygon
        return polygon
    except Exception as e:
        print(f"Error modifying polygon: {e}")
        return None