"""处方折算服务：POST /api/v1/rx/normalize 把处方数组统一折算为负柱镜形式。

仅依赖 Python 标准库（http.server）。
"""

import json
import math
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))
PATH = "/api/v1/rx/normalize"


def format_diopter(value):
    """度数保留两位小数；折算后为 0 的一律写成 0.00 而不是 -0.00。"""
    if value == 0:
        value = 0.0
    return f"{value:.2f}"


def check_diopter(record, key):
    """校验球镜/柱镜：必须是数字且为 0.25 的整数倍。返回 (值, 错误原因)。"""
    if key not in record:
        return None, f"缺少字段 {key}"
    value = record[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, f"{key} 必须是数字"
    if not math.isfinite(value):
        return None, f"{key} 必须是有限数字"
    if not (float(value) * 4).is_integer():
        return None, f"{key} 必须是 0.25 的整数倍"
    return float(value), None


def check_axis(value):
    """校验轴位：必须是 (0, 180] 内的整数。返回 (值, 错误原因)。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, "axis 必须是整数度数"
    if not float(value).is_integer():
        return None, "axis 必须是整数度数"
    axis = int(value)
    if not 1 <= axis <= 180:
        return None, "axis 必须在 (0, 180] 范围内"
    return axis, None


def normalize_record(record):
    """折算单条处方。成功返回 (结果 dict, None)，失败返回 (None, 原因)。"""
    if not isinstance(record, dict):
        return None, "记录必须是 JSON 对象"

    sphere, err = check_diopter(record, "sphere")
    if err:
        return None, err
    cylinder, err = check_diopter(record, "cylinder")
    if err:
        return None, err

    if cylinder != 0:
        # 柱镜非零时轴位必填且须合法
        if record.get("axis") is None:
            return None, "cylinder 非零时 axis 必填"
        axis, err = check_axis(record["axis"])
        if err:
            return None, err
        if cylinder > 0:
            # 正柱镜折算为负柱镜形式：球镜加柱镜、柱镜取反、轴位减 90（<=0 再加 180）
            sphere += cylinder
            cylinder = -cylinder
            axis -= 90
            if axis <= 0:
                axis += 180
        # 柱镜本为非正时三项原样保留
    else:
        axis = None  # 柱镜为 0 时轴位返回 null

    return {
        "sphere": format_diopter(sphere),
        "cylinder": format_diopter(cylinder),
        "axis": axis,
    }, None


def normalize_all(payload):
    """逐条折算；无效记录记下标与原因并跳过，不影响其余记录。"""
    results = []
    errors = []
    for index, record in enumerate(payload):
        result, reason = normalize_record(record)
        if reason is None:
            results.append({"index": index, **result})
        else:
            errors.append({"index": index, "reason": reason})
    return {"count": len(results), "results": results, "errors": errors}


class Handler(BaseHTTPRequestHandler):
    server_version = "RxNormalize/1.0"

    def do_POST(self):
        if self.path != PATH:
            self.respond(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.respond(400, {"error": "Content-Length 无效"})
            return
        try:
            payload = json.loads(self.rfile.read(max(length, 0)))
        except ValueError:
            self.respond(400, {"error": "请求体不是有效的 JSON"})
            return
        if not isinstance(payload, list):
            self.respond(400, {"error": "请求体必须是处方数组"})
            return
        self.respond(200, normalize_all(payload))

    def respond(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"listening on http://{HOST}:{PORT}{PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
