import xmltodict


class XmlService:
    # 初始化
    def __init__(self, file_name):
        self.filename = file_name

    def read_xml(self):
        with open(self.filename, 'r') as file:
            self.data = xmltodict.parse(file.read())

    def write_xml(self, data):
        with open(self.filename, 'w') as file:
            file.write(xmltodict.unparse(data, pretty=True))
