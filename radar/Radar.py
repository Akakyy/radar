from typing import List, Tuple, Literal
import random, math, pygame
from pygame.locals import *
from OpenGL.GL import *
import time, traceback
from radar.Noise import RadarNoise
from radar.PolygonUtils import PolygonManager, Polygon, PolygonType, Sector
from radar.MovingObject import MovingObject
from radar.SoundRecorder import AudioRecorder
    
from radar.AlgorithmRecognition import AlgorithmRecognizer


class Radar:
    def __init__(self, dir_to_save_wav, pipe, segmenter, syntax_parser, morph, width=800, height=800):
        self.dir_to_save_wav = dir_to_save_wav
        self.pipe = pipe
        self.algorithm_reconizer = AlgorithmRecognizer(self, segmenter, syntax_parser, morph)
        self.border_radius = 1.9  # максимальный радиус в радарных единицах
        self.max_distance_km = 30  # максимальная дистанция в км
        self.distance_circles = [
            {"radius": 0.5, "distance": 10},
            {"radius": 0.8, "distance": 15},
            {"radius": 1.1, "distance": 20},
            {"radius": 1.4, "distance": 25},
            {"radius": 1.7, "distance": self.max_distance_km}
        ]
        self.polygon_manager = PolygonManager()
        self.min_sides = 6
        self.max_sides = 30
        self.min_polygons_number = 1
        self.max_polygons_number = 5
        # Generate random polygons on initialization
        self.generate_random_polygons()
        self.moving_objects_dict: Dict[int, MovingObject] = {}

        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 16)  # Made font slightly smaller for better clarity
        
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
        
        self.sector_angle_degrees = 60.0
        self.angle = 0
        self.radar_speed = 5.0
        self.center_radius = 0.3
        self.moving_objects: List[MovingObject] = []
        self.last_spawn_time = time.time()
        self.spawn_delay = 1.0
        self.next_target_id = 1
        self.max_objects = 10
        self.max_objects_per_rad = 3
        self.fade_in_duration = 0.5
        self.visibility_duration = 2.0
        self.show_trajectory_ids: Set[int] = set()

        
    def create_sector(self, distance_km: float, angle: float, type: str):
        """Создает сектор, принимая расстояние в километрах"""
        #radar_distance = self.km_to_radar_units(distance_km, )
        return self.polygon_manager.create_sector(distance_km, angle, type, self.max_distance_km, self.distance_circles)
        
        
    def get_distance_from_center(self, x: float, y: float) -> float:
        """Calculate the distance from center in radar units"""
        return math.sqrt(x * x + y * y)
    
    def get_azimuth(self, x: float, y: float) -> float:
        """Calculate azimuth in degrees"""
        azimuth = math.degrees(math.atan2(y, x))
        if azimuth < 0:
            azimuth += 360
        return azimuth

    def distance_to_radar_units(self, distance: float) -> float:
        """Convert real distance (km) to radar units"""
        # Scale factor: border_radius corresponds to maximum distance (30 km)
        return (distance * self.border_radius) / 30
    
    
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
        #status = random.choice(['unknown', 'enemy', 'ally'])  # Random status
        
        new_obj = MovingObject(
            pos=[x, y],
            velocity=[0, 0],
            creation_time=time.time(),
            target_id=self.next_target_id,
            control_point=control_point,
            start_pos=start_pos,
            trajectory_type=trajectory_type,
            speed_factor=speed_factor,
            status='unknown'  # Set status
        )
        
        # Add object to the list and dictionary
        self.moving_objects.append(new_obj)
        self.moving_objects_dict[new_obj.target_id] = new_obj  # Store in dictionary
        self.next_target_id += 1

    def render_text(self, text, x, y):
        """Render multiline text with proper spacing"""
        viewport = glGetIntegerv(GL_VIEWPORT)
        screen_x = int((x + 2) * viewport[2]/4)
        screen_y = int((-y + 2) * viewport[3]/4)
        
        # Split text into lines and render each line separately
        lines = text.split('\n')
        line_height = self.font.get_height()
        
        for i, line in enumerate(lines):
            # Create surface for each line
            text_surface = self.font.render(line, True, (0, 255, 0))
            text_surface = pygame.transform.flip(text_surface, False, True)
            text_data = pygame.image.tostring(text_surface, "RGBA", True)
            text_width, text_height = text_surface.get_size()
            
            # Save current matrices
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()
            
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            glOrtho(0, viewport[2], viewport[3], 0, -1, 1)
            
            glEnable(GL_TEXTURE_2D)
            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, text_width, text_height, 0, 
                        GL_RGBA, GL_UNSIGNED_BYTE, text_data)
            
            # Adjust y position for each line
            line_y = screen_y + (i * line_height)
            
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex2f(screen_x, line_y)
            glTexCoord2f(1, 0); glVertex2f(screen_x + text_width, line_y)
            glTexCoord2f(1, 1); glVertex2f(screen_x + text_width, line_y + text_height)
            glTexCoord2f(0, 1); glVertex2f(screen_x, line_y + text_height)
            glEnd()
            
            # Cleanup
            glDeleteTextures([texture_id])
            glDisable(GL_TEXTURE_2D)
            
            # Restore matrices in reverse order
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()
            

    def draw_checkmark(self, x: float, y: float, size: float, status: Literal):
        """Draw a larger blue checkmark at position (x, y) with a specified size."""
        glBegin(GL_LINES)
        
        # Set color based on status
        if status == 'unknown':
            glColor3f(0.0, 0.0, 1.0)  # Blue for unknown
        elif status == 'враг':
            glColor3f(1.0, 0.0, 0.0)  # Red for enemy
        elif status == 'союзник':
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

    
    def update_moving_object(self, obj):
        # Update existing methods to track distance and azimuth
        if obj.active and obj.visible:
            # Calculate and store distance and azimuth
            obj.distance = self.radar_units_to_distance(
                self.get_distance_from_center(obj.pos[0], obj.pos[1])
            )
            obj.azimuth = self.get_azimuth(obj.pos[0], obj.pos[1])
            
            
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
        
    def draw_sweep_line_anti_clock_wise(self):
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
        
        # Iterate from self.angle - 75 degrees up to self.angle + 1 degrees
        for deg in range(int(self.angle - 75), int(self.angle + 1)):  # Changed to +1 step for counter-clockwise
            rad = math.radians(deg)
            x = self.border_radius * math.cos(rad)
            y = self.border_radius * math.sin(rad)
            glVertex2f(x, y)
        
        glEnd()
    def radar_units_to_distance(self, units: float) -> float:
        """Convert radar units to real distance (km)"""
        return (units * 30) / self.border_radius
        
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
        
        # Draw distance circles with labels
        for circle_info in self.distance_circles:
            self.draw_circle_with_label(circle_info)
            
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
        self.draw_sweep_line_anti_clock_wise()
        self.draw_moving_objects()
        self.draw_polygons()
        
    def draw_polygons(self):
        sector_effects = []
        for sector in self.polygon_manager.get_sectors():
            sector_effect = SectorEffect(
                sector_angle=sector.angle,
                sector_distance=sector.get_scaled_distance()
            )
            sector_effects.append(sector_effect)
        
        # Apply sector effects to polygons
        apply_sector_effects(self.polygon_manager, sector_effects)
        
        # Rest of your existing draw_polygons method remains the same
        for polygon in self.polygon_manager.get_polygons():
            self.draw_polygon(polygon)
            
            # Calculate the centroid of the polygon for positioning the text
            centroid_x = sum(vertex[0] for vertex in polygon.vertices) / len(polygon.vertices)
            centroid_y = sum(vertex[1] for vertex in polygon.vertices) / len(polygon.vertices)
            
            # Render the polygon ID near the centroid
            glColor3f(0.5, 0.5, 0.5)  # Set color to grey for the ID text
            self.render_text(str(polygon.id), centroid_x, centroid_y)
        
        # Draw all sectors
        for sector in self.polygon_manager.get_sectors():
            sector.draw()
    

    def remove_polygon_by_id(self, polygon_id: int):
        self.polygon_manager.remove_polygon(polygon_id)

    def run(self):
        self.set_sector_angle(35.0)


        #self.polygon_manager.create_sector(random.uniform(5, 25), random.uniform(0, 360), random.choice(PolygonType.__args__))
        #self.polygon_manager.create_sector(random.uniform(5, 25), random.uniform(0, 360), random.choice(PolygonType.__args__))
        # Create some test sectors
        self.create_sector(10, 45, "signal_rejection")  # At 45 degrees
        self.create_sector(28, 87, "wind")  # At 135 degrees
        audio_recorder = AudioRecorder(self.dir_to_save_wav)
        
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
                    elif event.key == K_k:
                        audio_recorder.start_recording()
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
                elif event.type == KEYUP:
                    # Stop recording when K key is released
                    if event.key == K_k:
                        
                        try:
                            filename = audio_recorder.stop_recording()
                            text = self.pipe(str(filename), generate_kwargs={"language": "russian"})
                            print(f'Recognized string: {text}')
                            self.algorithm_reconizer.recognize(text['text'].lower())
                        except Exception as e:
                            traceback.print_exc()
                            continue
                        #tokens = tokenize_russian_text(text)
                        #print('Split to tokens')
                        
            self.update_objects()
            self.draw()
            #self.angle = (self.angle + self.radar_speed) % 360
            self.angle = (self.angle - self.radar_speed) % 360
            self.draw_polygons()

            pygame.display.flip()
            pygame.time.wait(20)

    
    def draw_moving_objects(self):
        current_time = time.time()
        
        # Draw trajectories first
        for obj in self.moving_objects:
            if obj.active and obj.visible:
                self.update_moving_object(obj)
                
                if obj.target_id in self.show_trajectory_ids:
                    obj.show_trajectory = True
                    trajectory_points = obj.get_full_trajectory(current_time)
                    if trajectory_points:
                        glBegin(GL_LINE_STRIP)
                        if obj.status == 'unknown':
                            glColor4f(0.0, 0.0, 1.0, 0.5)
                        elif obj.status == 'enemy':
                            glColor4f(1.0, 0.0, 0.0, 0.5)
                        else:  # ally
                            glColor4f(0.0, 1.0, 0.0, 0.5)
                        
                        for point in trajectory_points:
                            glVertex2f(point[0], point[1])
                        glEnd()
                else:
                    obj.show_trajectory = False

        # Draw objects
        for obj in self.moving_objects:
            if obj.active and obj.visible:
                alpha = self.calculate_object_alpha(obj, current_time)
                if alpha > 0:
                    self.draw_checkmark(obj.pos[0], obj.pos[1], status=obj.status, size=0.2)
                    glColor3f(0.0, 1.0, 0.0)  # Bright green for better visibility
                    # Format text with proper spacing
                    info_text = f"ID: {obj.target_id}\n{obj.distance:.1f} km\nAZ: {obj.azimuth:.1f}°"
                    self.render_text(info_text, obj.pos[0], obj.pos[1])

    def draw_circle_with_label(self, circle_info):
        radius = circle_info["radius"]
        distance = circle_info["distance"]
        
        # Draw circle
        glColor4f(0.0, 0.3, 0.0, 1.0)
        self.draw_circle(radius)
        
        # Draw distance label with proper spacing
        label_x = radius * math.cos(math.radians(45))
        label_y = radius * math.sin(math.radians(45))
        glColor3f(0.0, 1.0, 0.0)
        self.render_text(f"{distance} km", label_x, label_y)
 
    def process_sector_effects(self):
        """
        Apply sector effects to polygons during drawing or update
        """
        for sector in self.polygon_manager.get_sectors():
            if not sector.is_active():
                # Find intersecting polygons
                for polygon in self.polygon_manager.get_polygons():
                    split_vertices = split_polygon_by_sector(polygon.vertices, sector)
                    
                    # If splitting occurred
                    if len(split_vertices) > 1:
                        self.polygon_manager.split_polygon(polygon.id, split_vertices)
                    
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


