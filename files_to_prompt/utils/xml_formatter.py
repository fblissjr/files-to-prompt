from typing import List, Dict, Optional
import os
import xml.etree.ElementTree as ET
import xml.sax.saxutils as saxutils
import base64
import click


def read_file(file_path: str, base64_encode: bool = False) -> str:
    mode = "rb" if base64_encode else "r"
    with open(file_path, mode) as file:
        content = file.read()
        if base64_encode:
            return base64.b64encode(content).decode("utf-8")
        if isinstance(content, bytes):
            return content.decode("utf-8")
        return content


def create_document_xml(
    files: List[str],
    base64_encode_binary: bool = False,
    metadata: Optional[Dict[str, str]] = None,
) -> ET.Element:
    root = ET.Element("documents")

    for index, file_path in enumerate(files):
        try:
            file_content = read_file(file_path, base64_encode=base64_encode_binary)
            is_base64 = base64_encode_binary
        except IOError as e:
            warning_message = f"Error reading file {file_path}: {e}"
            click.echo(click.style(warning_message, fg="red"), err=True)
            continue

        document = ET.SubElement(root, "document", index=str(index))

        if metadata:
            for key, value in metadata.items():
                document.set(key, value)

        source = ET.SubElement(document, "source")
        source.text = file_path

        document_content = ET.SubElement(document, "document_content")
        if is_base64:
            document_content.set("encoding", "base64")

        if not is_base64:
            file_content = saxutils.escape(file_content)

        document_content.text = f"\n{file_content}\n"

    return root


def write_document_xml(xml_element: ET.Element) -> str:
    return ET.tostring(xml_element, encoding="unicode", method="xml")
