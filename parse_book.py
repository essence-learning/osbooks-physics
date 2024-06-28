import xml.etree.ElementTree as ET
import json

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

if __name__ == "__main__":
    title = 'Physics'
    xml_file = './collections/physics.collection.xml'
    json_file = f'{title}.json'

    parsed_data = {'title': title}
    parsed_data.update(parse_xml_to_json(xml_file))

    with open(json_file, 'w') as f:
        json.dump(parsed_data, f, indent=4)
