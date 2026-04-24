# 飞书附件发送集成说明

## 功能说明

当用户在**飞书**发起搜索请求时，OpenClaw 执行技能后，需要将生成的 Excel 文件作为附件发送给飞书用户。

## 消息来源判断

在 OpenClaw 消息处理层，根据 `channel` 元数据判断：
- `channel = "feishu"` → 飞书发起，需要发送附件
- 其他渠道（webchat 等）→ 不发送，只返回文字结果

## 实现逻辑

### 1. 解析 skill 输出

`unified_search.py` 执行后，会在输出中包含文件路径：

```
搜索完成!
生成文件:
  📁 /Users/chenyiming/Desktop/smart搜索文件夹/文化和旅游部_社会力量_20260423_144517.xlsx
```

**解析方法**：在输出中查找 `📁` 或 `生成文件:` 后的路径。

**返回值**：`excel_paths` 列表，元素为完整文件路径字符串。

### 2. 飞书发送附件

当检测到飞书渠道 + 生成了 Excel 文件时，使用 `message` 工具发送附件：

```python
from message import action, channel, target, msg_type, content

# 获取发送者 open_id（从消息上下文的 SenderId 获取，格式 ou_xxx）
sender_open_id = "ou_xxxxxxxxxxxxxxxxxxxxxxxx"

# 文件绝对路径
file_path = "/Users/xxx/Desktop/smart搜索文件夹/文化和旅游部_社会力量_20260423_144517.xlsx"

# 发送文件消息
result = message(
    action="send",
    channel="feishu",
    target=sender_open_id,
    msg_type="file",
    file_path=file_path  # message 工具支持直接传本地文件路径
)
```

### 3. 完整示例代码

```python
def handle_smart_search_feishu(query, sender_open_id):
    """处理飞书发起的 smart-policy-search 搜索"""
    import subprocess, json, re

    # 1. 执行搜索
    result = subprocess.run(
        ["python3", SKILL_PATH + "/scripts/unified_search.py", query, "--source", "auto"],
        capture_output=True, text=True, timeout=120
    )
    output = result.stdout + result.stderr

    # 2. 解析生成的 Excel 文件路径
    excel_path = None
    for line in output.split("\n"):
        if "📁" in line or "生成文件:" in line:
            # 提取路径："/Users/xxx/Desktop/smart搜索文件夹/xxx.xlsx"
            match = re.search(r'[:：]\s*(/.+\.xlsx)', line)
            if match:
                excel_path = match.group(1).strip()
                break

    # 3. 如果是飞书渠道，发送附件
    if excel_path and sender_open_id:
        try:
            from message import action, channel, target, msg_type, file_path
            message(
                action="send",
                channel="feishu",
                target=sender_open_id,
                msg_type="file",
                file_path=excel_path
            )
        except Exception as e:
            print(f"飞书发送附件失败: {e}")

    # 4. 返回原始输出
    return output
```

## 关键点

1. **文件上传**：飞书不能直接发送本地文件，需要先调用 `feishu_drive_file upload` 上传到云空间，获取 `file_key`，再发送
2. **sender_open_id**：从飞书消息事件的 `sender.sender_id.open_id` 字段获取
3. **超时处理**：搜索任务可能耗时较长，建议 timeout 设为 120 秒以上
4. **非飞书渠道**：直接返回 `unified_search.py` 的文字输出即可，不触发文件发送

## 消息事件中的用户标识获取

飞书消息事件的 `event` 结构中包含发送者信息：

```json
{
  "event": {
    "sender": {
      "sender_id": {
        "open_id": "ou_c7ef480b7bce39e9dcf7a469cb08190d"
      }
    }
  }
}
```

使用 `feishu_im_user_message` 发送时，`receive_id` 填写此 `open_id`。
