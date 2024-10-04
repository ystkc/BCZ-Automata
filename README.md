# BCZ-Automata



## ⚠️ 免责申明

感谢您选择使用本小班数据管理器。在使用本程序之前, 请您**仔细阅读**并理解以下免责声明内容：

 - 本程序基于[GPLv3](https://www.gnu.org/licenses/agpl-3.0.html)开源，仅供个人学习、研究和其他非商业性质的合法用途, 任何因违反相关法律法规或侵犯他人权益所导致的法律责任, 由用户自行承担。
 - 用户在使用本程序时, 应遵守所在国家或地区的法律法规, 并对使用该程序产生的一切后果负全部责任。
 - 本程序对于用户使用过程中可能产生的各种风险（包括但不限于被数据来源公司的封禁、用户自身合规问题等）不承担任何责任。
 - 用户违反本声明或者滥用本程序进行非法活动的, 数据来源公司将有权追究您的法律责任。
 - 本程序作者对用户使用本程序产生的一切纠纷、损失或伤害不承担任何责任。
 - 一旦用户开始使用本程序, 则视为用户已充分理解并同意本免责声明的全部内容, 如果您无法接受上述条款, 请**立即停止**使用本程序。

## 运行参数
 - **`--debug`使用调试模式运行，使用修改重载、只加载前三个账号，不使用gevent服务器，只使用flask自带服务器，并发数较少**
## 配置说明
 - **`host` `port`(config.json)服务器运行的端口**
 - **`database_path`(config.json)未使用字段**
 - **`dict_db_path`(config.py)词典结构数据库路径（需要提供）**
 - **`db_path`(thrift_utils.py)用户已学单词数据库路径（自动生成）**
 - **`puzzle.db`(thrift_utils.py)一站到底题库数据库路径（自动生成）**
 - **`user_cookie.json`储存用户凭证的文件，格式如下，其中有中文的3个字段需要自行填写
 ```
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
 ```
 

## 部分活动的API，使用频率较低，不提供自动化

2024NCSVC_pk报名：状态查询：`https://pkonline1.baicizhan.com/api/contest/2024/tournament/status?code=mB5AG9fCzo`
2024NCSVC_pk报名：报名：`https://pkonline1.baicizhan.com/api/contest/2024/tournament/preApply?code=mB5AG9fCzo&type=2`
同桌申请：`https://social.baicizhan.com/api/deskmate/invite_deskmate?uniqueId=xxx`
同桌通过：`https://social.baicizhan.com/api/deskmate/recv_deskmate?uniqueId=xxx&source=0`
