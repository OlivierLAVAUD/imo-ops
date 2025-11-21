import json
from datetime import datetime

class JsonExportPipeline:
    def open_spider(self, spider):
        self.file = open('iad_annonces.json', 'w', encoding='utf-8')
        self.file.write('[\n')
        self.first_item = True

    def close_spider(self, spider):
        self.file.write('\n]')
        self.file.close()

    def process_item(self, item, spider):
        line = '' if self.first_item else ',\n'
        self.first_item = False
        json_line = json.dumps(dict(item), ensure_ascii=False, indent=2)
        self.file.write(line + json_line)
        return item