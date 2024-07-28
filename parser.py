from pathlib import Path
import json
import xml.etree.ElementTree as ET

class Module:
    def __init__(self):
        self.title = '{Page missing title}'
        self.id = 'noid'
        self.content = ''
        self.glossary = dict()

    def __repr__(self):
        return f'Title: {self.title}, id: {self.id}, content_length: {len(self.content)}, glossary_length: {len(self.glossary)}'

def remove_namespace(element):
    '''Removes all namespaces from XML tree'''
    for elem in element.iter():
        if isinstance(elem.tag, str):
            elem.tag = elem.tag.split('}')[-1]
    return element

def text(element, section_depth):
    '''Returns parsed inner XML'''
    content = ''

    if element.text:
        content += element.text
    for child in element:
        content += generate_content(child, section_depth)
        if child.tail:
            content += child.tail

    return content.strip()

def generate_content(node, section_depth) -> str:
    if 'class' in node.attrib and node.attrib['class'] == 'os-teacher':
        return ''

    output = []

    match node.tag:
        case 'content' | 'section' | 'list':
            for child in node:
                output.append(generate_content(child, section_depth + 1))

        case 'newline':
            return '\n'

        case 'para':
            output.append(text(node, section_depth) + '\n')

        case 'title':
            output.append(f'{"#" * section_depth} {text(node, section_depth)}')

        case 'item':
            output.append(f'* {text(node, section_depth)}')

        case 'emphasis':
            effect = '**'

            if 'effect' in node.attrib:
                match node.attrib['effect']:
                    case 'italics':
                        effect = '*'
                    case _:
                        effect = '**'

            output.append(f'{effect}{text(node, section_depth)}{effect}')

        case _:
            pass
            # for child in node:
            #     output += generate_content(child)
    return '\n'.join(output)

def process_module(root) -> Module:
    # title
    # metadata
    # content
    # glossary

    current_module = Module()

    for component in root:
        match component.tag:
            case 'title':
                current_module.title = component.text

            case 'metadata':
                for metadata in component:
                    if metadata.tag == 'content-id':
                        current_module.id = metadata.text

            case 'content':
                current_module.content = generate_content(component, 0)

            case 'glossary':
                pass

            case _:
                pass

    current_module.content = f'# {current_module.title}\n' + current_module.content

    return current_module

def process_toc(xml_file, module_table):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    remove_namespace(root)

    def parse_collection(node):
        if node.tag == 'module':
            module_id = node.attrib['document']
            module_title = module_table[module_id].title if module_id in module_table else 'No Title Found'
            parsed_collection = {'is_page': True, 'title': module_title, 'id': module_id}
        else:
            parsed_collection = {'is_page': False, 'title': 'No Title Found', 'subsections': []}

            for element in node:
                if element.tag == 'title':
                    parsed_collection['title'] = element.text
                else:
                    parsed_collection['subsections'].append(parse_collection(element))

        return parsed_collection

    parsed_data = parse_collection(root.find('content'))

    # I don't know why pyright is bugging out over this line but it works fine
    parsed_data['title'] = root.find('metadata').find('title').text

    return parsed_data


if __name__ == '__main__':
    BOOK_ID = 'physics'

    cwd = Path.cwd()
    collection_file = cwd / Path(f'collections/{BOOK_ID}.collection.xml')

    module_table: dict[str, Module] = dict()

    # Parse the modules
    # modules = [m for m in (cwd / 'modules').iterdir() if m.is_dir()]
    modules = [cwd / 'modules/m54082']
    for module in modules:
        print(f'Processing {module.name}')
        module_tree = ET.parse(module / 'index.cnxml')
        module_root = module_tree.getroot()

        remove_namespace(module_root)

        module_obj = process_module(module_root)
        print(module_obj)

        # For each module, write conent to mdx file
        with open(cwd / Path(f'content/{module_obj.id}.mdx'), 'w', encoding='utf-8') as f:
            f.write(module_obj.content)

        # Then, add to module table for later access to metadata
        module_table[module_obj.id] = module_obj
        print('=' * 20)
        print(module_obj.content)

    # Generate the TOC
    toc_data = process_toc(collection_file, module_table)
    print(json.dumps(toc_data, indent=2))
