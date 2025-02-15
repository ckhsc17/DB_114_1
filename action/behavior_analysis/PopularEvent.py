from ..Action import Action
from DB_utils import get_top_popular_events

class PopularEvent(Action):
    def exec(self, conn, user):
        """
        執行 PopularEvent 操作：
         - 呼叫 get_top_popular_events() 取得資料庫查詢結果
         - 將結果轉換為字串訊息
         - 透過 socket (conn) 傳送訊息給 client
        """
        print("Popular Event Analysis: 列出完成率最高的 10 個活動")
        try:
            # 取得完成率最高的活動資料
            events = get_top_popular_events()
            
            # 組合字串訊息
            message_lines = []
            header = "event_id | participant_count | user_max | participation_rate"
            message_lines.append(header)
            for row in events:
                event_id, participant_count, user_max, participation_rate = row
                message_lines.append(f"{event_id} | {participant_count} | {user_max} | {participation_rate}")
            message = "\n".join(message_lines)
            
            # 傳送訊息給 client
            conn.sendall(message.encode("utf-8"))
        except Exception as e:
            error_message = f"執行 PopularEvent 時發生錯誤: {str(e)}"
            print(error_message)
            conn.sendall(error_message.encode("utf-8"))
