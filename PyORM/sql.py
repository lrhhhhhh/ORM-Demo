sql_map = dict()
sql_map.update({
    '__create_db__':    'CREATE DATABASE IF NOT EXISTS {db_name};',
    '__create__':       'CREATE TABLE IF NOT EXISTS {table_name}(\n    {fields}\n)ENGINE=InnoDB DEFAULT CHARSET=utf8;',
    '__insert__':       'INSERT INTO {table_name}({fields}) VALUES ({values});',
    '__insert_many__':  'INSERT INTO {table_name}({fields}) \nVALUES \n{values};',
    '__update__':       'UPDATE {table_name} SET {fields} WHERE {clause};',
    '__delete__':       'DELETE FROM {table_name} WHERE {clause}',
    '__drop__':         'DROP TABLE IF EXISTS {table_name};',
    '__select__':       'SELECT * FROM {table_name} WHERE {condition};',
    '__select_all__':   'SELECT * FROM {table_name};',
})

