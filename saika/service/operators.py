Operators = {
    # Filter
    '==': lambda field, args: field.__eq__(*args),
    '!=': lambda field, args: field.__ne__(*args),
    '>': lambda field, args: field.__gt__(*args),
    '>=': lambda field, args: field.__ge__(*args),
    '<': lambda field, args: field.__lt__(*args),
    '<=': lambda field, args: field.__le__(*args),
    'in': lambda field, args: field.in_(*args),
    'not_in': lambda field, args: field.notin_(*args),
    'contains': lambda field, args: field.contains(*args),
    'like': lambda field, args: field.like(*args),
    'not_like': lambda field, args: field.not_like(*args),
    'ilike': lambda field, args: field.ilike(*args),
    'not_ilike': lambda field, args: field.not_ilike(*args),
    'between': lambda field, args: field.between(*args),
    # Order
    'asc': lambda field, args: field.asc(*args),
    'desc': lambda field, args: field.desc(*args),
    'nulls_first': lambda field, args: field.nulls_first(*args),
    'nulls_last': lambda field, args: field.nulls_last(*args),
}
