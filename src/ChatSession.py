import datetime


class ChatSession:
    def __init__(self, user_token):
        self.user_token = user_token
        self.chat_log = []
        self.last_updated = datetime.datetime.now()

    def get_chat_log(self):
        return self.chat_log

    def store_message(self, user_message, model_message):
        self.chat_log.extend([user_message, model_message])
        self.last_updated = datetime.datetime.now()

    def prune_chat_log(self, max_log_size):
        if len(self.chat_log) > max_log_size:
            num_messages_to_remove = len(self.chat_log) - max_log_size
            self.chat_log = self.chat_log[num_messages_to_remove:]
