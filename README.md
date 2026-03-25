<h1 align="center">🏪 商业选址排雷专家</h1>

<p align="center">
  <strong>给你的 AI Agent 装上顶级商业地产分析大脑与高德真实数据引擎</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/OpenClaw-Supported-orange.svg?style=for-the-badge&logo=Robot&logoColor=white" alt="OpenClaw">
  <img src="https://img.shields.io/badge/Data-AMap_LBS-green.svg?style=for-the-badge" alt="AMap">
</p>

<p align="center">
  <a href="#快速上手">快速开始</a> · <a href="#场景与痛点">解决痛点</a> · <a href="#支持的场景">支持场景</a> · <a href="#核心设计理念">设计理念</a>
</p>


## 为什么需要 AI 开店选址专家？

对于实体创业者、加盟商和投资人来说，选址是决定生死的关键一步。但传统的选址调研往往极其低效且充满陷阱：

- 💸 **“花了几万块买选址报告”** → 找咨询公司，收费高昂，等半个月才出一堆用不上的宏观数据。
- 📊 **“我觉得这里人流量挺大”** → 凭直觉去盘算，不知道旁边的地铁口全是匆忙的“假客流”。
- ☕ **“准备 80 万在杭州开个咖啡馆”** → 到底在哪个区、哪个板块、选择什么模式最不容易死？没有标准答案。
- 🗺️ **“去地图上搜一下竞品数”** → 自己手动查，根本没法建立消费水平、租售比预警、存量红海指数的综合三维模型。

**这些分析不是大模型做不到，而是大模型没有“商业思维逻辑”和“真实的地理数据”。**

普通的 AI 只能给你一句：“建议您综合考虑人流量和租金。”这完全是废话。

**AI Location Scout 把选址变成了一场专业的沉浸式数字推演：**

无需繁琐的 UI 系统，只需跟 Agent 对话交流。它拥有**严格的业务路由机制**和**真实高德地理数据引擎**，拒绝生成只说废话的 Markdown，最终一键吐出高保真、富有科技感、且可点选交互的**《选址多维评测网页大屏》**！

---

## 🧭 四大实战业务路由 (Supported Scenarios)

无论是找铺子还是验铺子，本 Agent 会自动识别意图并严格走查以下四条专业商业动线：

| 场景 | 你的提问示例 | Agent 的专业动作与硬核交付 |
|------|---------|-----------|
| 🛡️ **单点防守** | "静安寺附近想开个咖啡馆，帮我看看这个点子如何" | **极致红海排雷**。一键生成单点 HTML 研报，揭露周边 500m 最近死磕竞争者的准确距离和致命预警。 |
| 📊 **多组对比** | "这三个铺子哪个好？坐标分别在 A, B, C" | **多址数据对撞**。严格按地理坐标进行横向数据 PK，输出带有时空重叠视野的并排对比战报。 |
| 🔍 **模糊探索** | "我想在下沙开个奶茶店，预算 30 万" | **反向追问与地缘推理**。强制追问你的客群与面积需求，推理出 3 个绝佳潜力点，最后执行多点并列对比！ |
| 🏬 **反向招商** | "我手里有个 200 平沿街铺面，租给什么好" | **扫描消费真空带**。从房东视角扫描局部 POI 结构，反推最匹配及**绝对禁止入驻**的业态清单。 |

---

## 🏗️ 标杆级 Agent 工程架构 (How It Works)

这也是本开源项目最有价值的核心部分。我们没有将几十页的复杂 prompt 揉成一个大杂烩，而是采用**带严格类型检查和路由分发的多模块系统架构**。

在 `references/` 目录下，你能看到令大模型彻底告别“幻觉”的 4 大治理引擎：

1. **`routing-and-output.md` (意图路由锁)**
   硬性规定了所有请求必须优先匹配上述的“四大场景”。首创**“缺失参数强制追问”**机制（在模糊探索时，强迫大模型问清预算等前提），彻底避免 AI 自由发挥。
   
2. **`data-contracts.md` (反幻觉数据契约)**
   这是最核心的边界控制：严苛区分**【事实 Fact】**（如周边竞品数、均价）和**【推理 Inference】**（如客流潮汐、预计营收）。硬性规定大模型必须使用“基于推测...”句型，严禁其擅自捏造“占总客流 45%”等虚夸数据。
   
