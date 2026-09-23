"""处方柱镜形式统一折算服务（负柱镜形式）。

仅依赖 Python 3.14 标准库 http.server。
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8000"))
EPS = 1e-9


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _to_quarters(value):
    """把屈光度折算成 0.25 的整数倍个数；非整数倍返回 None。"""
    quarters = round(value * 4)
    if abs(value * 4 - quarters) > EPS:
        return None
    return quarters


def _fmt(quarters):
    """按两位小数输出，0 恒为 0.00 而非 -0.00。"""
    if quarters == 0:
        return "0.00"
    return f"{quarters / 4:.2f}"


def _normalize_record(record):
    """返回 (结果, None) 或 (None, 原因)。"""
    if not isinstance(record, dict):
        return None, "每条处方必须是对象"

    sphere = record.get("sphere")
    cylinder = record.get("cylinder")
    axis = record.get("axis", None)

    if sphere is None:
        return None, "sphere 缺失"
    if not _is_number(sphere):
        return None, "sphere 必须为数字"
    s_q = _to_quarters(sphere)
    if s_q is None:
        return None, "sphere 不是 0.25 的整数倍"

    if cylinder is None:
        return None, "cylinder 缺失"
    if not _is_number(cylinder):
        return None, "cylinder 必须为数字"
    c_q = _to_quarters(cylinder)
    if c_q is None:
        return None, "cylinder 不是 0.25 的整数倍"

    axis_present = "axis" in record and axis is not None
    if axis_present:
        if (
            not _is_number(axis)
            or isinstance(axis, bool)
            or float(axis) % 1 != 0
            or not (0 < axis <= 180)
        ):
            return None, "axis 必须为落在 (0, 180] 的整数"
        axis = int(axis)
    elif c_q != 0:
        return None, "cylinder 非零时 axis 缺失"

    # 柱镜为正时折算为负柱镜形式
    if c_q > 0:
        s_q += c_q
        c_q = -c_q
        axis = axis - 90
        if axis <= 0:
            axis += 180

    return {
        "sphere": _fmt(s_q),
        "cylinder": _fmt(c_q),
        "axis": axis if c_q != 0 else None,
    }, None


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/v1/rx/normalize":
            self._send_json(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"null")
        except (ValueError, TypeError):
            self._send_json(400, {"error": "请求体不是合法 JSON"})
            return

        if not isinstance(payload, list):
            self._send_json(400, {"error": "请求体必须是处方数组"})
            return

        results, errors = [], []
        for index, record in enumerate(payload):
            normalized, reason = _normalize_record(record)
            if reason is not None:
                errors.append({"index": index, "reason": reason})
            else:
                results.append({"index": index, **normalized})

        results.sort(key=lambda item: item["index"])
        errors.sort(key=lambda item: item["index"])
        self._send_json(200, {
            "results": results,
            "errors": errors,
            "accepted": len(results),
        })

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}")


def main():
    server = ThreadingHTTPServer(("", PORT), Handler)
    print(f"rx normalize service listening on http://0.0.0.0:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
