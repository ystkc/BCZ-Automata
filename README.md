# BCZ-Automata

 账号管理器（打卡、互动、加退班、公告阅读和修改）

## ⚠️ 免责申明

感谢您选择使用本小班数据管理器。在使用本程序之前, 请您**仔细阅读**并理解以下免责声明内容：

 - 本程序基于[GPLv3](https://www.gnu.org/licenses/agpl-3.0.html)开源，仅供个人学习、研究和其他非商业性质的合法用途, 任何因违反相关法律法规或侵犯他人权益所导致的法律责任, 由用户自行承担。
 - 用户在使用本程序时, 应遵守所在国家或地区的法律法规, 并对使用该程序产生的一切后果负全部责任。
 - 本程序对于用户使用过程中可能产生的各种风险（包括但不限于被数据来源公司的封禁、用户自身合规问题等）不承担任何责任。
 - 用户违反本声明或者滥用本程序进行非法活动的, 数据来源公司将有权追究您的法律责任。
 - 本程序作者对用户使用本程序产生的一切纠纷、损失或伤害不承担任何责任。
 - 一旦用户开始使用本程序, 则视为用户已充分理解并同意本免责声明的全部内容, 如果您无法接受上述条款, 请**立即停止**使用本程序。

## 安全警告
 - 本程序没有添加鉴权模块，请在内网使用或自行添加。

## 运行参数
 - **`--debug`使用调试模式运行，使用修改重载、只加载前三个账号，不使用gevent服务器，只使用flask自带服务器，并发数较少**
 - **`--static`不加载Schedule（忽略archiever_enable设置）**

## 备份警告
 - 请定期备份您的数据，重要的数据列表如下：
 config.json(如果有修改)
 user_cookie.json(建议保留原来的excel文件)
 config.database_path(默认值 ../BCZ-Notice-Examiner/bcz_notice.db 仅archiever_enable为true时生成)
 ./yzdd.db(硬编码 暂不支持更改 仅开启YZDD功能后生成)
 config.puzzle_path(默认值 ./puzzle.db 仅开启BCZ_NCSVC功能后生成)
 config.dict_patch_db_path(默认值 ./lookup_patch.db)
 config.stargazer_db(默认值 ./stargazer.db)

 - 生成的但不重要、无需备份的文件如下：
 ./lookup.db(由lookup.rar解压)
 ./learnt_words.db(硬编码 即将废除)
 ./storage(储存小号查询后的缓存)
 ./logs(储存日志、警告和错误、作弊追踪名单、订阅已读清单)
 ./tmp_bad_words.json(目前检查到的坏词)

 - groupmanager中重要的数据列表如下：
 data.db(储存群组信息、班长信息、用户数据、筛选历史、打卡历史等，建议所有表都保留1-2个星期内的数据)
 config.json(如果有修改)
 tidal_token.json和poster_token.json(一般和user_cookie.json同时生成，建议保留原来的excel文件)
 strategy.json(策略设置)
 monitor.json(自动化设置)


## 使用方法
1.获取自己账号的accesstoken，可运行lm.py或lp.py或访问/login，name可自定义方便自己看即可
2.访问/append，按指示完成账号信息excel表，然后按照提示全部复制黏贴提交到服务器。
3.启动app.py，浏览器访问127.0.0.1:8850，即可管理账号。
4.如果需要使用魔法令牌，请自行在移动端或移动端模拟器安装mitmproxy的CA证书并代理到8080端口；
5.如果需要配合fiddler使用魔法令牌，请安装fiddler的CA证书，并配置fiddler代理到本地8080端口+忽略服务器证书错误，且移动端或移动端模拟器代理到本地8888端口

## config.json配置说明
 - **`host` `port`** 服务器运行的端口，默认127.0.0.1:8850
 - **`database_path`** 公告和班级信息数据库路径（自动生成）默认../BCZ-Notice-Examiner/bcz_notice.db
 - **`dict_patch_db_path`** 词库补丁数据库路径（自动生成）默认./lookup_patch.db
 - **`puzzle_path`** BCZ_NCSVC题库数据库路径（自动生成）默认./puzzle.db
 - **`main_token`** 某有效账号的access_token，应当使用未加入任何小班的账号，否则昵称获取会不准确
 - **`sync_command`** 自动备份命令，每天早上执行一次，可以手动添加备份命令，或启动订阅公告start subscribe.py等方便管理的小工具。仅local为true时生效。
 - **`prevent_sleep_command`** 防止系统休眠命令，默认timeout，仅在win11下测试有效。仅local为true时生效。
 - **`allow_sleep_command`** 允许系统休眠命令，默认timeout reverse，仅在win11下测试有效。仅local为true时生效。
 - **`local`** 是否为本地运行，True时会晚上23:59自动运行关机命令，更改系统休眠设置，并在早上自动运行备份命令。
 - **`log_dir`** 日志目录，默认./logs/
 - **`check_notice_pace`** 公告坏词检查步长，单位为字符(中英文emoji都是1个字符)。
 - **`pk_blacklist`** 单词pk黑名单，如果对手分数>180，将会触发反挂机。（默认>188触发反挂机）
 - **`pk_whitelist`** 单词pk白名单，无论对手分数，都不会触发反挂机。
 - **`shutdown_command`** 关机命令，默认shutdown -s -t 120，仅在local为true时生效。
 - **`archiever_enable`** 是否启用排行榜班级信息备份功能（每天晚上23点半左右开始，本地模式下完成后自动关机）默认False。
 - **`class_list_2048`** 自定义班级列表，在archiever_enable为true时会一并备份。

## 独立工具清单
 - **`append.py`** 用于导入以及更新user_cookie.json文件，用法同启动后访问/append。
 - **`cheat.py`** 绘图显示昨日500词以上用户的作弊、爆破情况，来自目录下的"cheat_tracker.%YY-%MM-%DD.csv"文件，数据来源于automata的notice_and_rank
 - **`cooper.py`** 
 - **`copy_log.py`** 
 - **`dk.py`** 
 - **`escape.py`** 
 - **`extract.py`** 
 - **`fit.py`** 
 - **`flag.py`** 
 - **`hex_transmute.py`** 
 - **`lm.py`** 
 - **`lp.py`** 
 - **`magic_proxy.py`** 
 - **`notice.py`** 
 - **`pk_result_query.py`** 
 - **`read_thrift.py`** 
 - **`stargazer.py`** 
 - **`subscribe.py`** 
 - **`team.py`** 
 - **`total_length.py`** 
 - **`uv.py`** 
 - **`word_match.py`** 
 - **`xhcx.py`** 

## 待办事项
 - member_class_storage 类
 - 更新Notice-Examiner的页面
 - 学习单词时，改为从服务器获取学习记录（本地瞎选可能有点问题，而且新词书会bug）
 
## 部分活动的API，使用频率较低，不提供自动化

2024NCSVC_pk报名：状态查询：`https://pkonline1.baicizhan.com/api/contest/2024/tournament/status?code=mB5AG9fCzo`
2024NCSVC_pk报名：报名：`https://pkonline1.baicizhan.com/api/contest/2024/tournament/preApply?code=mB5AG9fCzo&type=2`
同桌申请：`https://social.baicizhan.com/api/deskmate/invite_deskmate?uniqueId=xxx`
同桌通过：`https://social.baicizhan.com/api/deskmate/recv_deskmate?uniqueId=xxx&source=0`
