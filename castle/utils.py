from castle.game_objects import GameObject

def pretty_print_object(obj, indent_level=0):
   """
   Pretty prints an object's properties in a dictionary-like format with proper indentation
   """
   # Define indentation settings
   INDENT_SPACES = 4
   indent = " " * (indent_level * INDENT_SPACES)


   # Get all properties excluding built-in methods and private attributes
   properties = {key: value for key, value in vars(obj).items()
                 if not key.startswith('_')}


   # Start the output with the class name
   # output = [f"{indent}{obj.__class__.__name__} {{"]
   output = ['{']


   # Print each property with proper indentation
   for key, value in properties.items():
       # Handle nested GameObject instances recursively
       if isinstance(value, GameObject):
           nested_output = pretty_print_object(value, indent_level + 1)
           output.append(f"{indent}{' ' * INDENT_SPACES}{key}:")
           output.append(nested_output)
       else:
           # Format the value nicely
           if isinstance(value, str):
               formatted_value = f"'{value}'"
           else:
               formatted_value = str(value)
           output.append(
               f"{indent}{' ' * INDENT_SPACES}{key}: {formatted_value},")


   output.append(f"{indent}}}")
   return "\n".join(output)

def pretty_list(obj_list):
    return "\n".join([pretty_print_object(obj) for obj in obj_list])