def point_in_sector(point: Tuple[float, float], sector_angle: float, sector_distance: float) -> bool:
    """
    Check if a point is inside a sector.
    
    Args:
        point: (x, y) coordinates of the point
        sector_angle: Angular width of the sector
        sector_distance: Radius of the sector
    
    Returns:
        Boolean indicating if point is in sector
    """
    # Calculate distance from center (origin)
    x, y = point
    distance = math.sqrt(x*x + y*y)
    
    # Check radius constraint
    if distance > sector_distance:
        return False
    
    # Calculate angle of the point
    point_angle = math.degrees(math.atan2(y, x))
    
    # Normalize angles
    if point_angle < 0:
        point_angle += 360
    
    # Calculate sector's start and end angles
    start_angle = 90  # As defined in sector's draw method
    end_angle = start_angle - sector_angle
    
    # Normalize end angle
    if end_angle < 0:
        end_angle += 360
    
    # Check angle constraint
    if start_angle <= end_angle:
        return start_angle <= point_angle <= end_angle
    else:
        # Sector crosses 0/360 degree boundary
        return point_angle >= start_angle or point_angle <= end_angle
        

def split_polygon_by_sector(polygon_vertices: List[Tuple[float, float]], 
                             sector_angle: float, 
                             sector_distance: float) -> List[List[Tuple[float, float]]]:
    """
    Split a polygon based on sector intersection.
    
    Args:
        polygon_vertices: List of polygon vertices
        sector_angle: Angular width of the sector
        sector_distance: Radius of the sector
    
    Returns:
        List of polygon parts after splitting
    """
    # Find which vertices are inside the sector
    inside_points = []
    
    for vertex in polygon_vertices:
        # Determine if vertex is inside sector
        is_inside = point_in_sector(vertex, sector_angle, sector_distance)
        inside_points.append(is_inside)
    
    # If all points are in or out, return original polygon
    if all(inside_points) or not any(inside_points):
        return [polygon_vertices]
    
    # Split the polygon
    split_polygons = []
    current_polygon = []
    
    # Cycle through vertices twice to handle wrap-around
    extended_vertices = polygon_vertices + [polygon_vertices[0]]
    extended_inside_points = inside_points + [inside_points[0]]
    
    current_state = extended_inside_points[0]
    
    for i in range(len(polygon_vertices)):
        current_vertex = extended_vertices[i]
        current_inside = extended_inside_points[i]
        next_vertex = extended_vertices[i+1]
        next_inside = extended_inside_points[i+1]
        
        current_polygon.append(current_vertex)
        
        # Check for state change
        if current_inside != next_inside:
            # State has changed, potentially start a new polygon
            if current_polygon:
                split_polygons.append(current_polygon)
                current_polygon = [current_vertex]
    
    # Add last polygon if not empty
    if current_polygon:
        split_polygons.append(current_polygon)
    
    return split_polygons
 
 
