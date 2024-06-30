import xml.etree.ElementTree as ET
import json
import re

def parse_xml_to_json(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    def parse_collection(collection):
        parsed_collection = {"pages": [], "subsections": []}
        for element in collection:
            tag = element.tag.split('}')[-1]
            if tag == "module":
                parsed_collection["pages"].append(element.attrib["document"])
            elif tag == "subcollection":
                title = element.find('{http://cnx.rice.edu/mdml}title').text
                subsection = {
                    "title": title,
                }
                subsection.update(parse_collection(element.find('{http://cnx.rice.edu/collxml}content')))
                parsed_collection["subsections"].append(subsection)
        return parsed_collection

    parsed_data = parse_collection(root.find('{http://cnx.rice.edu/collxml}content'))

    return parsed_data


def cnxml_to_mdx(cnxml_content):
    root = ET.fromstring(cnxml_content)
    output_mdx = ""

    def parse_element(element):
        tag = element.tag.split('}')[-1]
        if tag == 'title':
            return f'# {element.text}\n\n'
        elif tag == 'para':
            return f'{parse_para(element)}\n\n'
        elif tag == 'section':
            return f'{parse_section(element)}\n\n'
        elif tag == 'emphasis':
            return f'*{element.text}*'
        elif tag == 'list':
            return f'{parse_list(element)}\n\n'
        elif tag == 'link':
            return f'[{element.text}]({element.attrib.get("url")})'
        elif tag == 'sup':
            return f'<sup>{element.text}</sup>'
        elif element.text:
            return element.text
        else:
            return ''.join(parse_element(e) for e in element)

    def parse_para(element):
        content = ""
        if element.text:
            content += element.text
        for child in element:
            content += parse_element(child)
            if child.tail:
                content += child.tail
        return content

    def parse_section(element):
        output = ""
        for child in element:
            child_tag = child.tag.split('}')[-1]
            if child_tag == 'title':
                output += f'## {child.text}\n\n'
            else:
                output += parse_element(child)
        return output

    def parse_list(element):
        list_type = element.attrib.get('list-type', 'bulleted')
        bullet_style = element.attrib.get('bullet-style', 'none')
        output = ""
        for item in element:
            if list_type == 'bulleted':
                bullet = '*' if bullet_style == 'none' else bullet_style
                output += f'{bullet} {parse_element(item)}\n'
            else:
                output += f'{parse_element(item)}\n'
        return output

    for element in root.findall('.//'):
        output_mdx += parse_element(element)

    return output_mdx

def write_mdx():
    with open('./modules/m54082/index.cnxml', 'r', encoding='utf-8') as f:
        cnxml_content = f.read()

    mdx_content = cnxml_to_mdx(cnxml_content)

    with open('output.mdx', 'w', encoding='utf-8') as f:
        f.write(mdx_content)


if __name__ == "__main__":
    title = 'Physics'
    xml_file = './collections/physics.collection.xml'
    json_file = f'{title}.json'

    write_mdx()

    # Convert TOC stuff
    parsed_data = {'title': title}
    parsed_data.update(parse_xml_to_json(xml_file))

    with open(json_file, 'w') as f:
        json.dump(parsed_data, f, indent=4)
