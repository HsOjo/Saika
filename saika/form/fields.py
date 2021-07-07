from wtforms import Field


class DataField(Field):
    def process_formdata(self, valuelist):
        self.data = valuelist
