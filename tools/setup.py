from datetime import time

import tools


# tools.add_data_to_max_hang()
tools.load_from_json("basedata.json", 'max_hangs')

if not tools.check_table_exists('max_hangs'):
    try:
        tools.create_and_populate_max_hangs_table()
    except:
        print("table ")
        tools.delete_max_hang_table()
        time.sleep(10)
        tools.create_and_populate_max_hangs_table()
        tools.store_studentid_users()
