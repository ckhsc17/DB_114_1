from ..Action import Action
from DB_utils import get_hot_search_dates

class PopularDate(Action):
     def exec(self, conn, user):
        print("Popular Date Analysis")

        # 讀取 Admin 輸入的天數
        days = self.read_input(conn, "Enter the number of days to analyze (e.g. 30 days)")
        
        # 驗證輸入是否為有效數字，若無則預設為 30 天
        try:
            days = int(days) if days.isdigit() else 30
        except ValueError:
            days = 30  # 預設為 30 天

        # 取得熱門查詢日期數據
        table = get_hot_search_dates(days)
        
        # 發送結果表格給 Admin
        self.send_table(conn, table)