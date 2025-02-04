from ..Action import Action

class TimeAnalysis(Action):
    def exec(self, conn):
        print("List User Info")

        userid = self.read_input(conn, "user id that you want to show")

        table = list_user_info(userid)
        self.send_table(conn, table)
    
        return 