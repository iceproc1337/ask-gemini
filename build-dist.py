from jinja2 import Environment, FileSystemLoader

import os

# Create the output directory
output_dir = "dist"
# Check whether the specified output path exists or not
isExist = os.path.exists(output_dir)
if not isExist:
    os.makedirs(output_dir)

# Get the environment variables. This is determined by the environment on build time
APP_API_ENDPOINT = os.getenv("APP_API_ENDPOINT")

# Load templates from the input directory
file_loader = FileSystemLoader("templates")
env = Environment(loader=file_loader)

for filename in os.listdir("templates"):
    # Load the template
    template = env.get_template(filename)

    # Variables to be replaced in the template
    variables = {"api_endpoint": APP_API_ENDPOINT}

    output = template.render(variables)

    # Write the output to a file in the dist directory
    with open(os.path.join(output_dir, filename), "w") as f:
        f.write(output)

exit(0)
