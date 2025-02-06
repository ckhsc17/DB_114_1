from ..Action import Action
from DB_utils import get_online_users

class OnlineUsers(Action):
    def exec(self, conn):
        print("Online Users Analysis")

        #user_id = self.read_input(conn, "user id that you want to filter")

        table = get_online_users()
        
        self.send_table(conn, table)