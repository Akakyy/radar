import pygame
from pygame.locals import *
from OpenGL.GL import *
import math
import random
import time
from dataclasses import dataclass, field
from typing import List, Tuple,Literal


@dataclass
class NoisePoint:
    x: float
    y: float
    intensity: float
    speed: float
    phase: float
    radius: float

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
        #polygon_type = random.choice(self.polygon_types)
        #polygon = Polygon(self.next_number, vertices, polygon_type)
        self.polygons.append(polygon)
        self.next_number += 1

        
    def get_polygons(self) -> List[Polygon]:
        return self.polygons

@dataclass
class MovingObject:
    pos: List[float]
    velocity: List[float]
    creation_time: float
    target_id: int
    control_point: List[float]
    start_pos: List[float]
    trajectory_type: Literal['parabolic', 'straight', 'sinusoidal']
    speed_factor: float
    active: bool = True
    visible: bool = False
    last_sweep_time: float = 0.0  # Time when last swept by radar
    status: Literal['unknown', 'enemy', 'ally'] = 'unknown'  # New field for status
    # fields for trajectory tracking
    trajectory_points: List[Tuple[float, float]] = field(default_factory=list)
    show_trajectory: bool = False
    last_trajectory_update: float = 0.0

    def update_trajectory(self, current_time: float):
        """Update trajectory points with current position"""
        if current_time - self.last_trajectory_update >= 0.05:  # Update every 50ms
            self.trajectory_points.append((self.pos[0], self.pos[1]))
            self.last_trajectory_update = current_time
            
    def calculate_position(self, t: float) -> Tuple[float, float]:
        """Calculate position based on trajectory type at time t (0 to 1)"""
        # Adjust time based on speed factor
        adjusted_t = t * self.speed_factor
        if adjusted_t >= 1.0:
            return -self.start_pos[0], -self.start_pos[1]
            
        if self.trajectory_type == 'parabolic':
            return self._calculate_parabolic(adjusted_t)
        elif self.trajectory_type == 'straight':
            return self._calculate_straight(adjusted_t)
        else:  # sinusoidal
            return self._calculate_sinusoidal(adjusted_t)
    
    def _calculate_parabolic(self, t: float) -> Tuple[float, float]:
        """Parabolic trajectory using quadratic Bezier curve"""
        px = (1-t)**2 * self.start_pos[0] + \
             2*(1-t)*t * self.control_point[0] + \
             t**2 * (-self.start_pos[0])
        
        py = (1-t)**2 * self.start_pos[1] + \
             2*(1-t)*t * self.control_point[1] + \
             t**2 * (-self.start_pos[1])
        
        return px, py
    
    def _calculate_straight(self, t: float) -> Tuple[float, float]:
        """Straight line trajectory through center"""
        px = self.start_pos[0] + t * (-2 * self.start_pos[0])
        py = self.start_pos[1] + t * (-2 * self.start_pos[1])
        return px, py
    
    def _calculate_sinusoidal(self, t: float) -> Tuple[float, float]:
        """Sinusoidal trajectory through center"""
        base_x = self.start_pos[0] + t * (-2 * self.start_pos[0])
        base_y = self.start_pos[1] + t * (-2 * self.start_pos[1])
        
        dx = -self.start_pos[0]
        dy = -self.start_pos[1]
        length = math.sqrt(dx*dx + dy*dy)
        perp_x = -dy/length
        perp_y = dx/length
        
        wave_amplitude = 0.3
        wave = math.sin(t * 4 * math.pi) * wave_amplitude
        
        return (base_x + perp_x * wave,
                base_y + perp_y * wave)
    
    
    def calculate_future_trajectory(self, current_time: float) -> List[Tuple[float, float]]:
        """Calculate future trajectory points from current position"""
        future_points = []
        
        # Calculate remaining time in flight
        flight_duration = 3.0
        elapsed_time = current_time - self.creation_time
        remaining_duration = flight_duration - elapsed_time
        
        if remaining_duration <= 0:
            return future_points

        # Calculate 20 points along the remaining trajectory
        num_points = 20
        for i in range(num_points):
            t = elapsed_time + (remaining_duration * i / num_points)
            t_normalized = t / flight_duration
            if t_normalized >= 1.0:
                break
            x, y = self.calculate_position(t_normalized)
            future_points.append((x, y))
            
        return future_points

    def get_full_trajectory(self, current_time: float) -> List[Tuple[float, float]]:
        """Get combined historical and future trajectory points"""
        if not self.show_trajectory:
            return []
        
        # Combine historical points with future trajectory
        return self.trajectory_points + self.calculate_future_trajectory(current_time)

