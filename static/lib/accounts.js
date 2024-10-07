// 页面加载后，请求账号列表
let daka = 0, not_daka = 0;
String.prototype.replaceAll = function(s1, s2) {
  return this.replace(new RegExp(s1, "gm"), s2);
}
function refresh(btn){
  btn.textContent = `已打卡${daka}，未打卡${not_daka}`;
}
function reloadAll(){
  // 清空打卡计数
  daka = 0;
  not_daka = 0;
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
    showAccountList(data, init=1);
  })
 .catch(function(error) {
    console.error(error);
  });
}

function loadAccountList() {
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
      showAccountList(data, init=1);
    })
   .catch(function(error) {
      console.error(error);
    });
}
function replyAndACK(button, group_share_key, unique_id) {
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
    button.parentNode.parentNode.querySelector('#nickname').innerHTML = data.msg;
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
        table += `<tr style='${background}'>
          <td>${group.name}</td>
          <td>${group.rank}</td>
          <td>${group.introduction}</td>
          <td id='img_frame'>${group.notice}</td>
          <td id='nickname'>${group.group_nickname}</td>
          <td><button onclick="moreGroups(${unique_id})">增加班位</button></td>
          <td><button class='daka' onclick="daKa(this, ${unique_id})">打卡</button></td>
        </tr>`;
      }else{
        quit_button = '';
        background = '';
        if (group.leader == true){
          quit_button = `<td><button id='op1' onclick="changeNotice(this.parentNode, '${group.share_key}', ${unique_id}, '${group.group_id}')">改公告</button></td>`
          background = 'background-color: #00ffff88;';
        }
        else{
          quit_button = `<td><button id='op1'onclick="quitGroup('${group.name}', '${group.share_key}', ${unique_id})">退出</button></td>`
        }
        table += `
          <tr style='${background}'>
            <td>${group.name}</td>
            <td>${group.rank}</td>
            <td>${group.introduction}</td>
            <td id='notice' onclick='changeNotice(this, "${group.share_key}", ${unique_id})'>${group.notice}</td>
            <td id='nickname'>${group.group_nickname}</td>
            <td><button onclick="replyAndACK(this, '${group.share_key}', ${unique_id})">回复收到</button></td>
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
function changeNotice(element, group_share_key, unique_id, group_id=''){
  let op1_button = element.parentNode.querySelector('#op1');
  if (op1_button.textContent == "改公告" ) // 是班长，进入编辑公告模式
  {
    let notice_span = element.parentNode.querySelector('#notice');
    // 将notice_span改成输入框（保留当前公告）
    let original_content = notice_span.innerText;
    let original_html_content = notice_span.innerHTML;
    // 使textarea的宽度和高度与notice_span一致
    let width = notice_span.offsetWidth;
    let height = notice_span.offsetHeight;
    let input_span = `<textarea type="text" id="editor" style="width:${width}px;height:${height}px;">${original_content}</textarea>`;
    element.innerHTML = input_span;
    element.querySelector('#editor').focus();
    op1_button.textContent = "发送";
    // 设置ESC键退出编辑模式
    document.addEventListener('keydown', function(event){
      if (event.key == 'Escape'){
        notice_span.innerHTML = original_html_content;
        op1_button.textContent = "改公告";
      }
    });
  }
  else if (element.textContent != "发送" && op1_button.textContent == "发送")
    return;
  else if (element.textContent == "发送") // 是班长，发送公告
  {// 此处不使用op1.textContent是因为编辑公告时点击编辑器不应该触发
    content = element.parentNode.querySelector('#editor').value;
    //换回td
    let notice_span = element.parentNode.querySelector('#notice');
    
    // 查找content中所有`到空格之间的字符串，提取成列表
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
    op1_button.textContent = "今日已改公告";
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
      // sse
      let sse = new EventSource(`/api/change_notice_sse?group_share_key=${group_share_key}&unique_id=${unique_id}&group_id=${group_id}`);
      sse.onmessage = function(event) {
          notice_span.innerHTML = event.data;
          // console.log(event.data);
      };
    })
  .catch(function(error) {
      console.error(error);
      sse.close();
    });
  }
  if (op1_button.textContent == "退出" || op1_button.textContent == "发送") // 因为改公告点击后会立刻变为发送
  {
     // 显示昵称框
     fetch (`/api/get_nickname?unique_id=${unique_id}&group_share_key=${group_share_key}`)
     .then(response => response.json())
     .then(data => {
        data = data.data;
        // 先将my_reply写入#nickname中
        let my_reply = data.my_reply;
        if (my_reply != null){
          let nickname_span = element.parentNode.querySelector('#nickname');
          nickname_span.innerHTML = my_reply;
        }
        var old = element.parentNode.querySelector('#nickname_list');
        if (old) old.remove();
        // 在公告输入区下面加一个列表，点击昵称可以插入到公告中
        let nickname_list = document.createElement('ul');
        nickname_list.id = 'nickname_list';
        element.parentNode.querySelector('#notice').appendChild(nickname_list);
        // data是{uniqueId:{nickname:nickname, group_nickname:group_nickname, two_week_daka_dates:two_week_daka_dates[14]}}
        data = data.group_nickname;
        for (let unique_id in data){
          // console.log(data[unique_id]);
          // console.log(data[unique_id].two_week_daka_dates);
          let nickname_li = document.createElement('li');
          // 第一行显示昵称+(uniqueId)，第二行显示组内昵称，第三行显示两周打卡天数的前7位，第四行显示两周打卡天数的后7位
          if (op1_button.textContent == "发送")
            nickname_li.innerHTML = `<span onclick="insertNickname(this, '${unique_id}', '${data[unique_id].group_nickname}')">
${data[unique_id].nickname}(${unique_id})[${data[unique_id].completed_times}/${data[unique_id].duration_days}]:<br>
${data[unique_id].group_nickname}<br>
${data[unique_id].two_week_daka_dates.slice(0,7)}<br>
${data[unique_id].two_week_daka_dates.slice(7)}</span>`;
          else
            nickname_li.innerHTML = `<span>
${data[unique_id].nickname}(${unique_id})[${data[unique_id].completed_times}/${data[unique_id].duration_days}]:<br>
${data[unique_id].group_nickname}<br>
${data[unique_id].two_week_daka_dates.slice(0,7)}<br>
${data[unique_id].two_week_daka_dates.slice(7)}</span>`;
          nickname_list.appendChild(nickname_li);
        }
     })
     .catch(error => console.error(error));
  }
}
function insertNickname(element, unique_id, nickname){
  let editor = element.parentNode.parentNode.parentNode.querySelector('#editor');
  editor.value += `@${nickname}\`${unique_id} `;
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
function daKaAll(button){
  // 仅F12调用
  console.log("在180s内开始所有账号")
  document.querySelectorAll('.daka').forEach(function(button){
    // 随机延时0-180s
    random_secs = Math.floor(Math.random() * 180);
    setTimeout(function(){
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
function daKa(button, unique_id){
  // websocket链接
  
  let socket = io();
  socket.emit('daka', unique_id);
  socket.on('msg', function(data) {
    // console.log(data);
    msg = data;
    if (msg[0] == '$'){
      button.parentNode.parentNode.querySelector('#img_frame').innerHTML = msg;
    }
    else{
      button.parentNode.parentNode.querySelector('#nickname').innerHTML = msg;
    }
  });
  socket.on('error', function(error) {
    button.parentNode.parentNode.querySelector('#img_frame').innerHTML = error;
    socket.close();
  });
  
  // let socket = new WebSocket('ws://' + location.host + '/api/daka?unique_id=' + unique_id);
  // socket.onopen = function(event) {
  //   console.log("WebSocket已连接");
  // };
  // socket.onmessage = function(event) {
  //   console.log(event.data);
  //   msg = event.data;
  //   if (msg[0] == '$'){
  //     button.parentNode.parentNode.querySelector('#img_frame').innerHTML = msg;
  //   }
  //   else{
  //     button.parentNode.parentNode.querySelector('#nickname').innerHTML = msg;
  //   }
  // };
  // socket.onerror = function(event) {
  //   console.error(event);
  //   socket.close();
  // };

  // sse.onmessage = function(event) {
  //   if (event.data[0] == '$')
  //     button.parentNode.parentNode.querySelector('#img_frame').innerHTML = event.data;
  //   button.parentNode.parentNode.querySelector('#nickname').innerHTML = event.data;
  // };
  // sse.onerror = function(event) {
  //   console.error(event);
  //   sse.close();
  // };
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
function showAccountList(data, init=0) {
  var accountList = document.querySelector('.account-list');
  accountList.innerHTML = '';
  let str = '';
  data = data.data;
  data.forEach(function(account) {
    str += `<div id="group${account.unique_id}">
      <li class="account-item">${account.name}(${account.unique_id})
        <button class="delete-btn" onclick="deleteAccount(${account.unique_id})">删除</button>
        <button class="edit-btn" onclick="loadOwnGroups(${account.unique_id})">刷新</button>
        <button class="join-btn" onclick="changeToken('${account.access_token}', ${account.unique_id})">魔法账号</button>
      </li>
    </div>`;
    
  });
  str += `<div><button class="add-btn" onclick="addAccount()">新增</button></div>`;
  accountList.innerHTML = str;
  data.forEach(function(account) {
    if(init == 1){
      // 给予0-4s的随机延时
      setTimeout(function(){
        loadOwnGroups(account.unique_id);
      }, Math.floor(Math.random() * 5000));
    }
    else{
      loadOwnGroups(account.unique_id);
    }
  });
}
function changeToken(access_token, unique_id){
  // no-cors
  return fetch(`change_token`, {
    method: 'POST', // 根据需要选择请求方法
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      access_token: access_token,
      unique_id: unique_id
    })
  })
  .then(response => response.json())
  .then(data => {
    alert(data.msg);
  })
  .catch(error => console.error(error));
}

function addAccount() {
  var name = prompt("请输入账号名称:");
  if (name == null) return;
  var access_token = prompt("请输入access_token:");
  if (access_token == null) return;
  let unique_id = prompt("请输入unique_id:");
  if (unique_id == null) return;
  return fetch('/accounts/add', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: name,
      access_token: access_token,
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
    loadOwnGroups(unique_id);
  });
}

function deleteAccount(unique_id) {
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
  loadAccountList();
}