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

def text(element):
    '''Returns inner XML as text'''
    return ''.join(element.itertext())

def process_module(root) -> Module:
    # title
    # metadata
    # content
    # glossary

    current_module = Module()

    for component in root:
        match tag(component):
            case 'title':
                current_module.title = text(component).strip()

            case 'metadata':
                for metadata in component:
                    if tag(metadata) == 'content-id':
                        current_module.id = text(metadata).strip()

            case 'content':
                pass
            case 'glossary':
                pass
            case _:
                pass

    return current_module


if __name__ == '__main__':
    cwd = Path.cwd()
    
    title_table = dict()

    # First parse the modules
    modules = [m for m in (cwd / 'modules').iterdir() if m.is_dir()]
    for module in modules:
        print(f'Processing {module.name}')
        module_tree = ET.parse(module / 'index.cnxml')
        module_root = module_tree.getroot()

        module_obj = process_module(module_root)
        print(module_obj)
        # For each module, write conent to mdx file

        # Then, add to title table for TOC file
        title_table[module_obj.id] = module_obj.title

