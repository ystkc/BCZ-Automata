// 页面加载后，请求账号列表
let daka = 0, not_daka = 0, not_loaded = 0; // 总账号数=daka+not_daka，总班位数=总账号数*6
let focused_id = -1;
let groups_list = []; // 加入的班级列表，{name: 'xxx', count: 有多少个账号加入该班级, include_leader: true/false}
let notice_groups_count = 0, not_notice_groups_count = 0; // 加入的青铜班级（用于更公告）数量
let all_groups_count = 0; // 总现在开了的班位数量
let socket = null;
function connect_ws() {
  socket = new WebSocket(`ws://${location.host}/ws`);
  socket.onmessage = function(event) {
    // console.log(event.data); // 如果不知道是谁在打卡，可以查看控制台（说白了：懒）
    msg = event.data;
      msg_info = msg.split('#')
      unique_id = msg_info[0];
      msg_type = msg_info[1];
      meta_length = unique_id.length+msg_type.length
      content_type = msg[unique_id.length+msg_type.length];
      msg = msg.slice(meta_length+1);
      if (content_type == '$' || msg_type == 'error'){
        element = document.querySelector(`#img_frame${unique_id}`);
        if (element) {
          element.innerHTML = msg;
        }
      }
      else{
        element = document.querySelector(`#nickname${unique_id}`);
        if (element) {
          element.innerHTML = msg;
        }
      }
  };
}

String.prototype.replaceAll = function(s1, s2) {
  return this.replace(new RegExp(s1, "gm"), s2);
}
function refresh(btn){
  btn.innerHTML = `已打卡${daka}，未打卡${not_daka}，未加载${not_loaded}`;
  var group_str = '';
  groups_list.sort(function(a, b){
    return b.count - a.count;
  });
  groups_list.forEach(function(item){
    group_str += `${item.name}(${item.count})`;
    if (item.include_leader) {
      group_str += '含班长';
    }
    group_str += '<br>';
  });
  document.getElementById("info").innerHTML = `总班位${(daka + not_daka) * 6}，已开班位${all_groups_count}，加入青铜班级${notice_groups_count}，非青铜班级${not_notice_groups_count} <br> 加入的班级${group_str}`;
}
function reloadAll(){
  // 清空打卡计数
  daka = 0;
  not_daka = 0;
  not_loaded = 0;
  return fetch('/accounts/reload', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })
 .then(function(response) {
    return response.json();
  })
 .then(function(data) {
    showAccountList(data, init=1, list_only=true);
  })
 .catch(function(error) {
    console.error(error);
  });
}
function exportBlacklist(){
  return fetch('/blacklist', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
    }).then(function(response) {
      return response.json();
    })
   .then(function(data) {
      alert(data.msg);
   });
}
function updateNotice(){
  return fetch('/update_notice', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  }).then(function(response) {
    return response.json();
  })
 .then(function(data) {
    alert(data.msg);
  })
  .catch(function(error) {
    console.error(error);
  });
}

function loadAccountListAndData() {
  loadAccountList(false);
}

