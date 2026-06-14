# 模板渲染语法

> `notification_dispatcher.py` 的 `render_template()` 使用。纯 Python 实现，零依赖。

## 三种语法

### 1. 简单变量 `{{var}}`

```markdown
{{timestamp}}
{{greeting}}
```

渲染时将 `{{var}}` 替换为 `vars_dict["var"]` 的字符串值。未找到的变量替换为 `—`（全角破折号）。

```python
vars_dict = {"timestamp": "06月03日 12:38", "greeting": "下午好"}
```

### 2. 条件渲染 `[?cond:text?]`

```markdown
[?has_unhealthy:🔴 服务断开: {{unhealthy_list}}?]
[?all_clear:✅ 全系统正常?]
```

- `cond` 在 `vars_dict` 中查找
- 值为 truthy（`True`、非空字符串、非空列表）→ 渲染 `text`
- 值为 falsy（`False`、空、`None`）→ 整块删除
- 支持多行文本，使用 `re.DOTALL` 匹配
- `text` 中可包含 `{{var}}`，会在外层替换阶段处理

### 3. 循环 `{{#each list}}...{{/each}}`

```markdown
{{#each services}}
🟢 {{name}}
{{/each}}
```

- `list` 在 `vars_dict` 中查找，必须可迭代
- 每一项的 sub-vars 在循环体内替换
- 空列表 → 整块删除

```python
vars_dict = {
    "services": [
        {"status_icon": "🟢", "name": "badminton-backend"},
        {"status_icon": "🔴", "name": "autodl-inference"},
    ]
}
```

## 渲染顺序

```
条件块 [?...?]  →  循环块 {{#each}}  →  简单变量 {{var}}  →  清理残留
```

简单变量替换最多迭代 3 轮，处理嵌套引用。

## 常见错误

| 症状 | 原因 | 修复 |
|:--|:--|:--|
| 模板顶部有原始 `{{var}}` 输出 | 注释/说明行含 `{{}}` | 用 code fence 包裹或不写此类注释 |
| `---` 分隔线残留在空白报告 | 分隔符在条件块外 | 把 `---` 移进 `[?...?]` 内 |
| 循环不输出 | key 错名或 `vars_dict` 中未传入 | 检查 `{{#each xxx}}` 的 xxx 在 vars_dict 中存在 |
| 条件块残留原始语法文本 | `?]` 闭合符被其他文本干扰 | 确保 `?]` 是条件块的唯一闭合序列 |

## 实现参考

```python
def render_template(template, vars_dict):
    result = template

    # 1. 条件块 [?cond:text?] — DOTALL 多行
    result = re.sub(
        r'\[\?(\w+):(.*?)\?\]',
        lambda m: m.group(2) if vars_dict.get(m.group(1)) else "",
        result, flags=re.DOTALL
    )

    # 2. 循环 {{#each key}}...{{/each}}
    for m in re.finditer(r'\{\{#each\s+(\w+)\}\}(.*?)\{\{/each\}\}', result, re.DOTALL):
        items = vars_dict.get(m.group(1), [])
        replaced = "\n".join(
            m.group(2).replace("{{" + k + "}}", str(v))
            for item in items for k, v in item.items()
        ) if items else ""
        result = result.replace(m.group(0), replaced)

    # 3. 简单变量 (3轮迭代)
    for _ in range(3):
        for k, v in vars_dict.items():
            if isinstance(v, (str, int, float)):
                result = result.replace("{{" + k + "}}", str(v))

    # 4. 清理
    result = re.sub(r'\{\{.*?\}\}', '—', result)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()
```
