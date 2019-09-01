# -*- coding: utf-8 -*-
import csv

class CSV:
    def GetDictFromCsv(self, csv_file):
        """
        引数のCSVファイルを辞書データに変換する
        :params
            csv_file(str): csvファイルパス
        :return
            result_dict
        """
        data = []
        with open(csv_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
if __name__ == '__main__':
    test = CSV().GetDictFromCsv('../input/buyma_link.csv')
    print(test)