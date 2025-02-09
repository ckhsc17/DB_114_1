from ..Action import Action
from DB_utils import get_period_users

class LoginTime(Action):
     def exec(self, conn): # user is not needed
        print("Login Time Analysis hi hi bowen") # 給server看的

        start_date = self.read_input(conn, "start_date that you want to filter")
        end_date = self.read_input(conn, "end_date that you want to filter")
        interval = self.read_input(conn, "interval that you want to filter (day, hour)")

        table = get_period_users(start_date, end_date, interval) # get login stats
        #conn.send('hihi action 15 success\n'.encode('utf-8'))
        self.send_table(conn, table)
