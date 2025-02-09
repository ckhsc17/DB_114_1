from ..Action import Action
from DB_utils import log_login

class UsageRate(Action):
     def exec(self, conn, user):
        print("Classroom Usage Rate Analysis hi hi") # 給server看的

        #user_id = self.read_input(conn, "user id that you want to filter")

        table = log_login()
        self.send_table(conn, table)