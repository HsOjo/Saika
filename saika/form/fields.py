from wtforms import Field


class DataField(Field):
    def process_formdata(self, valuelist):
        setattr(self, 'data', valuelist)
