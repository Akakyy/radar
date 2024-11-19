from typing import List, Tuple, Literal
from radar.MovingObject import MovingObject


class AlgorithmRecognizer:
    def __init__(self, radar_object):
        self.radar = radar_object

    def set_moving_object_type(obj_id: int, type_obj: str):
        found_moving_object = [x for x in self.radar.moving_objects if x.target_id == obj_id]
        print(f'Found object to change its type: {found_moving_object}')
        if found_moving_object:
        
            valid_statuses = get_type_hints(MovingObject)['status'].__args__
            if type_obj in valid_statuses:
                found_moving_object.status = type_obj
            else:
                print(f'Cannot find such status: {type_obj}')
        else:
            print('Object id was not found {obj_id}')

    def show_trajectory_ids():
        for x in self.radar.moving_objects:
            self.radar.show_trajectory_ids.add(object_id)
                
    def disable_trajectory_ids():   
        for x in self.radar.moving_objects:
            if x in self.radar.show_trajectory_ids:
                self.radar.show_trajectory_ids.remove(object_id)

    def find_number_and_next_word(s, delimiter):
        parts = s.split(delimiter)  # Split the string by the delimiter
        if len(parts) > 1:  # Check if splitting produced more than one part
            for part in parts:
                # Regex to find a number followed optionally by a word
                match = re.search(r'(\d+)\s*(\w+)?', part)
                if match:
                    number = int(match.group(1))  # Extract the number
                    next_word = match.group(2)  # Extract the next word (if exists)
                    return number, next_word
        return None, None  # Return None for both if no match is found

        
        
    def recognize(self, parsed_string_from_audio: str):
        """
        Recognizes the command from a list of tokens and executes the corresponding function.
        :param tokens: string representing the parsed command.
        """
        
        if parsed_string_from_audio.strip().find("цель") > -1:
            parsed_object_id, moving_object_type = find_number_and_next_word(parsed_string_from_audio.strip(), "задать цель")
            print(f'Trying to set status for id: {parsed_object_id}; status {moving_object_type}')
            if parsed_object_id:
                self.set_moving_object_type(parsed_object_id, moving_object_type)
            else:
                print(f"Object of moving id was not found here: {parsed_string_from_audio}")
        elif parsed_string_from_audio.strip().find("казать трассу") > -1:
            self.show_trajectory_ids()
        elif parsed_string_from_audio.strip().startswith("убрать трассу"):
            self.disable_trajectory_ids()

        else:
            print(f"Unknown command: {parsed_string_from_audio}")
