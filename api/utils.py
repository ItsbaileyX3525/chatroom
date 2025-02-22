import string
import random
import time
import re


def get_random_string(length):
    letters = string.ascii_lowercase
    
    return ''.join(random.choice(letters) for i in range(length))

def read_list_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
            my_list = eval(content)
            return my_list
    except FileNotFoundError:
        print(f"The file '{filename}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

def epoch_to_dd_mm_yyyy():
    epoch_time = time.time()
    time_struct = time.gmtime(epoch_time)
    day = time_struct.tm_mday
    month = time_struct.tm_mon
    year = time_struct.tm_year
    formatted_date = "{:02d}/{:02d}/{:04d}".format(day, month, year)
    return formatted_date

data_list = read_list_from_file('./databases/emojis.emo')

def replace_colon_items(input_string, data_list=data_list):
    pattern = r':(.*?):'
    matches = re.findall(pattern, input_string)
    for match in matches:
        if match in data_list:
            input_string = input_string.replace(f':{match}:', data_list[match])
    return input_string