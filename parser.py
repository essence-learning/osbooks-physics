from pathlib import Path
import xml.etree.ElementTree as ET

COLLECTION_FILE = 'physics.collections.xml'

class Module:
    def __init__(self):
        self.title = '{Page missing title}'
        self.id = 'noid'
        self.content = ''
        self.glossary = dict()

    def __repr__(self):
        return f'Title: {self.title}, id: {self.id}, content_length: {len(self.content)}, glossary_length: {len(self.glossary)}'

def tag(element):
    '''Returns tag of element with namespace removed'''
    return element.tag.split('}', 1)[1]

def text(element, section_depth):
    '''Returns parsed inner XML'''
    content = ''

    if element.text:
        content += element.text
    for child in element:
        content += generate_content(child, section_depth)
        if child.tail:
            content += child.tail

    content.strip()

    return content

def generate_content(node, section_depth) -> str:
    if 'class' in node.attrib and node.attrib['class'] == 'os-teacher':
        return ''

    output = []

    match tag(node):
        case 'content' | 'section':
            for child in node:
                output.append(generate_content(child, section_depth + 1))

        case 'para':
            output.append(text(node, section_depth))

        case 'title':
            output.append(f'{"#" * section_depth} {text(node, section_depth)}')

        case 'emphasis':
            effect = ''

            if 'effect' in node.attrib:
                match node.attrib['effect']:
                    case 'italics':
                        effect = '*'
                    case _:
                        effect = ''

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
        match tag(component):
            case 'title':
                current_module.title = component.text

            case 'metadata':
                for metadata in component:
                    if tag(metadata) == 'content-id':
                        current_module.id = metadata.text

            case 'content':
                current_module.content = generate_content(component, 0)

            case 'glossary':
                pass

            case _:
                pass

    return current_module


if __name__ == '__main__':
    cwd = Path.cwd()
    
    module_table: dict[str, Module] = dict()

    # First parse the modules
    # modules = [m for m in (cwd / 'modules').iterdir() if m.is_dir()]
    modules = [cwd / 'modules/m54081']
    for module in modules:
        print(f'Processing {module.name}')
        module_tree = ET.parse(module / 'index.cnxml')
        module_root = module_tree.getroot()

        module_obj = process_module(module_root)
        print(module_obj)
        # For each module, write conent to mdx file

        # Then, add to module table for later access to metadata
        module_table[module_obj.id] = module_obj
        print('=' * 20)
        print(module_obj.content)

