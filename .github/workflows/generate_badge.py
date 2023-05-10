import requests
import xml.etree.ElementTree as ET

# Replace this with the raw URL of your XML file on GitHub
xml_url = "https://raw.githubusercontent.com/dobbelina/repository.dobbelina/master/plugin.video.cumination/plugin.video.cumination/addon.xml"

# Download the XML file from its URL
response = requests.get(xml_url)

# Parse the XML file and extract the version information
try:
    root = ET.fromstring(response.content)
    version = root.find(".//version").text
except AttributeError:
    version = "Not Found"

# Generate the badge URL
badge_url = "https://img.shields.io/badge/version-{}-green.svg".format(version)

# Update the README.md file with the badge
readme_file = open("README.md", "r")
readme_lines = readme_file.readlines()
readme_file.close()
badge_line = "![Version Badge]({})".format(badge_url)
for i in range(len(readme_lines)):
    if "Version Badge" in readme_lines[i]:
        readme_lines[i] = badge_line + "\n"
        break
readme_file = open("README.md", "w")
readme_file.writelines(readme_lines)
readme_file.close()