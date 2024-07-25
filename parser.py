import json
import os
from pathlib import Path

if __name__ == "__main__":
    book_title = 'Physics'
    cwd = Path.cwd()
    content_path = cwd / Path('content')

    if not cwd.exists():
        os.makedirs(cwd)

    if not content_path.exists():
        os.makedirs(content_path)

    xml_file = cwd / Path('collections/physics.collection.xml')
    toc_file = cwd / Path('toc.json')

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

