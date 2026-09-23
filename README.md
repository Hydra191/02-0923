# rx-normalize

把处方统一折算成负柱镜形式的 HTTP 服务，仅使用 Python 3.14 标准库（`http.server`），无第三方依赖。

## 启动

```bash
python3.14 app.py
```

默认监听 `8000` 端口，可用 `PORT=9000 python3.14 app.py` 覆盖。

## 接口

`POST /api/v1/rx/normalize`，请求体为处方数组，每条含：

- `sphere`：球镜，屈光度，0.25 步长
- `cylinder`：柱镜，屈光度，0.25 步长
- `axis`：柱镜轴位，整数度，范围 `(0, 180]`；柱镜为 0 时可省略

柱镜为正时折算：球镜 += 柱镜、柱镜取反、轴位减 90（≤ 0 则加 180）；柱镜 ≤ 0 时原样保留。
非法记录在 `errors` 中返回下标与原因并跳过，不影响其余记录；`results` 按下标升序。

## 示例请求

```bash
curl -s -X POST http://localhost:8000/api/v1/rx/normalize \
  -H 'Content-Type: application/json' \
  -d '[{"sphere":-2.00,"cylinder":1.00,"axis":30},{"sphere":-0.50,"cylinder":0,"axis":null},{"sphere":1.25,"cylinder":-0.75,"axis":90},{"sphere":0.1,"cylinder":-0.5,"axis":181}]'
```

响应：

```json
{
  "results": [
    {"index": 0, "sphere": "-1.00", "cylinder": "-1.00", "axis": 120},
    {"index": 1, "sphere": "-0.50", "cylinder": "0.00", "axis": null},
    {"index": 2, "sphere": "1.25", "cylinder": "-0.75", "axis": 90}
  ],
  "errors": [
    {"index": 3, "reason": "sphere 不是 0.25 的整数倍"}
  ],
  "accepted": 3
}
```
