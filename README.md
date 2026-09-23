# rx-normalize

处方折算服务：`POST /api/v1/rx/normalize` 接收处方数组（每条含 `sphere`、`cylinder`、`axis`），统一折算为负柱镜形式返回。仅依赖 Python 标准库，无第三方依赖。

## 启动

```sh
python3 app.py    # 监听 0.0.0.0:8000，可用环境变量 PORT 改端口
```

## 示例请求

```sh
curl -X POST http://localhost:8000/api/v1/rx/normalize \
  -H "Content-Type: application/json" \
  -d '[{"sphere": -1.25, "cylinder": 0.50, "axis": 180}, {"sphere": -2.00, "cylinder": -0.75, "axis": 90}, {"sphere": -0.25, "cylinder": 0.25, "axis": 10}, {"sphere": -3.00, "cylinder": 0.00}, {"sphere": 1.10, "cylinder": -0.50, "axis": 45}]'
```

响应（`results` 按输入下标升序，`count` 为合格条数，无效记录在 `errors` 中给出下标与原因）：

```json
{
  "count": 4,
  "results": [
    {"index": 0, "sphere": "-0.75", "cylinder": "-0.50", "axis": 90},
    {"index": 1, "sphere": "-2.00", "cylinder": "-0.75", "axis": 90},
    {"index": 2, "sphere": "0.00", "cylinder": "-0.25", "axis": 100},
    {"index": 3, "sphere": "-3.00", "cylinder": "0.00", "axis": null}
  ],
  "errors": [
    {"index": 4, "reason": "sphere 必须是 0.25 的整数倍"}
  ]
}
```