function loadAccountList(list_only=true) {
    return fetch('/accounts/list', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
   .then(function(response) {
      return response.json();
    })
   .then(function(data) {
      showAccountList(data, init=1, list_only=list_only);
    })
   .catch(function(error) {
      console.error(error);
    });
}
function replyAndACK(group_share_key, unique_id) {
  var content = prompt("请输入回复内容:");
  if (content == null) return;
  return fetch('/api/reply_and_ack', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      group_share_key: group_share_key,
      content: content,
      unique_id: unique_id
    })
  })
 .then(function(response) {
    return response.json();
  })
 .then(function(data) {
    document.querySelector(`#nickname${unique_id}${group_share_key}`).innerHTML = data.msg;
    // loadOwnGroups(unique_id);
  })
 .catch(function(error) {
    console.error(error);
    // loadOwnGroups(unique_id);
  });
}
function quitGroup(group_name, group_share_key, unique_id) {
  // 二次确认
  if (!confirm(`确认退出${group_name}吗？`)) return;
  return fetch('/api/quit_group', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      group_share_key: group_share_key,
      unique_id: unique_id
    })
  })
 .then(function(response) {
    return response.json();
  })
 .then(function(data) {
    loadOwnGroups(unique_id);
  })
 .catch(function(error) {
    console.error(error);
    loadOwnGroups(unique_id);
  });
}
function groupCounter(group_name, is_leader=false){
  group_name = group_name.split('<br>')[0];
  group_item = groups_list.find(item => item.name == group_name);
  if (group_item) {
    group_item.count += 1;
    if (is_leader) {
      group_item.include_leader = true;
    }
  } else {
    groups_list.push({name: group_name, count: 1, include_leader: is_leader});
  }
}
// 显示账号列表
function showOwnGroups(data, unique_id) {
  if (document.querySelector(`#table${unique_id}`)) document.querySelector(`#table${unique_id}`).remove();
  let table = `
    <table>
      <thead>
        <tr>
          <th>组名</th>
          <th>组类型</th>
          <th>组描述</th>
          <th>组公告</th>
          <th>班内昵称</th>
        </tr>
      </thead>
      <tbody>
  `;
  data = data.data;
  data.forEach(function(group) {
      if (group.share_key == ''){
        var background = '';
        if (group.rank[0] == '0'){
          background = 'background-color: #FFC0CB88;';
          not_daka += 1;
        }
        else if (group.rank[0] == '1'){
          background = 'background-color: #4CAF5088;';
          daka += 1;
        }
        all_groups_count += group.introduction;
        table += `<tr style='${background}'>
          <td>${group.name}</td>
          <td>${group.rank}</td>
          <td>加入上限${group.introduction}</td>
          <td id='img_frame${unique_id}'>${group.notice}</td>
          <td id='nickname${unique_id}'>${group.group_nickname}</td>
          <td><button onclick="moreGroups(${unique_id})">增加班位</button></td>
          <td><button class='daka' onclick="daKa(${unique_id})">打卡</button></td>
        </tr>`;
      }else{
        quit_button = '';
        background = '';
        
        if (group.leader == true){
          quit_button = `<td><button id='op1${unique_id}${group.share_key}' onclick="changeNotice('${group.share_key}', ${unique_id}, '${group.group_id}')">改公告</button><button id='op2${unique_id}${group.share_key}' onclick="quitGroup('${group.name}', '${group.share_key}', ${unique_id})">退出</button></td>`;
          background = 'background-color: #00ffff88;';
        }
        else{
          quit_button = `<td><button id='op1${unique_id}${group.share_key}' onclick="quitGroup('${group.name}', '${group.share_key}', ${unique_id})">退出</button></td>`
        }
        if (group.rank == 1)
          notice_groups_count += 1;
        else {
          not_notice_groups_count += 1;
          groupCounter(group.name, is_leader=group.leader);
        }
        table += `
          <tr style='${background}'>
            <td>${group.name}</td>
            <td>${group.rank}</td>
            <td>${group.introduction}</td>
            <td id='notice${unique_id}${group.share_key}' onclick='changeNotice("${group.share_key}", ${unique_id})'>${group.notice}</td>
            <td id='nickname${unique_id}${group.share_key}'>${group.group_nickname}</td>
            <td><button onclick="replyAndACK('${group.share_key}', ${unique_id})">回复收到</button></td>
            ${quit_button}
          </tr>
        `;
      }
    });
    
  table += `
      <tr><td><button class='join' onclick="joinGroup('${unique_id}')">加入班级</button></td></tr>
      </tbody>
    </table>
  `;
  table_element = document.createElement('div');
  table_element.id = `table${unique_id}`;
  table_element.innerHTML = table;
  document.querySelector(`#group${unique_id}`).appendChild(table_element);
}
function changeAvatar(unique_id){
  focused_id = unique_id;
  var dropArea = document.getElementById('dropzone');
  dropArea.style.display = 'flex';
  dropArea.innerHTML = `更换用户${unique_id}的头像<br>拖动文件到此处，或点击取消`;
  dropArea.scrollIntoView();
}
function changeNotice(group_share_key, unique_id, group_id=''){
  let op1_button = document.querySelector(`#op1${unique_id}${group_share_key}`);
  if (op1_button.textContent == "改公告" ) // 是班长，进入编辑公告模式
  {
    let notice_span = document.querySelector(`#notice${unique_id}${group_share_key}`);
    // 将notice_span改成输入框（保留当前公告）
    let original_content = notice_span.innerText;
    let original_html_content = notice_span.innerHTML;
    // 使textarea的宽度和高度与notice_span一致
    let width = notice_span.offsetWidth;
    let height = notice_span.offsetHeight;
    let input_span = `<textarea type="text" id="editor${unique_id}${group_share_key}" style="width:${width}px;height:${height}px;">${original_content}</textarea>`;
    notice_span.innerHTML = input_span;
    // notice_span.setAttribute("onclick", "");
    op1_button.textContent = "发送";
    // 设置ESC键退出编辑模式
    document.addEventListener('keydown', function(event){
      if (event.key == 'Escape'){
        notice_span.innerHTML = original_html_content;
        op1_button.textContent = "改公告";
      }
    });
    showNickNameList(group_share_key, unique_id);
  }
  else if (op1_button.textContent == "发送" && group_id != '') // 是班长，发送公告
  { // 区别：如果是点击编辑器，则group_id为空，不应该触发发送请求
    content = document.querySelector(`#editor${unique_id}${group_share_key}`).value;
    //换回td
    let notice_span = document.querySelector(`#notice${unique_id}${group_share_key}`);
    
    // 查找content中所有\x00之间的字符串并删掉
    
    content = content.replaceAll(/\\x00(.*?)\\x00/g, '');
    let nickname_list = []
    let nickname_regex = /`(\d+)/g; // 匹配`到空格之间的字符串
    let numbers = content.match(nickname_regex);
    if (numbers == null) numbers = [];
    // 将content中复合上述正则的字符串删掉
    content = content.replaceAll(nickname_regex, '');
    numbers = numbers.map(num => num.slice(1));
    console.log(numbers);
    console.log(content);
    length = content.length;
    if (length > 1000) {
      prompt(`公告内容长度${length} > 1000`);
      return;
    }
    notice_span.innerHTML = content;
    original_html_content = content;
    op1_button.textContent = "请稍候";
    // 发送请求
    return fetch('/api/change_notice', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        group_share_key: group_share_key,
        unique_id: unique_id,
        mentioned_ids: numbers,
        content: content
      })
    })
  .then(function(response) {
      return response.json();
    })
  .then(function(data) {
      op1_button.textContent = "发送中...";
      // sse
      let sse = new EventSource(`/api/change_notice_sse?group_share_key=${group_share_key}&unique_id=${unique_id}&group_id=${group_id}`);
      sse.onmessage = function(event) {
          if (event.data == "close") {
            sse.close();
            op1_button.textContent = "改公告";
          } else {
            notice_span.innerHTML = event.data;
          }
      };
    })
  .catch(function(error) {
      op1_button.textContent = "改公告";
      console.log(error);
      
      alert(error.msg);

      sse.close();
    });
  }
  else if (op1_button.textContent == "退出") // 不是班长，仅显示昵称列表
  {
     showNickNameList(group_share_key, unique_id);
  }
}
function showNickNameList(group_share_key, unique_id){
  let op1_button = document.querySelector(`#op1${unique_id}${group_share_key}`);
  // 显示昵称框
  fetch (`/api/get_nickname?unique_id=${unique_id}&group_share_key=${group_share_key}`)
  .then(response => response.json())
  .then(data => {
     data = data.data;
     // 先将my_reply写入#nickname中
     let my_reply = data.my_reply;
     if (my_reply != null){
       let nickname_span = document.querySelector(`#nickname${unique_id}${group_share_key}`);
       nickname_span.innerHTML = my_reply;
     }
     var old = document.querySelector(`#nickname_list${unique_id}${group_share_key}`);
     if (old) old.remove();
     // 在公告输入区下面加一个列表，点击昵称可以插入到公告中
     let nickname_list = document.createElement('ul');
     nickname_list.id = `nickname_list${unique_id}${group_share_key}`;
     document.querySelector(`#notice${unique_id}${group_share_key}`).appendChild(nickname_list);
     // data是{uniqueId:{nickname:nickname, group_nickname:group_nickname, two_week_daka_dates:two_week_daka_dates[14]}}
     data = data.group_nickname;
     // 查找公告和昵称中是否含有“下次互动字母”（如果都有，以昵称为准）
     var next_letter = '';
     var content = document.querySelector(`#notice${unique_id}${group_share_key}`).innerHTML;
     var index = content.indexOf('下次互动字母');
     if (index != -1){
       next_letter = content.slice(index+6, index+7);
     }
     if (my_reply.startsWith('下次互动字母')) {
       next_letter = my_reply.slice(6, 7);
     }
     var is_edit_notice_mode = op1_button.textContent == "发送";
     // 将以next_letter开头的昵称优先显示在列表前面
     function get_square_brackets(daka_info_list){ // -2、-1：透明方块，0：灰色方块，1：绿色方块
      var tmp_str = '<div class="squares">';
      daka_info_list.forEach(function(daka_info){
        if (daka_info == 0)
          tmp_str += '<div class="gray square"></div>';
        else if (daka_info == 1)
          tmp_str += '<div class="green square"></div>';
        else
          tmp_str += '<div class="transparent square"></div>';
      });
      return tmp_str + '</div>';
     }
     function get_nickname_str(unique_id, user_unique_id, group_share_key, user_data, is_edit_notice_mode) {
      var tmp_str = '';
      // 第一行显示昵称+(uniqueId)，第二行显示组内昵称，第三行显示两周打卡天数的前7位，第四行显示两周打卡天数的后7位
      if (is_edit_notice_mode) // 编辑公告时，点击昵称插入到公告中at
        tmp_str = `<span onclick="insertNickname('${user_data.nickname}', '${unique_id}', '${user_unique_id}', '${group_share_key}', '${user_data.group_nickname}')">`;
      else
        tmp_str = `<span>`;
      tmp_str += `${user_data.nickname}(${user_unique_id})[${user_data.completed_times}/${user_data.duration_days}]:<br>`;
      tmp_str += `${user_data.group_nickname}<br>`;
      tmp_str += `${get_square_brackets(user_data.two_week_daka_dates.slice(0, 7))}<br>`;
      tmp_str += `${get_square_brackets(user_data.two_week_daka_dates.slice(7))}</span>`;
      return tmp_str;
     }
     for (let user_unique_id in data){
      if (data[user_unique_id].group_nickname[0] == next_letter){
        nickname_list.innerHTML += get_nickname_str(unique_id, user_unique_id, group_share_key, data[user_unique_id], is_edit_notice_mode);
      }
     }
     for (let user_unique_id in data){
      if (data[user_unique_id].group_nickname[0] != next_letter){
       nickname_list.innerHTML += get_nickname_str(unique_id, user_unique_id, group_share_key, data[user_unique_id], is_edit_notice_mode);
      }
    }
  })
  .catch(error => console.error(error));
}
function insertNickname(user_nickname, monitor_unique_id, user_unique_id, group_share_key, group_nickname){
  let editor = document.querySelector(`#editor${monitor_unique_id}${group_share_key}`);
  editor.value += `\n@${group_nickname}\\x00${user_nickname}\\x00\`${user_unique_id} `;
}
function joinAll(){
  let share_key = prompt("请输入shareKey(16位)或inviteCode(5-8位):");
  if (share_key == null) return;
  console.log("在10s内开始所有账号")

  document.querySelectorAll('.join').forEach(function(button){
    // 随机延时0-10s
    random_secs = Math.floor(Math.random() * 10);
    setTimeout(function(){
      on_click_attr = button.getAttribute('onclick'); // joinGroup(unique_id)
      if (on_click_attr.indexOf('joinGroup') != -1){
        unique_id = on_click_attr.split('\'')[1]
        
        joinGroup(unique_id, share_key);
      }
    }, random_secs * 1000);
    // 将按钮的文字从10倒数到0
    let count = random_secs;
    let interval = setInterval(function(){
      button.innerHTML = count;
      count--;
      if (count < 0) {
        clearInterval(interval);
        button.innerHTML = "加入班级";
      }
    }, 1000);
  });

}
function buKa(){ // 给未打卡的账号打卡
  buttons = document.querySelectorAll('.daka')
  buttons_to_click = []
  buttons.forEach((button) => {
    status_str = button.parentNode.parentNode.innerHTML;
    if (status_str.indexOf('0未打卡') != -1){
      buttons_to_click.push(button);
    }
  });
  if (!confirm(`在${buttons_to_click.length*5}s内开始 未打卡 账号`)) return;
  buttons_to_click.forEach((button) => {
    // 随机延时0-180s
    random_secs = Math.floor(Math.random() * buttons_to_click.length * 5);
    setTimeout(() => {
      button.click();
    }, random_secs * 1000);
    // 将按钮的文字从50倒数到0
    let count = random_secs;
    let interval = setInterval(function(){
      button.innerHTML = count;
      count--;
      if (count < 0) {
        clearInterval(interval);
        button.innerHTML = "打卡";
      }
    }, 1000);
  });

}
function daKa(unique_id){
  // websocket链接
  document.querySelector(`#img_frame${unique_id}`).innerHTML = '';
  document.querySelector(`#nickname${unique_id}`).innerHTML = '';
  if (socket.readyState != 1) {
    document.querySelector(`#nickname${unique_id}`).innerHTML = '连接中...';
    connect_ws();
    let interval = setInterval(function(){
      if (socket.readyState == 1) {
        socket.send(`daka: ${unique_id}`);
        clearInterval(interval);
      }
    }, 1000);
  } else {
    socket.send(`daka: ${unique_id}`);
  }
}

