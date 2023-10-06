from datetime import datetime
from os import path

from pandas import DataFrame


class DataStore:
    def __init__(self):
        self.reset()

    def __bool__(self):
        return len(self.lastrow) > 0

    def reset(self):
        self.lastrow = {}
        self.data = DataFrame()

    def append(self, row):
        print(row)
        self.lastrow = row
        # monkey patch append to use pandas' internal function
        self.data = self.data._append(row, ignore_index=True)
        # better would be using concat according to stackoverflow. example:
        # pd.DataFrame(df).append(new_row, ignore_index=True)
        # becomes
        # pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    def write(self, basedir, prefix):
        filename = "{}_raw_{}.csv".format(prefix, datetime.now().strftime("%Y%m%d_%H%M%S"))
        full_path = path.join(basedir, filename)
        export_rows = self.data.drop_duplicates()
        if export_rows.shape[0]:
            print("Write RAW data to {}".format(path.relpath(full_path)))
            self.data.drop_duplicates().to_csv(full_path)
        else:
            print("no data")

    def plot(self, **args):
        return self.data.plot(**args)

    def lastval(self, key):
        return self.lastrow[key]

    def setlastval(self, key, val):
        self.lastrow[key] = val
