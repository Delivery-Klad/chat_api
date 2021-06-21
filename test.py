ip_table = {}


ip_table.update({f'test1': f'0.0.0.0'})
ip_table.update({f'test2': f'0.0.0.1'})
print(ip_table.get('test3'))
