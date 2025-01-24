#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
import re
from typing import List, Tuple, Literal, get_type_hints 
from radar.MovingObject import MovingObject
from radar.NumberParser import convert_numbers_in_text
from radar.PolygonUtils import PolygonType
from natasha import MorphVocab, Doc


class AlgorithmRecognizer:
    def __init__(self, radar_object, segmenter, syntax_parser, morph):
        self.radar = radar_object
        self.segmenter = segmenter
        self.syntax_parser = syntax_parser
        self.morph = morph

        
    def set_moving_object_type(self, obj_id: int, type_obj: str):  # Added self parameter
        found_moving_object = [x for x in self.radar.moving_objects if x.target_id == obj_id]
        print(f'Found object to change')
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
    
    def parse_coordinates_and_sector_type(self, text_str: str):
        # Разбиваем строку по пробелам или табуляциям
        parts = text_str.strip().split()

        # Проверка на количество элементов
        if len(parts) != 3:
            raise ValueError("Input string must contain exactly 3 parts.")

        # Парсим первое значение как целое число (расстояние в км)
        distance_km = int(parts[0])

        # Парсим второй элемент как угол в радианах
        try:
            angle_degrees = int(parts[1])
        except ValueError:
            raise ValueError("Angle must be a valid number.")

        # Парсим слово и проверяем, что оно соответствует одному из допустимых значений
        word = parts[2]
        if word not in PolygonType.__args__:
            raise ValueError(f"Invalid PolygonType. Valid options are: {', '.join(PolygonType.__args__)}")

        return distance_km, angle_degrees, word

    # Пример использования
    #input_str = "30 2 ветер"
    #try:
        #distance_km, angle_radians, word = parse_string(input_str)
        #print(f"Distance (km): {distance_km}, Angle (radians): {angle_radians}, Word: {word}")
    #except ValueError as e:
        #print(f"Error: {e}")
    
    def create_sector(self, text_str: str, delimiter: str):
    
        doc = Doc(text_str)
        doc.segment(self.segmenter)  # Split into sentences and tokens
        doc.parse_syntax(self.syntax_parser)  # Parse syntax tree to understand structure

        tokens = [_.text for _ in doc.tokens]  # Extract tokens from the document
        normalized_word = self.morph.parse(delimiter)[0].normal_form
        
        found_forms = []
        all_normalized_text = []
        # Split text into potential numeric chunks
        for token in tokens:
            word_normal = self.morph.parse(token)[0].normal_form  # Normalize each token
            #print(f'Token {token} normalized word {word_normal}')
            if (word_normal == 'градус') or (word_normal == 'километр'):
                continue
            all_normalized_text.append(word_normal)
                
        all_normalized_text = ' '.join(all_normalized_text)
        string_without_voice_command_str = all_normalized_text.split(normalized_word)[1]
        #print(f"string_without_voice_command_str: #{s.split(normalized_word)}#")
        print(f'string_without_voice_command_str {string_without_voice_command_str}')
        distance_km, angle_radians, word = self.parse_coordinates_and_sector_type(string_without_voice_command_str)
        #self.radar.polygon_manager.create_sector(distance_km, angle_radians, random.choice(PolygonType.__args__))
        self.radar.create_sector(distance_km, angle_radians, word)
        for x in self.radar.moving_objects:
            if x.target_id in self.radar.show_trajectory_ids:  # Fixed membership test
                self.radar.show_trajectory_ids.remove(x.target_id)

                
    @staticmethod
    def find_number_and_next_word(s: str, delimiter: str):
        print(f'Parsing text: {s}')
        parts = s.split(delimiter)
        if len(parts) > 1:
            for part in parts:
                match = re.search(r'(\d+)\s*(\w+)?', part)
                if match:
                    number = int(match.group(1))
                    next_word = match.group(2)
                    print(f'number {number} status {next_word}')
                    return number, next_word
        return None, None

    
    def find_word_forms_in_text(self, word, text):
        # Генерируем все формы слова
        doc = Doc(text)
        doc.segment(self.segmenter)  # Split into sentences and tokens
        doc.parse_syntax(self.syntax_parser)  # Parse syntax tree to understand structure

        tokens = [_.text for _ in doc.tokens]  # Extract tokens from the document
        normalized_word = self.morph.parse(word)[0].normal_form

        found_forms = []
        # Split text into potential numeric chunks
        for token in tokens:
            word_normal = self.morph.parse(token)[0].normal_form  # Normalize each token
            print(f'Token {token} normalized word {word_normal}')
            if word_normal == normalized_word:
                found_forms.append(word_normal)
        return found_forms
    
    def extract_words(self, text):
        # Используем регулярное выражение для поиска всех слов (с учетом кириллицы и латиницы)
        #print(f'before {text}')
        words_and_numbers = re.findall(r'[а-яА-ЯёЁa-zA-Z0-9]+', text)
        #print(f'after {words}')
        return words_and_numbers

    def recognize(self, parsed_string_from_audio: str):
        """
        Recognizes the command from a list of tokens and executes the corresponding function.
        :param parsed_string_from_audio: string representing the parsed command.
        """
        parsed_string_from_audio = convert_numbers_in_text(parsed_string_from_audio, self.segmenter, self.syntax_parser, self.morph)
        parsed_string_from_audio = ' '.join(self.extract_words(parsed_string_from_audio.strip()))
        
        print(f'Cleaned string: {parsed_string_from_audio}')
        found_forms_aim = self.find_word_forms_in_text("цель", parsed_string_from_audio)
        found_forms_sector = self.find_word_forms_in_text("сектор", parsed_string_from_audio)
        found_forms_set = self.find_word_forms_in_text("создать", parsed_string_from_audio)
        
        print(f'Found forms {str(found_forms_aim)}')
        if found_forms_aim:
            parsed_object_id, moving_object_type = self.find_number_and_next_word(
                parsed_string_from_audio, 
                found_forms_aim[0]
            )
            word_normal = self.morph.parse(moving_object_type)[0].normal_form
            #print(f'word_normal {word_normal} {dir(word_normal)}')
            
            found_forms_object_type = self.find_word_forms_in_text(word_normal, parsed_string_from_audio)
            #print(f'ggg {str(found_forms_object_type)}')
            if found_forms_object_type:
                moving_object_type = found_forms_object_type[0]
                print(f'Trying to set status for id: {parsed_object_id}; status {moving_object_type}')
                if parsed_object_id:
                    self.set_moving_object_type(parsed_object_id, moving_object_type)
                else:
                    print(f"Object of moving id was not found here: {parsed_string_from_audio}")
            else:
                print(f"Object type was not parsed (morph error) {moving_object_type}")
        elif parsed_string_from_audio.find("казать трас") > -1:
            print('Found command: показать трассу')  # Fixed string literal
            self.show_trajectory_ids()
        elif parsed_string_from_audio.find("брать трас") > -1:
            print('Found command: убрать трассу')  # Fixed string literal
            self.disable_trajectory_ids()
        #elif parsed_string_from_audio.find("дать сектор") > -1:
        elif found_forms_sector and found_forms_set:
            print('Found command: создать сектор')  # Fixed string literal
            self.create_sector(parsed_string_from_audio, "сектор")
            # создать вектор 10 километров 90 градусов ветер 
        else:
            print(f"Unknown command: {parsed_string_from_audio}")