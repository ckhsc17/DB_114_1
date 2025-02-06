from DB_utils import get_user_log
from ..Action import Action

class UsersLog(Action):
    def exec(self, conn):
        user_id = self.read_input(conn, "user id that you want to filter")
        table = get_user_log(user_id)
        
        self.send_table(conn, table)