3. **`template-rules.md` (前端防篡改锁)**
   用非常严厉的规则锁死大模型的写码欲望。禁止它乱改暗蓝配色，禁止重写 HTML 逻辑，多店对比必须走底层的 `locationData` JSON 注入。这种强约束保证了每份研报的绝对**高保真度**。
   
4. **`report-checklist.md` (QA 自检清单)**
   大模型在交出最后一份研报给用户之前，必须在潜意识里过一遍这 12 条发货检查单（如“是否遗漏最近竞品距离”），极大幅度降低了残次品输出率。

> **提示**：这套解耦架构完全可以作为你未来开发其他高阶、高商业价值 Agent 技能的**黄金模版**。

---

## 📊 专业研报交付样式 (Professional Report Style)

这是本插件最终在终端里生成的交互式专业研报。遵循极简商业美学，拒绝冗余干扰，确保核心决策数据一目了然：

> **💡 [深度选址研报示例 (基于高德 LBS 真实数据抓取生成)]**
> ![杭州选址研报界面演示](https://raw.githubusercontent.com/yyuchenBaii/ai_location_scout/main/docs/case.png) 
> (注：如果在本地运行，点开链接即是互动大屏；如果 Agent 部署在云端服务器，Agent 会直接输出完整的 HTML 源码供你在浏览器打开。)

---

## 🔑 快速接入与 API 扫盲指南

要启动底层物理探测引擎，你需要前往 [高德开放平台](https://console.amap.com/) 获取 **两种 Key**：

1. **「Web服务 API」**（用于后台计算竞品数据）。
2. **「Web端 (JS API)」**（用于前端渲染红海地图，包含 1 个 Key + 1 个安全密钥 SecCode）。

### 🔌 安装与自动化注入


直接发给 Agent：
> **“我已经申请好高德相关的 Key 了，Web服务 Key 是 [xxx]，JSAPI Key 是 [yyy]，安全密钥是 [zzz]。请帮我配上去。”**

Agent 会自动帮你绑定所有环境变量参数。

### 稳定交付建议

如果你希望最终 HTML 信息完整、结构固定、且不残留示例内容，推荐走下面这条链路：

1. 先运行高德查询脚本，保存 JSON 结果
2. 再运行 `python scripts/assemble_report_payload.py single spec.json payload.json`
3. 或运行 `python scripts/assemble_report_payload.py compare spec.json payload.json`
4. 最后运行 `python scripts/build_report.py single payload.json output.html`
5. 或运行 `python scripts/build_report.py compare payload.json output.html`

这样比让模型直接手改整份 HTML 更稳定，尤其适合多点对比和需要长期复用的 skill。

补充说明：

- `build_report.py` 默认会检查 `AMAP_JSAPI_KEY` 和 `AMAP_SEC_CODE`
- 如果只是演示占位模板，可显式加 `--allow-missing-map-keys`

### 新增的专业能力

- `python scripts/resolve_location.py "地点描述" "城市"`：用高德输入提示 + 地理编码 + 关键字搜索做地点标准化，适合对话前置确认。
- `python scripts/fetch_location_context.py "经度,纬度"`：补充行政区编码、AOI、最近商业锚点，以及步行/驾车/公交可达性。
- `python scripts/fetch_amap_poi.py "经度,纬度" "业态关键词"`：点位周边竞品扫描。
- `python scripts/fetch_amap_poi.py "业态关键词" --mode text --adcode 330110`：按行政区做片区级竞品搜索。
- `python scripts/fetch_amap_poi.py "经度,纬度" "业态关键词" --mode polygon --polygon "lng1,lat1;lng2,lat2;..."`：按明确边界做专业扫描，适合商场、园区、街区。

这些能力里，只有对选址结论有帮助的字段会进入最终报告；输入提示和候选列表只用于前置定位确认，不直接塞进报告。

---

## 🛡️ 数据安全与配置保护

1. 所有 API 私钥均为用户自己掌握，配置在本地环境中，不涉及向第三方平台的数据外流。
2. Python 数据查询抓取采用官方标准的 HTTP 解析，轻量合法。



## 贡献与反馈

这是基于真实开店血泪史凝结出的模型架构。如果你有更好的餐饮 / 零售计算公式，甚至是全新的破局场景，欢迎大方提交 Pull Request！

**点亮右上角的 Star 🌟**
