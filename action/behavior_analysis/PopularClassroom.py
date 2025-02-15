from ..Action import Action
from DB_utils import get_classroom_utilization

class PopularClassroom(Action):
    def exec(self, conn, user):
        """
        執行 PopularClassroom 操作：
         - 讀取使用者指定的期間（起始日期與結束日期，yyyymmdd 格式）
         - 呼叫 get_classroom_utilization() 取得教室租借統計資料
         - 將統計結果組成訊息，並透過 socket (conn) 傳送給 client
        """
        print("Popular Classroom Analysis: 統計指定期間內各教室租借與閒置時間比例")
        try:
            # 讀取使用者指定的日期範圍（假設 Action 有實作 read_input 方法）
            start_date = self.read_input(conn, "起始日期 (yyyymmdd)")
            end_date   = self.read_input(conn, "結束日期 (yyyymmdd)")

            data = get_classroom_utilization(start_date, end_date)
            
            # 組合訊息內容
            message_lines = []
            header = "classroom_id | total_reserved | total_possible | reserved_ratio | idle_ratio"
            message_lines.append(header)
            for row in data:
                classroom_id, total_reserved, total_possible, reserved_ratio, idle_ratio = row
                message_lines.append(
                    f"{classroom_id} | {total_reserved} | {total_possible} | {reserved_ratio} | {idle_ratio}"
                )
            message = "\n".join(message_lines)
            
            # 傳送訊息給 client
            conn.sendall(message.encode("utf-8"))
        except Exception as e:
            error_message = f"執行 PopularClassroom 時發生錯誤: {str(e)}"
            print(error_message)
            conn.sendall(error_message.encode("utf-8"))