function moreGroups(unique_id){
  if (!confirm("确认增加班位吗？")) return;
  return fetch('/api/more_groups', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      unique_id: unique_id
    })
  })
 .then(function(response) {
    return response.json();
  })
 .then(function(data) {
    loadOwnGroups(unique_id);
  })
 .catch(function(error) {
    console.error(error);
    loadOwnGroups(unique_id);
  });
}

function joinGroup(unique_id, group_share_key=null){
  let input = group_share_key;
  if (input == null){
    input = prompt("请输入班级shareKey(16位)或inviteCode(5-8位):");
    if (input == null) return;
  }
  let share_key = "";
  let invite_code = "";
  if (input.length == 16) share_key = input;
  else invite_code = input;
  return fetch('/api/join_group', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      unique_id: unique_id,
      share_key: share_key,
      invite_code: invite_code
    })
  })
 .then(function(response) {
    return response.json();
  })
 .then(function(data) {
    alert(data.msg);
    loadOwnGroups(unique_id);
  })
 .catch(function(error) {
    alert(error.msg);
    console.error(error);
    loadOwnGroups(unique_id);
  });
}

function loadOwnGroups(unique_id) {

    fetch('/own_groups?unique_id=' + unique_id, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      } 
    })
    .then(function(response) {
      return response.json();
    })
   .then(function(data) {
      showOwnGroups(data, unique_id);
    })
   .catch(function(error) {
      console.error(error);
    });
}
function showAccountList(data, init=0, list_only=false) {
  var accountList = document.querySelector('.account-list');
  accountList.innerHTML = '';
  let str = '';
  data = data.data;
  data.forEach(function(account) {
    var refresh_btn_text = '刷新';
    if (account.can_daka == 0) {
      refresh_btn_text = '点此加载';
      not_loaded += 1;
    }
    str += `<div id="group${account.unique_id}">
      <li class="account-item">${account.name}(${account.unique_id})
        <button class="delete-btn" onclick="deleteAccount(${account.unique_id})">删除</button>
        <button class="edit-btn" onclick="loadOwnGroups(${account.unique_id})">${refresh_btn_text}</button>
        <button class="join-btn" onclick="changeToken(${account.unique_id})">魔法账号</button>
      </li>
    </div>`;
    
  });
  str += `<div><button class="add-btn" onclick="addAccount()">新增</button></div>`;
  accountList.innerHTML = str;
  data_length = data.length;
  data.forEach(function(account) {
    if(account.can_daka == 1){
      if(init == 1){
        // 给予0-6s的随机延时
        if (!list_only) {
          setTimeout(function(){
            loadOwnGroups(account.unique_id);
          }, Math.floor(Math.random() * data_length * 100));
        }
      }
      else{
        loadOwnGroups(account.unique_id);
      }
    }
  });
}
function changeToken(unique_id){
  // no-cors
  return fetch(`change_token`, {
    method: 'POST', // 根据需要选择请求方法
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      unique_id: unique_id
    })
  })
  .then(response => response.json())
  .then(data => {
    alert(data.msg);
  })
  .catch(error => console.error(error));
}

