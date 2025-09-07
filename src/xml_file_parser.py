import xml.etree.ElementTree as ET
from typing import Dict, Any

class XMLFileParser:
    """
    A simple XML parser for .vti and .vtu files to extract and display their content.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.tree = None
        self.root = None
        self.parsed_data = {}

    def parse(self) -> None:
        """Parse the XML file and store the root element."""
        try:
            self.tree = ET.parse(self.file_path)
            self.root = self.tree.getroot()
            self.parsed_data = self._extract_content(self.root)
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse XML: {e}")
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")

    def _extract_content(self, element: ET.Element) -> Dict[str, Any]:
        """Recursively extract tag, attributes, and children from the XML element."""
        content = {
            'tag': element.tag,
            'attributes': element.attrib,
            'children': [self._extract_content(child) for child in element]
        }
        return content

    def get_summary(self) -> str:
        """Return a string summary of the XML structure for display purposes."""
        if not self.parsed_data:
            return "No data parsed. Call parse() first."
        return self._format_summary(self.parsed_data, level=0)

    def _format_summary(self, data: Dict[str, Any], level: int = 0) -> str:
        indent = '  ' * level
        summary = f"{indent}<{data['tag']}"
        if data['attributes']:
            attrs = ' '.join(f'{k}="{v}"' for k, v in data['attributes'].items())
            summary += f" {attrs}"
        summary += ">\n"
        for child in data['children']:
            summary += self._format_summary(child, level + 1)
        summary += f"{indent}</{data['tag']}>\n"
        return summary
