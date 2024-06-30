import xml.etree.ElementTree as ET
import json
import os

from pathlib import Path

def parse_xml_to_json(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    def parse_collection(collection):
        parsed_collection = {"pages": [], "subsections": []}
        for element in collection:
            tag = element.tag.split('}')[-1]
            if tag == "module":
                parsed_collection["pages"].append({
                    "id": element.attrib["document"],
                    "title" : "page title"
                })
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


def cnxml_to_mdx(cnxml_file):
    root = ET.parse(cnxml_file)
    output_mdx = ""
    content_id = ""
    content_title = ""

    def parse_element(element):
        print(f'recursive parse of {element}')
        tag = element.tag.split('}')[-1]
        if tag == 'title':
            content_title = element.text
            return f'# {element.text}\n'
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
        elif tag == 'metadata':
            for e in element:
                if 'content-id' in e.tag:
                    content_id = e.text
                    break
        elif tag == 'note':
            if element.attrib['class'] == 'os-teacher':
                return ''

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

    for element in root.findall('./*'):
        print(f'top level parse of {element}')
        output_mdx += parse_element(element)

    return content_id, content_title, output_mdx

def write_mdx():
    cnxml_file = Path('./modules/m54083/index.cnxml')
    # with open('./modules/m54083/index.cnxml', 'r', encoding='utf-8') as f:
    #     cnxml_content = f.read()

    id, title, mdx_content = cnxml_to_mdx(cnxml_file)
    print(f'id: {id}, title: {title}')

    with open('output.mdx', 'w', encoding='utf-8') as f:
        f.write(mdx_content)

    return id, title


if __name__ == "__main__":
    book_title = 'Physics'
    directory_path = Path.cwd() / Path(book_title)

    if not directory_path.exists():
        os.makedirs(directory_path)

    xml_file = Path.cwd() / Path('collections/physics.collection.xml')
    toc_file = directory_path / Path('toc.json')

    write_mdx()

    # Convert TOC stuff
    parsed_data = {'title': book_title}
    parsed_data.update(parse_xml_to_json(xml_file))

    with open(toc_file, 'w') as f:
        json.dump(parsed_data, f, indent=4)
