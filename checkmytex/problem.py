import hashlib


class Problem:
    def __init__(self, origin, message, context, long_id: str, tool: str, rule: str, search=None, look_up_url=None):
        self.short_id = str(hashlib.md5((tool + long_id).encode()).hexdigest())
        self.long_id = long_id
        self.tool = tool
        self.origin = origin
        self.message = message
        self.context = context
        self.rule = rule
        self.look_up_url = look_up_url

    def __repr__(self):
        return f"Problem[{self.tool}:{self.short_id}: {self.message} :{self.origin}]"