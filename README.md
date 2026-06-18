# BCZ-Automata

账号矩阵管理器（打卡、互动、点赞、海报、招新卡、加退班、公告阅读和修改、授权）

## ⚠️ 免责申明

感谢您选择使用本小班数据管理器。在使用本程序之前, 请您**仔细阅读**并理解以下免责声明内容：

- 本程序基于[GPLv3](https://www.gnu.org/licenses/agpl-3.0.html)开源，仅供个人学习、研究和其他非商业性质的合法用途, 任何因违反相关法律法规或侵犯他人权益所导致的法律责任, 由用户自行承担。
- 用户在使用本程序时, 应遵守所在国家或地区的法律法规, 并对使用该程序产生的一切后果负全部责任。
- 本程序对于用户使用过程中可能产生的各种风险（包括但不限于被数据来源公司的封禁、用户自身合规问题等）不承担任何责任。
- 用户违反本声明或者滥用本程序进行非法活动的, 数据来源公司将有权追究您的法律责任。
- 本程序作者对用户使用本程序产生的一切纠纷、损失或伤害不承担任何责任。
- 一旦用户开始使用本程序, 则视为用户已充分理解并同意本免责声明的全部内容, 如果您无法接受上述条款, 请**立即停止**使用本程序。

## ⚠️ 安全警告

- 本程序没有添加鉴权模块，请在内网使用或自行添加。

---

## 第一部分：开始使用

### 1.1 获取令牌

项目提供两种方式获取百词斩账号令牌：

**方式一：短信验证码登录**（推荐）

```bash
python lp.py
```

运行后输入手机号，接收验证码，令牌会自动复制到剪贴板。

**方式二：账号密码登录**

```bash
python lm.py
```

运行后输入用户名和密码，令牌会自动复制到剪贴板。

### 1.2 导入令牌

后续添加账号方法同此。

1. **启动主程序**：`python app.py` 
   - 程序会自动生成 `config.json`，修改后重启即可正常运行。
   
   需要先配置的是主令牌（`main_token`）建议使用不加入任何小班的试用账号。

   其余配置可以先使用默认，后续参照第三部分修改，重启主程序生效。

2. **添加账号**：访问 `http://localhost:8850/append`
   - 下载csv模板，在Excel等打开后填写账号信息（令牌、昵称、配置等）
   - 从Excel中复制，黏贴到网站输入框，提交

3. **管理账号，阅读公告和打卡**
   - 访问 `http://localhost:8850/accounts`
   - 查看账号列表、打卡状态、铜板数量、IP等基本信息、执行打卡、加入退出班级等操作

   点击账号后面的“加载”或“刷新”按钮即可显示或更新上述信息。部分信息和操作位于账号表格的最后一行和最后一列。
   
   - 可以快捷的修改公告、查违禁词和互动

   点击显示公告的单元格，如果是班长则可以修改和发布公告，如果是成员则可以快速查看班内有哪些成员修改了班内昵称，及其打卡天数、漏卡情况。

   班长在修改公告时，点击下方成员列表（包含上述的昵称头像、打卡天数和漏卡情况）可以快捷插入@成员内容。

   发送公告时，建议先用`ystkc.github.io/check`检查公告是否有违禁词，并复制一份副本，按照网站上提示的在末尾加上一段内容，然后发送。如果违禁，程序会从后往前逐字删除再发送。在开头加上`>`可以改为从前往后。在开头加上`#`可以禁用逐字删除程序。

   - 打卡

   打卡过程包括查看每日一句、新学、复习拼写、斩词、打卡、分享、领取同桌、小班、铜板商城每日奖励、同桌双人战、和任务中心的部分每日任务。新学5复习5的情况下大约需要5分钟。如需快速打卡，请使用`python dk.py`。

   打卡计划已经硬编码，每天早上5-10点会自动打卡（第一次进入该时间区域时会自动打卡，启动时如果已经在该时间区域会马上开始）。当然也可以在网页端的账号信息右下角的打卡按钮进行手动打卡，流程基本相同。
   

4. **查看公告和互动、授权分班支援和管理（互班、海报和招新卡）**
   - 访问 `http://localhost:8850/subscribe`
   
   如果更喜欢控制台版本，可以使用`python subscribe.py`，功能完全相同。启动时扫描订阅信息大约需要20秒

   不论账户类型，当订阅的账户有公告更新，会展示在订阅列表中。
   
   如果订阅的账户是班长，会在周一提醒是否发送招新卡。

   如果订阅的账户有授权分班，会每次扫描一个最久没访问过的授权分班，可以对其进行点赞、账号支援、改名互动和收到、发送海报、解除授权等。

5. **查看追踪的班级数据**
   - 访问 `http://localhost:8850/groups`
   
   数据收集器有两部分，一部分是排行榜，另一部分是自行添加的关注班级。此页面会展示关注班级历史每天的打卡数、每周打卡数和每周排名，以及成员的停留历史记录。

   若要使用此功能，需要部署到服务器，或每天晚上开启本程序保持运行，开启本地模式后，程序在零点收集完数据后会自动关闭电脑。

6. **查看其他班级和历史公告**
   - 访问 `http://localhost:8850/notice`
   
   查看指定班长管理的班级公告历史。同上需要部署到服务器或晚上收集数据

### 1.5 魔法令牌功能
- 如果需要使用魔法令牌，请自行在移动端或移动端模拟器安装 mitmproxy 的 CA 证书并代理到 8080 端口
- 如果需要配合 fiddler 使用魔法令牌，请自行在移动端或移动端模拟器安装 fiddler 的 CA 证书，并配置 fiddler 代理到本地 8080 端口 + 忽略服务器证书错误，且移动端或移动端模拟器代理到本地 8888 端口

### 1.6 运行参数

- **`--debug`** 使用调试模式运行，使用修改重载、只加载前三个账号，不使用 gevent 服务器，只使用 flask 自带服务器，并发数较少
- **`--static`** 不加载 Schedule（忽略 `archiever_enable` 设置）默认加载Schedule可以用于每天自动打卡
---

## 第二部分：主要结构

### 2.1 Templates 目录

Templates 目录包含前端页面模板，用于 Web 界面展示：

| 文件 | 功能 |
|------|------|
| `templates/accounts.html` | **账号矩阵管理** - 查看所有账号列表、打卡状态、批量操作 |
| `templates/append.html` | **账号导入** - 通过表格批量添加或更新账号信息 |
| `templates/delete.html` | **账号删除** - 通过表格批量删除账号 |
| `templates/groups.html` | **班级数据可视化** - 查看班级排名、成员历史、打卡统计图表 |
| `templates/login.html` | **登录页面** - 手机号验证码登录获取令牌 |
| `templates/notice.html` | **班级公告查看器** - 查看指定班长管理的班级公告历史 |
| `templates/subscribe.html` | **公告订阅** - 查看订阅账号的班级公告更新，进行回复操作 |
| `templates/user.html` | **用户详情** - 显示登录后获取的用户 ID 和令牌 |

### 2.2 Log 日志目录

日志目录位于 `./logs/`，包含 4 类日志：

| 日志类型 | 文件格式 | 说明 |
|----------|----------|------|
| **cheat-tracker** | `cheat-tracker_YYYY-MM-DD.csv` | 作弊追踪日志，记录 500 词以上用户的作弊、爆破情况 |
| **log** | `log_YYYY-MM-DD_HH-MM-SS.txt` | 主程序运行日志，记录打卡、数据采集等操作 |
| **pk** | `pk_YYYY-MM-DD_HH-MM-SS.csv` | PK 对战记录，包含对手 ID、分数等信息 |
| **subscriber** | `subscriber_YYYY-MM-DD.csv` | 订阅公告日志，记录公告更新和回复操作 |

### 2.3 数据文件

| 文件 | 说明 |
|------|------|
| `config.json` | 系统配置文件，包含所有运行参数 |
| `lookup_patch.db` | **PK 词库补丁** - 记录已做过的 PK 题目，减少重复查询和错误 |
| `lookup.db` | 基础词库，`lookup_patch.db` 为其拓展 |
| `puzzle.db` | **YZDD 记录表** - 记录一站到底答题数据 |
| `stargazer.db` | **反挂追踪记录** - 记录反挂狙击程序的对战情况 |
| `user_cookie.json` | **账号数据文件** - 存储所有账号的 cookie 和配置信息 |
| `yzdd.db` | 一站到底数据库 |
| `bcz_notice.db` | 公告数据库（`database_path` 默认值，仅 `archiever_enable` 为 true 时生成） |

---

## 第三部分：config.json 配置说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| **`host`** | `127.0.0.1` | 服务器地址 |
| **`port`** | `8850` | 服务器端口 |
| **`main_token`** | `''` | 主账号令牌，可用试用账号令牌（必填） |
| **`database_path`** | `../BCZ-Notice-Examiner/bcz_notice.db` | archiever 储存库，含公告、用户、班级、连胜信息 |
| **`archiever_enable`** | `False` | archiever 开关，开启时每天固定时间爬取信息并储存 |
| **`class_list_2048`** | - | 如果要 archiever 额外爬取不在榜上的小班，可以将sharekey加入此处。不受 archiever 开关控制 |
| **`dict_patch_db_path`** | `./lookup_patch.db` | PK 补丁包，记录做过的题，减少查询和错误 |
| **`puzzle_path`** | `./puzzle.db` | YZDD 记录表 |
| **`local`** | `False` | 本地模式。开启时会每天固定时间执行同步、阻止休眠、允许休眠和关机命令 |
| **`sync_command`** | `[]` | 每天早上执行一次，可以手动添加备份命令，或启动如订阅公告 `start subscribe.py` 等方便管理的小工具 |
| **`prevent_sleep_command`** | `timeout` | 每天傍晚执行一次，防止在晚上爬取数据时本地设备休眠而无法正常运行。功能：设置笔记本合盖操作无，睡眠永不，休眠永不 |
| **`allow_sleep_command`** | `timeout reverse` | 每天半夜数据爬取结束后执行一次。功能：睡眠 3 分钟，休眠 3 分钟 |
| **`shutdown_command`** | `shutdown -s -t 900` | 每天半夜数据爬取结束后执行一次，建议：定时 900s 以上关机 |
| **`log_dir`** | `./logs/` | 日志目录，包括 daka、pk、subscribe、stargazer、cheat_tracker |
| **`check_notice_pace`** | `3` | 涉嫌违禁公告自动后往前查违禁步长。在公告前面加上 `#` 可以取消自动，加 `>` 改方向为前往后 |
| **`pk_blacklist`** | `[]` | PK 黑名单，遇到后改为强反挂模式。但属于被动反挂，对于极端挂无法获胜。反极端挂请使用 stargazer |
| **`pk_whitelist`** | `[]` | PK 白名单，遇到后禁用反挂，即便对方开挂也只会跟随分数 |
| **`stargazer_enable`** | `True` | 启动 stargazer 功能 |
| **`stargazer_db`** | `stargazer.db` | stargazer 跟踪记录 |
| **`anticheat_power`** | `10` | 初始反挂力度，最低 0 时第一手 188，最高 25 时第一手 199，建议 5-10 |
| **`do_not_charge_pk_energy`** | `True` | 不使用铜板充能 |
| **`arbiter_interval`** | `1` | arbiter 发车时间间隔，单位秒，发车总时长 = `arbiter_size * arbiter_interval + arbiter_offset` |
| **`arbiter_offset`** | `2` | arbiter 胜利后，开始下一轮的延迟，单位秒 |
| **`arbiter_size`** | `8` | 建议最大值：总账号数 / (60 秒每体力 * 10 体力每次) * 30s 每局 * 2，理论最大值 18，还要测试确保带宽足够 |

---

## 第四部分：备份说明

### 4.1 重要数据

主程序：

1. 以下数据建议每次修改后都及时备份：

   - `config.json`（如果有修改）
   - `user_cookie.json`（建议保留原来的 excel 文件）

2. 以下数据是自动的数据采集生成，删除后会自动生成，但会丢失历史数据。可以定期备份

   - `config.database_path`（默认值 `../BCZ-Notice-Examiner/bcz_notice.db`，仅 `archiever_enable` 为 true 时生成）
   - `./yzdd.db`（硬编码，暂不支持更改，仅开启 YZDD 功能后生成）
   - `config.puzzle_path`（默认值 `./puzzle.db`，仅开启 BCZ_NCSVC 功能后生成）
   - `config.dict_patch_db_path`（默认值 `./lookup_patch.db`）
   - `config.stargazer_db`（默认值 `./stargazer.db`）

groupmanager：

1. 以下数据建议每次修改后都及时备份：

   - `config.json`（如果有修改）
   - `strategy.json`（策略设置）
   - `monitor.json`（自动化设置）

2. 以下数据是自动的数据采集生成，删除后会自动生成，但会丢失历史数据。可以定期备份

   - `data.db`（储存群组信息、班长信息、用户数据、筛选历史、打卡历史等，建议所有表都保留 1-2 个星期内的数据）
   - `tidal_token.json` 和 `poster_token.json`（一般和 `user_cookie.json` 同时生成，建议保留原来的 excel 文件）

### 4.2 生成但不重要（无需备份）

- `./lookup.db`（由 `lookup.rar` 解压）
- `./learnt_words.db`（硬编码，即将废除）
- `./storage`（储存小号查询后的缓存）
- `./logs`（储存日志、警告和错误、作弊追踪名单、订阅已读清单）
- `./tmp_bad_words.json`（目前检查到的坏词）

---

## 第五部分：独立工具清单

### 5.1 账号管理工具

| 工具 | 功能 |
|------|------|
| `append.py` | 导入/更新/删除账号数据到 `user_cookie.json`，用法同启动后访问 `/append` |
| `lm.py` | 通过账号密码获取令牌 |
| `lp.py` | 通过短信验证码获取令牌 |
| `dk.py` | 快速打卡测试工具 |

### 5.2 PK 对战工具

| 工具 | 功能 |
|------|------|
| `king.py` | **上段程序** - 将允许 PK 的账号自动上段至王者1星 |
| `stargazer.py` | **反挂追踪** - 跟踪指定用户并尝试与其匹配单词对战，狙击其上星操作 |
| `interval.py` | PK 时间间隔分析 - 分析被狙击者的星数变化的时间差并作图 |
| `pk_result_query.py` | 查询自动 PK 程序的对局记录 |
| `ttbb.py` | **PK 词库导出器** - 导出各段位 PK 词库，可筛除简单词 |

### 5.3 公告相关工具

| 工具 | 功能 |
|------|------|
| `notice.py` | **公告违禁词检查** - 检查公告内容是否包含违禁词，需要配合 BCZ-Notice-Examiner 库使用（现更名为ystkc.github.io） |
| `subscribe.py` | **公告订阅查询** - 命令行查询已订阅用户的公告等等更新 |
| `clash.py` | **公告同音替换** - 将公告进行同音常见字替换，绕过违禁词审查 |

### 5.4 数据分析工具

| 工具 | 功能 |
|------|------|
| `cheat.py` | 作弊分析 - 绘图显示昨日 500 词以上用户的作弊、爆破情况，数据来源于 automata 的 `notice_and_rank` |
| `cooper.py` | 铜板统计 - 绘制库中所有已打卡账号的铜板数柱状图 |
| `uv.py` | UV 指数分析 - 绘制用户打卡指数日趋势变化图表 |
| `fit.py` | 数据拟合 - 从 `fit.xlsx` 读取数据进行高斯拟合和指数拟合 |
| `xhcx.py` | **小号查询器** - 查询指定班级成员 IP 分布和打卡时间 |

### 5.5 活动工具

| 工具 | 功能 |
|------|------|
| `flag.py` | 立 flag - 为库中所有允许组队的账号参与活动立 flag |
| `team.py` | 组队工具 - 为库中的用户组队或立 flag |

### 5.6 辅助工具

| 工具 | 功能 |
|------|------|
| `magic_proxy.py` | **令牌登录代理** - 通过 mitmproxy 实现令牌注入，使客户端使用指定令牌登录 |
| `copy_log.py` | 日志复制 - 读取当日日志文件并复制到剪贴板 |
| `extract.py` | 数据导出 - 导出指定账号的铜板等信息 |

### 5.7 调试工具（可忽略）

| 工具 | 功能 |
|------|------|
| `escape.py` | 令牌转义 - 将剪贴板中的令牌进行 URL 转义 |
| `fun_cnt.py` | 函数统计 - 统计项目中指定字符串的出现次数 |
| `hex_transmute.py` | Fiddler 解析器 - 将 Fiddler 中拷贝的 cookie 转换为 Python 字典 |
| `total_length.py` | 公告长度计算 - 计算某天公告的总长度 |
| `bot.py` | QQ 机器人 - 自动回复公告相关消息【已废弃】 |

---

## 第六部分：注意事项

---

## 第七部分：参考 API（部分活动，使用频率较低，不提供自动化）

- 2024NCSVC_pk 报名：状态查询 - `https://pkonline1.baicizhan.com/api/contest/2024/tournament/status?code=mB5AG9fCzo`
- 2024NCSVC_pk 报名：报名 - `https://pkonline1.baicizhan.com/api/contest/2024/tournament/preApply?code=mB5AG9fCzo&type=2`
- 同桌申请 - `https://social.baicizhan.com/api/deskmate/invite_deskmate?uniqueId=xxx`
- 同桌通过 - `https://social.baicizhan.com/api/deskmate/recv_deskmate?uniqueId=xxx&source=0`

---

## 待办事项

- `member_class_storage` 类
- 更新 Notice-Examiner 的页面
- 学习单词时，改为从服务器获取学习记录（本地瞎选可能有点问题，而且新词书会 bug）