def apply_sector_effects(polygon_manager, sector_effects: List[SectorEffect]):
    """
    Apply sector effects to polygons
    
    Args:
        polygon_manager: PolygonManager instance
        sector_effects: List of active sector effects
    """
    # Get current polygons
    polygons = polygon_manager.get_polygons()
    
    # Temporary storage for new polygons
    polygons_to_remove = []
    polygons_to_add = []
    
    # Process each polygon against all active sector effects
    for polygon in polygons:
        modified_polygon = False
        
        for sector_effect in sector_effects:
            # Skip inactive sector effects
            if not sector_effect.is_active():
                continue
            
            # Try to split the polygon
            split_polygons = split_polygon_by_sector(
                polygon.vertices, 
                sector_effect.sector_angle, 
                sector_effect.sector_distance
            )
            
            # If polygon was split
            if len(split_polygons) > 1:
                modified_polygon = True
                
                # Remove original polygon
                polygons_to_remove.append(polygon)
                
                # Create new polygons
                for split_vertices in split_polygons:
                    new_polygon = Polygon(
                        id=polygon_manager.next_number, 
                        vertices=split_vertices, 
                        type=polygon.type
                    )
                    polygons_to_add.append(new_polygon)
                    polygon_manager.next_number += 1
        
        # If no modification occurred, keep the original polygon
        if not modified_polygon:
            continue
    
    # Remove split polygons
    for polygon in polygons_to_remove:
        polygon_manager.remove_polygon(polygon.id)
    
    # Add new polygons
    for polygon in polygons_to_add:
        polygon_manager.add_polygon(polygon)

