import re
import quickjs
from poe import Client, request_with_retries,generate_payload,logger
import json
import hashlib, time


user_agent = "This will be ignored! See the README for info on how to set custom headers."
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": "\"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"112\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Linux\"",
    "Upgrade-Insecure-Requests": "1"
}
client_identifier = "chrome112"

class cc(Client):

    def __init__(self, token, formkey, proxy=None, headers=headers, device_id=None,
                 client_identifier=client_identifier):
        self.ws_connecting = False
        self.ws_connected = False
        self.ws_error = False
        self.connect_count = 0
        self.setup_count = 0

        self.formkey = formkey

        self.token = token
        self.device_id = device_id
        self.proxy = proxy
        self.client_identifier = client_identifier

        self.active_messages = {}
        self.message_queues = {}
        self.suggestion_callbacks = {}

        self.headers = {**headers, **{
            "Host": "poe.com",
            "Cache-Control": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        }}
        self.formkey_salt = None

        self.connect_ws()

    def extract_formkey(self, html,app_script=None):
        script_regex = r'<script>(.+?)</script>'
        script_text = """
      let QuickJS = undefined, process = undefined;
      let window = new Proxy({
        document: {a:1},
        navigator: {a:1}
      },{
        get(obj, prop) {
          return obj[prop] || true;
        },
        set(obj, prop, value) {
          obj[prop] = value;
          return true;
        }
      });
    """
        script_text += "".join(re.findall(script_regex, html))
        function_regex = r'(window\.[a-zA-Z0-9]{17})=function'
        function_text = re.search(function_regex, script_text).group(1)
        script_text += f"{function_text}();"

        salt = "Jb1hi3fg1MxZpzYfy"

        context = quickjs.Context()
        formkey = context.eval(script_text)
        print(formkey)
        formkey = self.formkey
        return formkey, salt

    def get_next_data(self, overwrite_vars=False):
        logger.info("Downloading next_data...")

        r = request_with_retries(self.session.get, self.home_url)
        json_regex = r'<script id="__NEXT_DATA__" type="application\/json">(.+?)</script>'
        json_text = re.search(json_regex, r.text).group(1)
        next_data = json.loads(json_text)

        if overwrite_vars:
            self.formkey, self.formkey_salt = self.extract_formkey(r.text)
            if "payload" in next_data["props"]["pageProps"]:
                self.viewer = next_data["props"]["pageProps"]["payload"]["viewer"]
            else:
                self.viewer = next_data["props"]["pageProps"]["data"]["viewer"]
            self.user_id = self.viewer["poeUser"]["id"]
            self.next_data = next_data

        return next_data

    def send_query(self, query_name, variables, attempts=20):
        for i in range(attempts):
            json_data = generate_payload(query_name, variables)
            payload = json.dumps(json_data, separators=(",", ":"))

            base_string = payload + self.gql_headers["poe-formkey"] + self.formkey_salt

            headers = {
                "content-type": "application/json",
                "poe-tag-id": hashlib.md5(base_string.encode()).hexdigest()
            }
            headers = {**self.gql_headers, **headers}

            if query_name == "recv":
                r = request_with_retries(self.session.post, self.gql_recv_url, data=payload, headers=headers)
                return None

            r = request_with_retries(self.session.post, self.gql_url, data=payload, headers=headers)
            data = r.json()
            if data["data"] == None:
                logger.warn(
                    f'{query_name} returned an error: {data["errors"][0]["message"]} | Retrying ({i + 1}/20) | Response: {data}')
                time.sleep(2)
                continue

            return r.json()

        raise RuntimeError(f'{query_name} failed too many times.')
