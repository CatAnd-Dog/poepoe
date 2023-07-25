import poebiubiubiu
from flask import Flask, request, jsonify, Response, make_response, stream_with_context
import random
from flask_cors import CORS
import json
import time
import config



app = Flask(__name__)
CORS(app)

# 全局变量
client_all = {}
poe_ck=config.poe_ck

poe_bot=config.poe_bot
poe_apikey=config.poe_apikey    # poe验证


# 初始化读取ck,连接poe
def get_client():
    for i in range(len(poe_ck)):
        try:
            client = poebiubiubiu.cc(poe_ck[i][0],poe_ck[i][1])
            client_all[i] = client
        except:
            pass

get_client()




# 如果有失效的，则更新poe连接
def update_client(i):
    global client_all
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            client_all[i] = poebiubiubiu.cc(poe_ck[i][0],poe_ck[i][1])
            return  # 如果连接成功，立即返回，不执行下面的代码
        except Exception as e:
            print(f"Attempt {attempt + 1} to connect failed: {e}")
            if attempt < max_attempts - 1:  # 如果这不是最后一次尝试，那么等待一会儿再试
                time.sleep(2)
            else:  # 如果这是最后一次尝试，那么删除失效的连接
                del client_all[i]
                print(f"Failed to connect after {max_attempts} attempts, connection {i} removed.")


# 构造回复
response_content = {
    "choices": [
        {
            "delta": {
                "content": "请关注公众号：oneperfect"
            }
        }
    ]
}


# 从请求头中提取token
def extract_token_from_headers():
    token = None
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # 去掉 "Bearer " 前缀
    return token




@app.route('/v1/chat/completions', methods=['POST'])
def send_message():
    data = request.json
    model_name = data["model"]
    message = data["messages"]

    # 获取token
    key = extract_token_from_headers().strip()

    # 调用poe  4.0
    if model_name in poe_bot and key==poe_apikey:
        ck, client = random.choice(list(client_all.items()))
        model = poe_bot[model_name]

        def generate():
            try:
                for chunk in client.send_message(model, str(message), with_chat_break=True, async_recv=False):
                    response_content["choices"][0]["delta"]["content"] = chunk["text_new"]
                    yield f'data: {json.dumps(response_content)}\n\n'

            except:
                update_client(ck)
                response_content["choices"][0]["delta"]["content"] = "请联系站长或重试"
                yield f'data: {json.dumps(response_content)}\n\n'
        yield 'data: {"choices": [{"delta": {"content": "[DONE]"}}]}\n\n'
        response = Response(stream_with_context(generate()), content_type='text/event-stream')
        return response

    else:
        return str(len(client_all))



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=47124)

