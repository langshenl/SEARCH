# 中文搜索引擎配置

## 搜索URL模板

### 百度
```
https://www.baidu.com/s?wd={keyword}&rn=10
```
- 中文政策覆盖最全
- 结果页编码：UTF-8
- 反爬：较严格

### Bing 中国
```
https://cn.bing.com/search?q={keyword}&ensearch=0
```
- 政府网站收录好
- 结果页编码：UTF-8
- 反爬：中等

### 搜狗微信
```
https://wx.sogou.com/weixin?type=2&query={keyword}
```
- 政务文章、政策文件
- 微信生态内容
- 反爬：较宽松

### 头条搜索
```
https://so.toutiao.com/search?keyword={keyword}
```
- 最新政策资讯
- 反爬：较严格

## URL构建规则

### 编码处理
- 关键词需URL编码：`encodeURIComponent(keyword)`
- 空格转 `%20` 或 `+`

### 参数说明
- `rn=10`：每页10条结果
- `ensearch=0`：中文搜索
- `type=2`：微信搜索类型

## 结果解析规则

### 百度
```html
<!-- 结果块 -->
<div class="result">
  <h3 class="t"><a href="URL">标题</a></h3>
  <div class="c-abstract">摘要内容</div>
  <div class="c-author">来源 | 时间</div>
</div>
```

### Bing
```html
<li class="sa_item">
  <h2><a href="URL">标题</a></h2>
  <p>摘要</p>
  <span class="sa_attr">来源</span>
</li>
```

### 搜狗微信
```html
<div class="txt-box">
  <h3><a href="URL">标题</a></h3>
  <p class="txt-info">摘要...</p>
  <div class="s-p">来源 · 时间</div>
</div>
```

## 域名来源映射

从URL提取简洁来源名称：

| 域名 | 来源名称 |
|------|---------|
| gov.cn | 政府官网 |
| people.com.cn | 人民网 |
| xinhuanet.com | 新华网 |
| cctv.com | 央视网 |
| thepaper.cn | 澎湃新闻 |
| jiemian.com | 界面新闻 |
| 36kr.com | 36氪 |
| ithome.com | IT之家 |
| 163.com | 网易 |
| sohu.com | 搜狐 |
| qq.com | 腾讯 |
| weixin.qq.com | 微信 |

## 反爬应对策略

1. **延迟请求**：每个引擎间隔1-2秒
2. **随机User-Agent**：轮流使用不同UA
3. **降级方案**：某个引擎失败时继续其他引擎
4. **结果校验**：过滤明显错误/空结果

---

# 各省份政府官网（政策搜索专用）

当搜索词包含省份/城市名称时，**优先限定搜索这些政府网站**，使用 `site:{域名}` 语法。

## 省级政府网站列表

| 省份 | 政府官网 |
|------|---------|
| 北京市 | https://www.beijing.gov.cn |
| 天津市 | https://www.tj.gov.cn |
| 河北省 | https://www.hebei.gov.cn |
| 山西省 | https://www.shanxi.gov.cn |
| 内蒙古 | https://www.nmg.gov.cn |
| 辽宁省 | https://www.ln.gov.cn |
| 吉林省 | https://www.jl.gov.cn |
| 黑龙江省 | https://www.hlj.gov.cn |
| 上海市 | https://www.shanghai.gov.cn |
| 江苏省 | https://www.jiangsu.gov.cn |
| 浙江省 | https://www.zj.gov.cn |
| 安徽省 | https://www.ah.gov.cn |
| 福建省 | https://www.fujian.gov.cn |
| 江西省 | https://www.jiangxi.gov.cn |
| 山东省 | http://www.shandong.gov.cn |
| 河南省 | https://www.henan.gov.cn |
| 湖北省 | https://www.hubei.gov.cn |
| 湖南省 | https://www.hunan.gov.cn |
| 广东省 | https://www.gd.gov.cn |
| 广西 | http://www.gxzf.gov.cn |
| 海南省 | https://www.hainan.gov.cn |
| 重庆市 | https://www.cq.gov.cn |
| 四川省 | https://www.sc.gov.cn |
| 贵州省 | https://www.guizhou.gov.cn |
| 云南省 | https://www.yn.gov.cn |
| 西藏 | https://www.xizang.gov.cn |
| 陕西省 | https://www.shaanxi.gov.cn |
| 甘肃省 | https://www.gansu.gov.cn |
| 青海省 | http://www.qinghai.gov.cn |
| 宁夏 | https://www.nx.gov.cn |
| 新疆 | https://www.xinjiang.gov.cn |

## 搜索语法

### 政府网站限定
```
site:gov.cn 关键词
```

### 示例
- 用户输入：`2026年湖北政策`
- 搜索词转换：`site:hubei.gov.cn 2026年湖北政策`
- 或：`site:hubei.gov.cn 2026年 湖北 政策`

## 搜索策略

### 第一优先级（政府官网）
识别搜索词中的省份，使用 `site:{对应域名}` 搜索

### 第二优先级（综合引擎）
如果政府官网限定后结果太少，放开限制使用普通搜索

### 第三优先级（微信生态）
政策文件、解读类文章常在微信公众号发布，可额外加搜狗微信
