from ..Action import Action
from DB_utils import log_login

class LoginBehavior(Action):
     def exec(self, conn, user):
        print("Login Time Analysis")

        #user_id = self.read_input(conn, "user id that you want to filter")

        table = log_login()
        self.send_table(conn, table)