class Radar:
    def __init__(self, width=800, height=800):
        
        self.border_radius = 1.9
        self.polygon_manager = PolygonManager()
        self.min_sides = 6  # Minimum number of sides
        self.max_sides = 30  # Maximum number of sides
        self.min_polygons_number = 1  # Minimum number of polygons
        self.max_polygons_number = 5  # Maximum number of polygons
        
        # Generate random polygons on initialization
        self.generate_random_polygons()
        self.moving_objects_dict: Dict[int, MovingObject] = {}  # Dictionary to hold objects by ID

        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Radar Tracking System")
        
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 24)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-2, 2, -2, 2, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        self.sector_angle_degrees = 60.0  # Default sector angle in degrees where max number of objects are allowed
        self.angle = 0
        self.radar_speed = 5.0
        self.center_radius = 0.3
        self.moving_objects: List[MovingObject] = []
        self.last_spawn_time = time.time()
        self.spawn_delay = 1.0
        self.next_target_id = 1
        self.max_objects = 10
        self.max_objects_per_rad = 3
        self.fade_in_duration = 0.5    # Duration for object to fade in after sweep
        self.visibility_duration = 2.0  # How long object stays visible after sweep
        self.show_trajectory_ids: Set[int] = set()
    
    
    def generate_random_polygons(self):
        num_polygons = random.randint(self.min_polygons_number, self.max_polygons_number)
        for i in range(num_polygons):
            center = self.generate_border_point_inside_radar()
            polygon = self.create_random_polygon(i + 1, center)  # Pass the ID (1-based)
            self.polygon_manager.add_polygon(polygon)  # Add the VERTICES, not the Polygon object

                
    def set_sector_angle(self, angle: float):
       """Set the angular sector width in degrees."""
       self.sector_angle_degrees = angle

        
    def generate_random_speed(self) -> float:
        """Generate random speed factor between 0.5 and 2.0"""
        return random.uniform(0.05, 0.1)


    def create_random_polygon(self, polygon_id: int, center: Tuple[float, float]) -> Polygon:
        """Create a random convex polygon with a maximum angle."""
        num_sides = random.randint(self.min_sides, self.max_sides)  # Randomly choose the number of sides
        angle_offset = random.uniform(0, 90)  # Offset for the polygon's rotation
        angle_step = 90 / num_sides  # Maximum angle step
        
        vertices = []
        for i in range(num_sides):
            angle = angle_offset + i * angle_step
            rad_angle = math.radians(angle)
            radius = random.uniform(0.2, 0.5)  # Random distance from center
            x = center[0] + radius * math.cos(rad_angle)
            y = center[1] + radius * math.sin(rad_angle)
            vertices.append((x, y))
        
        #polygon_type = random.choice(self.polygon_types)
        polygon_type = random.choice(PolygonType.__args__)
        return Polygon(id=polygon_id, vertices=vertices, type=polygon_type)


    def spawn_polygons(self):
        num_polygons = random.randint(n, m)  # Define n and m
        for i in range(num_polygons):
            center = self.generate_border_point_inside_radar()  # Random position on the border
            polygon = self.create_random_polygon(i, center)
            self.polygons.append(polygon)  # Store the polygon


    def generate_control_point(self, start_pos: List[float]) -> List[float]:
        dx = -start_pos[0]
        dy = -start_pos[1]
        length = math.sqrt(dx*dx + dy*dy)
        
        perp_x = -dy/length
        perp_y = dx/length
        
        offset = random.uniform(-1, 1)
        control_x = (start_pos[0] + (-start_pos[0])) / 2 + perp_x * offset
        control_y = (start_pos[1] + (-start_pos[1])) / 2 + perp_y * offset
        
        return [control_x, control_y]
    
    def get_objects_in_sector(self, angle: float, angle_width: float = 1.0) -> int:
        """Count active objects in a given angular sector"""
        count = 0
        for obj in self.moving_objects:
            if not obj.active:
                continue
            obj_angle = math.atan2(obj.pos[1], obj.pos[0])
            if obj_angle < 0:
                obj_angle += 2 * math.pi
            if abs(obj_angle - angle) <= angle_width:
                count += 1
            count += 1
        return count


    def generate_border_point_inside_radar(self) -> Tuple[float, float]:
        """Generate a random point within the radar area."""
        radius = random.uniform(0, self.border_radius)  # Limit to within the border radius
        angle = random.uniform(0, 2 * math.pi)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        return x, y
        
    def generate_border_point(self) -> Tuple[float, float]:
        angle = random.uniform(0, 2 * math.pi)
        x = self.border_radius * math.cos(angle)
        y = self.border_radius * math.sin(angle)
        return x, y

    def spawn_new_object(self):
        # Check total object count
        active_objects = sum(1 for obj in self.moving_objects if obj.active)
        if active_objects >= self.max_objects:
            return
        
        x, y = self.generate_border_point()
        angle = math.atan2(y, x)
        if angle < 0:
            angle += 2 * math.pi
            
        # Check density in current sector
        if self.get_objects_in_sector(angle) >= self.max_objects_per_rad:
            return
            
        start_pos = [x, y]
        control_point = self.generate_control_point(start_pos)
        
        # Randomly choose trajectory type and speed
        trajectory_type = random.choice(['parabolic', 'straight', 'sinusoidal'])
        speed_factor = self.generate_random_speed()
        
        # Randomly assign status
        status = random.choice(['unknown', 'enemy', 'ally'])  # Random status
        
        new_obj = MovingObject(
            pos=[x, y],
            velocity=[0, 0],
            creation_time=time.time(),
            target_id=self.next_target_id,
            control_point=control_point,
            start_pos=start_pos,
            trajectory_type=trajectory_type,
            speed_factor=speed_factor,
            status=status  # Set status
        )
        
        # Add object to the list and dictionary
        self.moving_objects.append(new_obj)
        self.moving_objects_dict[new_obj.target_id] = new_obj  # Store in dictionary
        self.next_target_id += 1

    def render_text(self, text, x, y):
        """Render text vertically with correct orientation"""
        viewport = glGetIntegerv(GL_VIEWPORT)
        screen_x = int((x + 2) * viewport[2]/4)
        screen_y = int((-y + 2) * viewport[3]/4)  # Flip y-coordinate
        
        # Render text upright
        text_surface = self.font.render(text, True, (0, 255, 0))
        # Flip the surface vertically to fix orientation
        text_surface = pygame.transform.flip(text_surface, False, True)
        
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        text_width, text_height = text_surface.get_size()
        
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glPushMatrix()
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, viewport[2], viewport[3], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glEnable(GL_TEXTURE_2D)
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, text_width, text_height, 0, 
                     GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        # Offset text position
        screen_x += 10
        screen_y -= text_height + 10
        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(screen_x, screen_y)
        glTexCoord2f(1, 0); glVertex2f(screen_x + text_width, screen_y)
        glTexCoord2f(1, 1); glVertex2f(screen_x + text_width, screen_y + text_height)
        glTexCoord2f(0, 1); glVertex2f(screen_x, screen_y + text_height)
        glEnd()
        
        glDeleteTextures([texture_id])
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glPopAttrib()

    def draw_checkmark(self, x: float, y: float, size: float, status: Literal):
        """Draw a larger blue checkmark at position (x, y) with a specified size."""
        glBegin(GL_LINES)
        
        # Set color based on status
        if status == 'unknown':
            glColor3f(0.0, 0.0, 1.0)  # Blue for unknown
        elif status == 'enemy':
            glColor3f(1.0, 0.0, 0.0)  # Red for enemy
        elif status == 'ally':
            glColor3f(0.0, 1.0, 0.0)  # Green for ally
        #glColor3f(0.0, 0.0, 1.0)  # Set color to blue
        glVertex2f(x - size * 0.2, y - size * 0.2)  # Starting point of checkmark
        glVertex2f(x, y + size * 0.2)                # Top point of checkmark
        glVertex2f(x, y + size * 0.2)                # Top point of checkmark
        glVertex2f(x + size * 0.2, y - size * 0.2)  # Ending point of checkmark
        glEnd()
    
    def calculate_object_alpha(self, obj, current_time):
        """Calculate object's alpha (transparency) based on its state"""
        if not obj.last_sweep_time:
            return 0.0
            
        # Fade in after sweep
        time_since_sweep = current_time - obj.last_sweep_time
        if time_since_sweep < self.fade_in_duration:
            return 0.0
            
        # Start fade out if needed
        #if obj.fade_out_time:
            #fade_progress = (current_time - obj.fade_out_time) / 0.5  # 0.5s fade out
            #return max(0.0, 1.0 - fade_progress)
            
        return 1.0

    def update_object_status(self, obj_id: int, new_status: str):
        """Update the status of an object by ID."""
        if obj_id in self.moving_objects_dict:
            obj = self.moving_objects_dict[obj_id]
            obj.status = new_status  # Change status
    
    def is_in_sweep_area(self, obj_x: float, obj_y: float) -> bool:
        """Check if an object is in the current sweep area"""
        obj_angle = math.degrees(math.atan2(obj_y, obj_x))
        if obj_angle < 0:
            obj_angle += 360
            
        # Consider the sweep area (20 degrees behind the sweep line)
        sweep_start = (self.angle - 20) % 360

        # Handle wrap-around case
        if sweep_start > self.angle:
            return obj_angle >= sweep_start or obj_angle <= self.angle
        else:
            return sweep_start <= obj_angle <= self.angle
            
    def update_objects(self):
        current_time = time.time()
        
        if (current_time - self.last_spawn_time >= self.spawn_delay and 
            sum(1 for obj in self.moving_objects if obj.active) < self.max_objects):
            self.spawn_new_object()
            self.last_spawn_time = current_time
        
        for obj in self.moving_objects:
            if not obj.active:
                continue
            
            flight_duration = 3.0
            t = (current_time - obj.creation_time) / flight_duration
            
            if t * obj.speed_factor >= 1.0:
                obj.active = False
                continue
                
            obj.pos[0], obj.pos[1] = obj.calculate_position(t)
            
            next_t = min(1.0, t + 0.01)
            next_x, next_y = obj.calculate_position(next_t)
            obj.velocity = [
                (next_x - obj.pos[0]) * 100,
                (next_y - obj.pos[1]) * 100
            ]
            
            # Update trajectory points
            obj.update_trajectory(current_time)
            
            # Check if object is in sweep area
            if self.is_in_sweep_area(obj.pos[0], obj.pos[1]):
                if not obj.visible:
                    obj.last_sweep_time = current_time
                    obj.visible = True

    def draw_sweep_line(self):
        glBegin(GL_LINES)
        glColor4f(0.0, 1.0, 0.0, 1.0)
        glVertex2f(0, 0)
        
        # Calculate the endpoint of the sweep line
        x = self.border_radius * math.cos(math.radians(self.angle))
        y = self.border_radius * math.sin(math.radians(self.angle))
        glVertex2f(x, y)
        glEnd()
        
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(0.0, 0.5, 0.0, 0.15)
        glVertex2f(0, 0)
        
        # Iterate from self.angle + 75 degrees down to self.angle - 75 degrees
        for deg in range(int(self.angle + 75), int(self.angle - 1), -1):  # Notice the -1 step for clockwise
            rad = math.radians(deg)
            x = self.border_radius * math.cos(rad)
            y = self.border_radius * math.sin(rad)
            glVertex2f(x, y)
        
        glEnd()

    
    def draw_central_area(self):
        glColor4f(1.0, 0.0, 0.0, 0.2)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(0, 0)
        segments = 50
        for i in range(segments + 1):
            theta = 2.0 * math.pi * i / segments
            x = self.center_radius * math.cos(theta)
            y = self.center_radius * math.sin(theta)
            glVertex2f(x, y)
        glEnd()
        
        glColor4f(1.0, 0.0, 0.0, 1.0)
        self.draw_circle(self.center_radius)
    
    def draw_circle(self, radius, segments=50):
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            theta = 2.0 * math.pi * i / segments
            x = radius * math.cos(theta)
            y = radius * math.sin(theta)
            glVertex2f(x, y)
        glEnd()
    
    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        
        # Draw grid circles
        glColor4f(0.0, 0.3, 0.0, 1.0)
        for radius in [0.5, 1.0, 1.5]:
            self.draw_circle(radius)
            
        # Draw outer border
        glColor4f(0.0, 1.0, 0.0, 1.0)
        self.draw_circle(self.border_radius)
        
        # Draw crosshairs
        glBegin(GL_LINES)
        glVertex2f(-self.border_radius, 0)
        glVertex2f(self.border_radius, 0)
        glVertex2f(0, -self.border_radius)
        glVertex2f(0, self.border_radius)
        glEnd()
        
        self.draw_central_area()
        self.draw_sweep_line()
        self.draw_moving_objects()

    def draw_polygons(self):
        for polygon in self.polygon_manager.get_polygons():
            self.draw_polygon(polygon)
        
            # Calculate the centroid of the polygon for positioning the text
            centroid_x = sum(vertex[0] for vertex in polygon.vertices) / len(polygon.vertices)
            centroid_y = sum(vertex[1] for vertex in polygon.vertices) / len(polygon.vertices)

            # Render the polygon ID near the centroid
            glColor3f(0.5, 0.5, 0.5)  # Set color to grey for the ID text
            self.render_text(str(polygon.id), centroid_x, centroid_y)

    def remove_polygon_by_id(self, polygon_id: int):
        self.polygon_manager.remove_polygon(polygon_id)

    def run(self):
        self.set_sector_angle(35.0)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        pygame.quit()
                        return
                    elif event.key == K_UP:
                        self.radar_speed *= 1.2
                    elif event.key == K_DOWN:
                        self.radar_speed *= 0.8
                    # Handle trajectory toggling for specific objects
                    elif pygame.key.get_mods() & pygame.KMOD_CTRL:
                        if K_1 <= event.key <= K_9:
                            object_id = event.key - K_1 + 1
                            # Toggle trajectory for specific object ID
                            if object_id in self.show_trajectory_ids:
                                self.show_trajectory_ids.remove(object_id)
                            else:
                                self.show_trajectory_ids.add(object_id)
                    # Handle polygon removal (when Ctrl is not pressed)
                    elif K_1 <= event.key <= K_9:
                        number = event.key - K_1 + 1
                        if not self.polygon_manager.remove_polygon(number):
                            print(f"Polygon {number} does not exist.")

            self.update_objects()
            self.draw()
            self.angle = (self.angle + self.radar_speed) % 360
            self.draw_polygons()

            pygame.display.flip()
            pygame.time.wait(20)

    def draw_moving_objects(self):
        current_time = time.time()
        
        # Draw trajectories first (so they appear behind objects)
        for obj in self.moving_objects:
            if obj.active and obj.visible:
                # Only draw trajectory if object's ID is in show_trajectory_ids
                if obj.target_id in self.show_trajectory_ids:
                    obj.show_trajectory = True
                    trajectory_points = obj.get_full_trajectory(current_time)
                    if trajectory_points:
                        glBegin(GL_LINE_STRIP)
                        # Use object's status color for trajectory
                        if obj.status == 'unknown':
                            glColor4f(0.0, 0.0, 1.0, 0.5)  # Blue
                        elif obj.status == 'enemy':
                            glColor4f(1.0, 0.0, 0.0, 0.5)  # Red
                        else:  # ally
                            glColor4f(0.0, 1.0, 0.0, 0.5)  # Green
                        
                        for point in trajectory_points:
                            glVertex2f(point[0], point[1])
                        glEnd()
                else:
                    obj.show_trajectory = False

        # Draw objects (remains the same)
        for obj in self.moving_objects:
            if obj.active and obj.visible:
                alpha = self.calculate_object_alpha(obj, current_time)
                if alpha > 0:
                    self.draw_checkmark(obj.pos[0], obj.pos[1], status=obj.status, size=0.2)
                    glColor3f(0.5, 0.5, 0.5)
                    self.render_text(str(obj.target_id), obj.pos[0], obj.pos[1])


