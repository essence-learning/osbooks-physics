import xml.etree.ElementTree as ET
import json
import os
from pathlib import Path

def remove_namespace(element):
    for elem in element.iter():
        if isinstance(elem.tag, str):
            elem.tag = elem.tag.split('}')[-1]
    return element

def parse_xml_to_json(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    remove_namespace(root)

    def parse_collection(collection):
        parsed_collection = {"pages": [], "subsections": []}
        for element in collection:
            tag = element.tag
            if tag == "module":
                parsed_collection["pages"].append({
                    "id": element.attrib["document"],
                    "title": "page title"
                })
            elif tag == "subcollection":
                title = element.find('title').text
                subsection = {
                    "title": title,
                }
                subsection.update(parse_collection(element.find('content')))
                parsed_collection["subsections"].append(subsection)
        return parsed_collection

    parsed_data = parse_collection(root.find('content'))

    return parsed_data

def cnxml_to_mdx(cnxml_file):
    root = ET.parse(cnxml_file).getroot()
    remove_namespace(root)
    output_mdx = ""
    content_id = ""
    content_title = ""

    def parse_element(element):
        tag = element.tag
        if tag == 'title':
            return f'## {element.text}\n'
        elif tag == 'para':
            return f'{parse_para(element)}\n\n'
        elif tag == 'term':
            inner = element.text if element.text else ''
            return f'**{inner.strip()}**'
        elif tag == 'caption':
            return f'<caption>{element.text}</caption>\n'
        elif tag == 'section':
            return f'{parse_section(element)}\n\n'
        elif tag == 'emphasis':
            return f'*{element.text}*'
        elif tag == 'list':
            return f'{parse_list(element)}\n'
        elif tag == 'link':
            return f'[{element.text}]({element.attrib.get("url")})'
        elif tag == 'sup':
            return f'<sup>{element.text}</sup>'
        elif tag == 'metadata':
            for e in element:
                if 'content-id' in e.tag:
                    nonlocal content_id
                    content_id = e.text
                elif 'title' in e.tag:
                    nonlocal content_title
                    content_title = e.text
            return ''
        elif tag == 'note':
            if 'class' in element.attrib:
                if element.attrib['class'] == 'os-teacher':
                    return ''
                elif element.attrib['class'] in {'learning-objectives', 'snap-lab'}:
                    objective_content = ''.join(parse_element(e) for e in element).split('\n')
                    objective_lines = [f'> {line}' for line in objective_content]
                    return '\n'.join(objective_lines) + '\n'
        elif tag == 'tbody':
            return f'{parse_table(element)}\n'
        elif tag == 'equation':
            return f'{ET.tostring(element, encoding="unicode")}\n'
        elif tag == 'math':
            return f'{ET.tostring(element, encoding="unicode")}'

        try_recurse = ''.join(parse_element(e) for e in element)
        as_str = element.text
        return try_recurse if try_recurse != '' else (as_str if as_str is not None else '')

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
            child_tag = child.tag
            if child_tag == 'title':
                output += f'### {child.text}\n\n'
            else:
                output += parse_element(child)
        return output

    def parse_list(element):
        list_type = element.attrib.get('list-type', 'bulleted')
        bullet_style = element.attrib.get('bullet-style', 'none')
        output = ""
        for i, item in enumerate(element):
            if list_type == 'bulleted':
                bullet = '*' if bullet_style == 'none' else bullet_style
                output += f'{bullet} {parse_element(item)}\n'
            else:
                output += f'{i + 1}. {parse_element(item)}\n'
        return output

    def parse_table(element):
        output = "<table>\n"
        rows = element.findall('./*')
        for row in rows:
            output += "  <tr>\n"
            for cell in row.findall('./*'):
                output += f"    <td>{parse_element(cell).strip()}</td>\n"
            output += "  </tr>\n"
        output += "</table>\n"
        return output

    for element in root.findall('./*'):
        output_mdx += parse_element(element)

    return content_id, content_title, output_mdx

def write_mdx(write_directory):
    modules_path = Path('./modules/')
    mapping_dict = dict()

    for article in modules_path.iterdir():
        print(f'parsing {article}')
        cnxml_file = article / Path('index.cnxml')

        this_id, this_title, mdx_content = cnxml_to_mdx(cnxml_file)
        mapping_dict[this_id] = this_title
        print(f'id: {this_id}, title: {this_title}')

        mdx_content.replace('\u0092', '\'')

        with open(write_directory / Path(f'{this_id}.mdx'), 'w', encoding='utf-8') as f:
            f.write(mdx_content)

    return mapping_dict

if __name__ == "__main__":
    book_title = 'Physics'
    directory_path = Path.cwd() / Path(book_title)
    content_path = directory_path / Path('content')

    if not directory_path.exists():
        os.makedirs(directory_path)

    if not content_path.exists():
        os.makedirs(content_path)

    xml_file = Path.cwd() / Path('collections/physics.collection.xml')
    toc_file = directory_path / Path('toc.json')

    id_mappings = write_mdx(content_path)

    # Convert TOC stuff
    parsed_data = {'title': book_title}
    parsed_data.update(parse_xml_to_json(xml_file))

    # update the id mappings from toc
    def update_obj(obj):
        if 'pages' in obj:
            for page in obj['pages']:
                if page['id'] in id_mappings:
                    page['title'] = id_mappings[page['id']]
        if 'subsections' in obj:
            for subsection in obj['subsections']:
                update_obj(subsection)

    update_obj(parsed_data)

    with open(toc_file, 'w') as f:
        json.dump(parsed_data, f, indent=4)
