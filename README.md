# BCZ-Automata



## ⚠️ 免责申明

感谢您选择使用本小班数据管理器。在使用本程序之前, 请您**仔细阅读**并理解以下免责声明内容：

 - 本程序基于[GPLv3](https://www.gnu.org/licenses/agpl-3.0.html)开源，仅供个人学习、研究和其他非商业性质的合法用途, 任何因违反相关法律法规或侵犯他人权益所导致的法律责任, 由用户自行承担。
 - 用户在使用本程序时, 应遵守所在国家或地区的法律法规, 并对使用该程序产生的一切后果负全部责任。
 - 本程序对于用户使用过程中可能产生的各种风险（包括但不限于被数据来源公司的封禁、用户自身合规问题等）不承担任何责任。
 - 用户违反本声明或者滥用本程序进行非法活动的, 数据来源公司将有权追究您的法律责任。
 - 本程序作者对用户使用本程序产生的一切纠纷、损失或伤害不承担任何责任。
 - 一旦用户开始使用本程序, 则视为用户已充分理解并同意本免责声明的全部内容, 如果您无法接受上述条款, 请**立即停止**使用本程序。

## 网络安全警告
 - 本程序设计为在内网下使用。由于access_token明文传输储存，如果要公开使用（不推荐），请自行添加鉴权并修改access_token的储存方式。
## 运行参数
 - **`--debug`使用调试模式运行，使用修改重载、只加载前三个账号，不使用gevent服务器，只使用flask自带服务器，并发数较少**

## 使用方法
1.获取自己账号的accesstoken、uniqueid（就是bczid），name可自定义方便自己看
2.按如下格式填写user_cookie.json 其中有中文的3个字段分别是name、bczid和accesstoken
```
[
    {
        "config": {
            "book_id": 410,
            "name": "str管理界面显示名称",
            "unique_id": int用户bczId,
            "adv_id": 166102,
            "timezone": "Asia/Shanghai",
            "device_name_ext": "DCO-AL00-HUAWEI",
            "app_channel": "Rongyao"
        },
        "cookie": {
            "access_token": "str用户凭证",
            "tfstk": "",
            "app_name": "7060100",
            "device_name": "android%2FDCO-AL00-HUAWEI",
            "client_time": "",
            "device_id": "",
            "serial": "",
            "channel": "qq",
            "device_version": "12",
            "version": "12",
            "Pay-Support-H5": "alipay_mob_client:weixin_app:qq_app",
            "bcz_dmid": "2a16dfbb"
        }
    },
]
 ```
3.启动app.py，浏览器访问127.0.0.1：8850，一般操作到此即可
4.如果需要使用魔法令牌，请自行在移动端或移动端模拟器安装mitmproxy的CA证书并代理到8080端口；
5.如果需要配合fiddler使用魔法令牌，请安装fiddler的CA证书，并配置fiddler代理到本地8080端口+忽略服务器证书错误，且移动端或移动端模拟器代理到本地8888端口

## 配置说明
 - **`host` `port`(config.json)服务器运行的端口**
 - **`database_path`(config.json)未使用字段**
 - **`dict_db_path`(config.py)词典结构数据库路径（需要提供）**
 - **`db_path`(thrift_utils.py)用户已学单词数据库路径（自动生成）**
 - **`puzzle.db`(thrift_utils.py)一站到底题库数据库路径（自动生成）**
 - **`user_cookie.json`储存用户凭证的文件
 
 

## 部分活动的API，使用频率较低，不提供自动化

2024NCSVC_pk报名：状态查询：`https://pkonline1.baicizhan.com/api/contest/2024/tournament/status?code=mB5AG9fCzo`
2024NCSVC_pk报名：报名：`https://pkonline1.baicizhan.com/api/contest/2024/tournament/preApply?code=mB5AG9fCzo&type=2`
同桌申请：`https://social.baicizhan.com/api/deskmate/invite_deskmate?uniqueId=xxx`
同桌通过：`https://social.baicizhan.com/api/deskmate/recv_deskmate?uniqueId=xxx&source=0`

## 待办备忘录
- [] 弹窗提示新公告
- [] 每天自动检测嫌疑词汇机
- [] debug:单词pk获取对方的bczId功能

## 更新记录
v18 2024.10.25
整理完善README.md的`更新记录`，增加单词pk`获取对方bczId`功能（不是API，是玄学行为）
v17 2024.10.23 
调整顺序以获得`任务中心`的铜板奖励。增加`每日一句精讲`的功能。
v16 2024.10.21
增加`定时打卡机`，毕竟是自用，就硬编码4:40了。问题蛮多调了3天还没成，不愧是麦花。
v15 2024.10.19
进一步完善了BCZ-Notice-Examiner，用上了之前的公告获取机，每天获取一个段位，增加`notice_parser.py`.
（我想，这个py公开出去可能会让官方不很乐意，就先放这吧）
v14
增加了`单词pk`，我们也有调速挂了，平时应放尽放，大概1400能上星就好。到时候加个黑名单狠狠干干那些1550+的狗狗
v13
整理程序结构，特别是打卡机，进行了一系列解耦操作，拆出学习+任务中心+一起背、商城、单词大赛pk、同桌pk和其他
v12
增加了`同桌双人战`功能（吐槽：官方做的UI太令人难受啦，延迟巨高，性能又差。还不快去学学多邻国！）
增加`魔法杖`功能，从此手动功能都不用了，一台模拟器+mitm+fiddler就解决了。
(fiddler方便储存回测，mitm方便实时修改，可以让fiddler当第一级代理，mitm当第二级)
v11
添加`班长修改公告`、`看班内改名和成员数据`、`自动查违禁`功能，管班方便多了。
v10
添加`公告回复+收到`功能，再也不用到处跑看公告了。
v9
为了方便小号管理，添加`加退班`功能。这个功能后来也移植到groupmanager成为潮汐令牌功能。
v8
添加`单词大赛自动机`。正赛当然不水了，只是平时水铜板用。
增加第一个版本的`README.md`
增加若干手动方法，例如`单词大赛报名`，`组队`，这些频率太低，要用的时候手动抓包效率更高
v7
从BCZ-wordscheck（后更名为BCZ-Notice-Examiner）中拆出来的`公告和排名获取功能`（因为账号数据都在这，也方便每日自动化）
v6
由于groupmanager的一些问题，将getHeades重新封装`get_headers.py`用于复用，修复了双引号、逗号的问题。（Cookie问题。百词斩有些服务器是认不得逗号的，全部用分号才认得出来。而客户端有时也是用逗号的。emmm。）大部分headers的cookie都有双引号。一些DESKMATE_VERSARY字段不是必然的，就暂时没处理。
v5
由于账号的增加，将SSE改成了Websocket。SSE一个浏览器同时支持6个，也太少了。
v4
添加了日常学习拼写分享奖励领取流程，每日可领100左右铜板。赶上组队、单词大赛可以到150-200。
v3
考虑到前端添加删除没啥用，删掉了。添加打卡功能。因为是自己用的，就 **`明文传输access_token`**，而且没有鉴权模块，这是不安全的，仅限内网使用，否则会带来不可预料的后果。如果以后有人需要使用需要注意。
v2
添加了账号管理系统，可以在前端显示简单的账号信息表格（这！没错就是麦花的UI水平），第一批按钮：`刷新`、`添加`、`删除`
添加了`hex_transmute.py`fiddler头转换器、`read_thrift.py`和`print_thrift_obj`，用于thrift接口debug的实用小工具。AI在小工具编写上得心应手。
v1
想要整一个能够自动打卡且领取铜板奖励的小程序，不过这个性质决定了不能公开发布啦。引入了似然的BCZ-Automata进行修改。解析了BCZapp的thrift接口。