function redirectToGroups() {
  // 在新标签页打开/groups
  window.open('/groups');
}
function redirectToNotices() {
  // 在新标签页打开/notice
  window.open('/notice');
}
function addAccount() {
  // 重定向到/append
  window.location.href = '/append';
}

function deleteAccount(unique_id) {
  if (!confirm("确认删除吗？此操作不可撤销")) return;
  document.querySelector(`#group${unique_id}`).innerHTML = `删除中...${unique_id}`;
  return fetch('/accounts/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      unique_id: unique_id
    })
  })
 .then(function(response) {
    return response.json();
  })
 .then(function(data) {
    document.querySelector(`#group${unique_id}`).innerHTML = `已删除${unique_id}`;
  })
 .catch(function(error) {
    console.error(error);
  });
}


// 页面加载完成后，调用 loadAccountList 函数
window.onload = function() {
  var dropArea = document.getElementById('dropzone');
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false)
  });

  function preventDefaults(e) {
      e.preventDefault()
      e.stopPropagation()
  }

  ['dragenter', 'dragover'].forEach(eventName => {
      dropArea.classList.add('highlight')
  });

  ['dragleave', 'drop'].forEach(eventName => {
      dropArea.classList.remove('highlight')
  });
  
  dropArea.addEventListener('drop', handleDrop, false)
  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    // 判断是否是一个图片
    if (e.dataTransfer.files.length !== 1 || !e.dataTransfer.files[0].type.startsWith('image')) {
      alert('请拖入一个图片文件');
      return;
    }
    // 发送文件数据到/api/change_avatar?unique_id=${focused_id}
    let file = e.dataTransfer.files[0];
    let formData = new FormData();
    formData.append('img_data', file);

    fetch('/api/change_avatar?unique_id=' + focused_id, {
      method: 'POST',
      body: formData
    })
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {
      alert(data.msg);
      document.getElementById('dropzone').style.display = 'none';
      loadOwnGroups(focused_id);
    })
    .catch(function(error) {
      console.error(error);
    });
  }

  connect_ws();
  loadAccountList();
}