# Update the draw_polygon function to use the polygon's color
def draw_polygon(self, polygon: Polygon):
    """Draw a filled polygon with soft edges and enhanced radar noise effect."""
    current_time = time.time()
    
    # Use polygon's color instead of fixed color
    r, g, b = polygon.color
    
    # Draw base polygon with gradient edges
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Draw multiple layers with decreasing opacity for soft edge effect
    edge_layers = 15
    base_size = 1.0
    edge_growth = 0.008
    
    for layer in range(edge_layers - 1, -1, -1):
        scale_factor = base_size + (layer * edge_growth)
        alpha = 0.1 * (1 - (layer / edge_layers))
        
        glBegin(GL_POLYGON)
        glColor4f(r * 0.3, g * 0.3, b * 0.3, alpha)  # Darker version of polygon's color
        
        center_x = sum(v[0] for v in polygon.vertices) / len(polygon.vertices)
        center_y = sum(v[1] for v in polygon.vertices) / len(polygon.vertices)
        
        for vertex in polygon.vertices:
            scaled_x = center_x + (vertex[0] - center_x) * scale_factor
            scaled_y = center_y + (vertex[1] - center_y) * scale_factor
            glVertex2f(scaled_x, scaled_y)
        
        glEnd()
    
    # Draw main polygon body with polygon's color
    glBegin(GL_POLYGON)
    glColor4f(r, g, b, 0.7)
    for vertex in polygon.vertices:
        glVertex2f(*vertex)
    glEnd()
    
    # Initialize noise if not exists
    if not hasattr(polygon, 'noise'):
        polygon.noise = RadarNoise(polygon.vertices)
    
    # Draw noise effects with adjusted color
    for point in polygon.noise.noise_points:
        if polygon.noise.point_in_polygon(point.x, point.y):
            time_factor = current_time * point.speed + polygon.noise.time_offset
            wave = math.sin(time_factor + point.phase)
            intensity = point.intensity * (0.5 + 0.5 * wave)
            
            # Use polygon's color for noise effects
            draw_gradient_circle(
                point.x + 0.02 * math.cos(time_factor), 
                point.y + 0.02 * math.sin(time_factor),
                point.radius,
                intensity * 0.7,
                (r, g, b)  # Pass polygon's color to gradient circle
            )
    
    # Add scanning line effect with polygon's color
    scan_angle = (current_time * 2) % (2 * math.pi)
    for vertex in polygon.vertices:
        if polygon.noise.point_in_polygon(vertex[0], vertex[1]):
            angle_to_vertex = math.atan2(vertex[1], vertex[0])
            angle_diff = abs(angle_to_vertex - scan_angle)
            if angle_diff < 0.3:
                intensity = 0.2 * (1 - angle_diff / 0.3)
                draw_gradient_circle(
                    vertex[0],
                    vertex[1],
                    0.07,
                    intensity,
                    (r, g, b)  # Pass polygon's color
                )


# Update the gradient circle function to accept color
def draw_gradient_circle(x: float, y: float, radius: float, alpha: float, color: Tuple[float, float, float]):
    """Draw a circle with radial gradient using the polygon's color."""
    segments = 32
    r, g, b = color
    
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(r, g, b, alpha)  # Center color using polygon's color
    glVertex2f(x, y)
    
    glColor4f(r, g, b, 0)  # Fade to transparent while keeping the color
    for i in range(segments + 1):
        angle = 2.0 * math.pi * i / segments
        px = x + radius * math.cos(angle)
        py = y + radius * math.sin(angle)
        glVertex2f(px, py)
    glEnd()

# Add this function to update your Radar class
def update_Radar_class(Radar):
    Radar.draw_polygon = draw_polygon

update_Radar_class(Radar)

if __name__ == "__main__":
    radar = Radar()
    radar.run()