import httpx  
import asyncio  
import random  
import json
import time
  
def test_task(access_token: list, period_s: int) -> list:
    async def _task(name, token, start_delay_s):  
        """模拟异步任务"""  
        print(f"Task {name} is ready")  
        await asyncio.sleep(start_delay_s)
        print(f"Task {name} is running...")  
        async with httpx.AsyncClient(http2=True,timeout=10) as client:
            client.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Code/1.88.0 Chrome/120.0.6099.291 Electron/28.2.8 Safari/537.36'})
            response1 = await client.get('https://cn.bing.com/')
            await asyncio.sleep(random.randint(1500, 2000) / 1000)
            response2 = await client.get('https://www.baidu.com/')
            await asyncio.sleep(random.randint(1500, 2000) / 1000)
            response3 = await client.get('https://cn.bing.com/')
            await asyncio.sleep(random.randint(1500, 2000) / 1000)
            response4 = await client.get('https://www.baidu.com/')
            await asyncio.sleep(random.randint(1500, 2000) / 1000)
            response5 = await client.get('https://cn.bing.com/')
        return f"Result from {name}: {response1.status_code}, {response2.status_code}, {response3.status_code}, {response4.status_code}, {response5.status_code}" 
    
    async def run_tasks_and_collect_results(*tasks):  
        # 使用asyncio.gather来并发运行所有任务并等待它们完成  
        results = await asyncio.gather(*tasks)  
        return results  
    
    tasks = []
    for i in range(len(access_token)):
        # 任务开始前给予0-period_s秒的延迟，模拟网络延迟等因素
        task = _task(f"{i+1}.{access_token[i]['name']}", access_token[i]["token"], random.randint(0, period_s * 1000) / 1000)
        tasks.append(task)  
    return asyncio.run(run_tasks_and_collect_results(*tasks))

if __name__ == '__main__':
    with open("susan.json", "r", encoding="utf-8") as f:
        access_token = json.load(f)
        print(test_task([{"name": "susan", "token": access_token[0]}], 5))
    # 期望得到4个结果和2个tunnel