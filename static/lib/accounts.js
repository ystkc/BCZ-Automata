// 页面加载后，请求账号列表
let daka = 0, not_daka = 0;
function refresh(btn){
  btn.textContent = `已打卡${daka}，未打卡${not_daka}`;
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
          quit_button = `<td><button onclick="changeNotice(this, '${group.share_key}', ${unique_id})">改公告</button></td>`
          background = 'background-color: #00ffff88;';
        }
        else{
          quit_button = `<td><button onclick="quitGroup('${group.name}', '${group.share_key}', ${unique_id})">退出</button></td>`
        }
        table += `
          <tr style='${background}'>
            <td>${group.name}</td>
            <td>${group.rank}</td>
            <td>${group.introduction}</td>
            <td id='notice'>${group.notice}</td>
            <td id='nickname'>${group.group_nickname}</td>
            <td><button onclick="replyAndACK(this, '${group.share_key}', ${unique_id})">回复收到</button></td>
            ${quit_button}
          </tr>
        `;
      }
    });
    
  table += `
      <tr><td><button onclick="joinGroup('${unique_id}')">加入班级</button></td></tr>
      </tbody>
    </table>
  `;
  table_element = document.createElement('div');
  table_element.id = `table${unique_id}`;
  table_element.innerHTML = table;
  document.querySelector(`#group${unique_id}`).appendChild(table_element);
}
function changeNotice(element, group_share_key, unique_id){
  let notice_span = element.parentNode.parentNode.querySelector('#notice');
  var content = prompt("请输入新的公告内容:");
  if (content == null) return;
  // post_notice
  return fetch('/api/change_notice', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      group_share_key: group_share_key,
      unique_id: unique_id,
      content: content
    })
  })
 .then(function(response) {
    return response.json();
  })
 .then(function(data) {
    // sse
    let sse = new EventSource(`/api/change_notice_sse?group_share_key=${group_share_key}&unique_id=${unique_id}`);
    sse.onmessage = function(event) {
        notice_span.innerHTML = event.data;
    };
  })
 .catch(function(error) {
    console.error(error);
    sse.close();
  });
}
function daKaAll(button){
  // 仅F12调用
  console.log("在50s内开始所有账号")
  document.querySelectorAll('.daka').forEach(function(button){
    // 随机延时0-50s
    random_secs = Math.floor(Math.random() * 50);
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
  // 发送请求后，获得一个sse链接，展示在页面上
  let sse = new EventSource('/api/daka?unique_id=' + unique_id);
  sse.onmessage = function(event) {
    if (event.data[0] == '$')
      button.parentNode.parentNode.querySelector('#img_frame').innerHTML = event.data;
    button.parentNode.parentNode.querySelector('#nickname').innerHTML = event.data;
  };
  sse.onerror = function(event) {
    console.error(event);
    sse.close();
  };
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

function joinGroup(unique_id){
  var input = prompt("请输入班级shareKey(16位)或inviteCode(5-8位):");
  if (input == null) return;
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
    loadOwnGroups(unique_id);
  })
 .catch(function(error) {
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
      <li class="account-item">${account.name}(${account.unique_id}), ${account.access_token} - ${account.device_id}
        <button class="delete-btn" onclick="deleteAccount(${account.unique_id})">删除</button>
        <button class="edit-btn" onclick="loadOwnGroups(${account.unique_id})">刷新</button>
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
      }, Math.floor(Math.random() * 4000));
    }
    else{
      loadOwnGroups(account.unique_id);
    }
  });


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