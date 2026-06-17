import json
import csv
import random

my_integer = 4
my_float = 1.2
my_complex = 1+2j

print("result of addition is:")
print(my_integer + my_float + my_complex)


my_string = "Hello, Python!"
my_multiline_string = """
This is a string
that spans multiple lines.
"""
print("result of printing strings is:")
print(my_string + " " + my_multiline_string)

# Booleans
is_python_fun = True
is_winter = False

if is_python_fun:
    print("Python is indeed fun!")
if is_winter:
    print("It's winter!")
else:
    print("It's not winter.")

# Lists: Ordered, mutable, allows duplicates
my_list = [10, 20, 30, 'apple', is_python_fun]
print("result of printing list is:")
print(my_list)
my_list.append(40)
print("result of printing list is:")
print(my_list)

# Tuples: Ordered, immutable, allows duplicates
my_tuple = (1, 2, 3, 'banana')
#my_tuple.append(4) # This would raise an error
print("result of printing tuple is:")
print(my_tuple) 

# Sets: Unordered, mutable, unique elements only
my_set = {1, 2, 3, 3, 4} # {1, 2, 3, 4}
my_set.add(5)
print("result of printing set is:")
print(my_set)   

# Dictionaries: Unordered, mutable, key-value pairs
my_dict = {
    'name': 'Alice',
    'age': 30,
    'city': 'New York'
}
my_dict['age'] = 31 # Mutable operation
print("result of printing dictionary is:")
print(my_dict)

squared_numbers = [x**2 for x in range(5)] # List comprehension
even_numbers_set = {x for x in range(10) if x % 2 == 0} # Set comprehension
name_lengths = {name: len(name) for name in ['Alice', 'Bob', 'Charlie']}
print("result of printing squared numbers is:")
print(squared_numbers)  
print("result of printing even numbers set is:")
print(even_numbers_set) 
print("result of printing name lengths is:")
print(name_lengths)


# Function with parameters and a return value
def greet(name, message="Hello"):
    return f"{message}, {name}!"

print(greet('John'))
print(greet('Jane', 'Good morning'))

# *args and **kwargs: Variable-length arguments
def flexible_function(*args, **kwargs):
    print("Positional arguments (*args):", args)
    print("Keyword arguments (**kwargs):", kwargs)

flexible_function(1, 2, 3,4, a='apple', b='ball')

items = ["a", "b", "c"]

# enumerate — instead of: i = 0; for x in items: ... i += 1
for i, x in enumerate(items):
    print(i, x) 

names  = ["Sam", "Lee", "Jo"]
scores = [90, 85, 70]

for name, score in zip(names, scores):
    print(name, score)