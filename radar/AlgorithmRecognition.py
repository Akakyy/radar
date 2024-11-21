#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
import re
from typing import List, Tuple, Literal, get_type_hints 
from radar.MovingObject import MovingObject
from radar.NumberParser import convert_numbers_in_text


class AlgorithmRecognizer:
    def __init__(self, radar_object, segmenter, syntax_parser, morph):
        self.radar = radar_object
        self.segmenter = segmenter
        self.syntax_parser = syntax_parser
        self.morph = morph

        
    def set_moving_object_type(self, obj_id: int, type_obj: str):  # Added self parameter
        found_moving_object = [x for x in self.radar.moving_objects if x.target_id == obj_id]
        print(f'Found object to change its type: {found_moving_object}')
        if found_moving_object:
            valid_statuses = get_type_hints(MovingObject)['status'].__args__
            if type_obj in valid_statuses:
                found_moving_object[0].status = type_obj  # Access first element of list
            else:
                print(f'Cannot find such status: {type_obj}')
        else:
            print(f'Object id was not found {obj_id}')  # Fixed f-string
            
    def show_trajectory_ids(self):
        for x in self.radar.moving_objects:
            self.radar.show_trajectory_ids.add(x.target_id)
                
    def disable_trajectory_ids(self):   
        for x in self.radar.moving_objects:
            if x.target_id in self.radar.show_trajectory_ids:  # Fixed membership test
                self.radar.show_trajectory_ids.remove(x.target_id)
                
    @staticmethod
    def find_number_and_next_word(s: str, delimiter: str):
        parts = s.split(delimiter)
        if len(parts) > 1:
            for part in parts:
                match = re.search(r'(\d+)\s*(\w+)?', part)
                if match:
                    number = int(match.group(1))
                    next_word = match.group(2)
                    return number, next_word
        return None, None
    
    def recognize(self, parsed_string_from_audio: str):
        """
        Recognizes the command from a list of tokens and executes the corresponding function.
        :param parsed_string_from_audio: string representing the parsed command.
        """
        parsed_string_from_audio = convert_numbers_in_text(parsed_string_from_audio, self.segmenter, self.syntax_parser, self.morph)
        
        if parsed_string_from_audio.strip().find("цель") > -1:
            parsed_object_id, moving_object_type = self.find_number_and_next_word(
                parsed_string_from_audio.strip(), 
                "цель"
            )
            print(f'Trying to set status for id: {parsed_object_id}; status {moving_object_type}')
            if parsed_object_id:
                self.set_moving_object_type(parsed_object_id, moving_object_type)
            else:
                print(f"Object of moving id was not found here: {parsed_string_from_audio}")
        elif parsed_string_from_audio.strip().find("казать трассу") > -1:
            print('Found command: показать трассу')  # Fixed string literal
            self.show_trajectory_ids()
        elif parsed_string_from_audio.strip().find("брать трассу") > -1:
            print('Found command: убрать трассу')  # Fixed string literal
            self.disable_trajectory_ids()
        else:
            print(f"Unknown command: {parsed_string_from_audio}")