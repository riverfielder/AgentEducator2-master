class Result:
    @staticmethod
    def success(data=None, message="操作成功"):
        return {"code": 200, "message": message, "data": data}

    @staticmethod
    def error(code=400, message="操作失败"):
        return {"code": code, "message": message, "data": None}