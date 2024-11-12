from dataclasses import dataclass, field
from typing import List, Tuple, Literal
import math


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
