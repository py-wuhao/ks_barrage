import random
import time
import _thread as thread

import requests
import websocket
from websocket import WebSocketApp

from barrage import MessageDecode

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36',
    'Content-Type': 'application/json;charset=UTF-8'
}

wss_url = 'wss://live-ws-pg-group3.kuaishou.com/websocket'


class Client(WebSocketApp):
    def __init__(self, url, stream_id, token):
        super().__init__(url,
                         on_open=self.on_open,
                         on_message=self.on_message,
                         on_error=self.on_error,
                         on_close=self.on_close,
                         )
        self.stream_id = stream_id
        self.token = token

    @staticmethod
    def get_page_id():
        charset = "bjectSymhasOwnProp-0123456789ABCDEFGHIJKLMNQRTUVWXYZ_dfgiklquvxz"
        page_id = ''
        for _ in range(0, 16):
            page_id += random.choice(charset)
        page_id += "_"
        page_id += str(int(time.time() * 1000))
        return page_id

    def on_message(self, message):
        data = [m for m in message]
        message = MessageDecode(data)
        if message.decode():
            message.feed_decode()
            if message.message.get('gift'):
                print('收到礼物：')
                print(message.message.get('gift'))
            elif message.message.get('user'):
                print('收到弹幕：')
                print(message.message.get('user'))

    def on_error(self, error):
        print(error)

    def on_close(self):
        print("### closed ###")

    def on_open(self):
        part1 = [0x08, 0xC8, 0x01, 0x1A, 0xC8, 0x01, 0x0A, 0x98, 0x01]  # 可能与版本有关
        part2 = [ord(c) for c in self.token]
        part3 = [0x12, 0x0B]
        part4 = [ord(c) for c in self.stream_id]
        part5 = [0x3A, 0x1E]
        page_id = self.get_page_id()
        part6 = [ord(c) for c in page_id]

        d = part1 + part2 + part3 + part4 + part5 + part6
        self.send(d, websocket.ABNF.OPCODE_BINARY)

        def send_heart_beat(ws):
            while True:
                time.sleep(20)
                # 发送心跳-当前时间戳-毫秒
                head = [0x08, 0x01, 0x1A, 0x07, 0x08]
                timestamp = int(time.time() * 1000)
                time_arr = MessageDecode.hex_(timestamp)
                heartbeat = head + time_arr
                ws.send(heartbeat, websocket.ABNF.OPCODE_BINARY)

        thread.start_new_thread(send_heart_beat, (self,))

    def start(self):
        websocket.enableTrace(False)
        self.run_forever(skip_utf8_validation=True)


class Spider:
    def __init__(self, kwai_id, client):
        self.kwai_id = kwai_id
        self.client = client
        self.stream_id = None
        self.token = None

    def get_stream_id(self):
        body = "{\"operationName\":\"LiveDetail\",\"variables\":{\"principalId\":\"%s\"\
                },\"query\":\"query LiveDetail($principalId: String) {\\n  liveDetail(principalId: $principalId) {\\n\
                liveStream\\n   feedInfo {\\n      pullCycleMillis\\n      __typename\\n    }\\n    watchingInfo {\\n\
                likeCount\\n       watchingCount\\n      __typename\\n    }\\n    noticeList {\\n      feed\\n      options\\n\
                __typename\\n    }\\n    fastComments\\n    commentColors\\n    moreRecommendList {\\n      user{\\n\
                id\\n        profile\\n        name\\n       __typename\\n      }\\n      watchingCount\\n\
                src\\n      title\\n      gameId\\n      gameName\\n      categoryId\\n      liveStreamId\\n    playUrls {\\n\
                quality\\n        url\\n        __typename\\n      }\\n      quality\\n      gameInfo {\\n category\\n\
                name\\n        pubgSurvival\\n        type\\n        kingHero\\n         __typename\\n}\\n\
                redPack\\n      liveGuess\\n      expTag\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\"\
                }\r\n" % self.kwai_id

        url = 'https://live.kuaishou.com/graphql'
        resp = requests.post(url, headers=headers, data=body)

        if resp.status_code != 200:
            return
        data = resp.json()
        stream_id = data.get('data', {}).get('webLiveDetail', {}).get('liveStream', {}).get('liveStreamId')
        return stream_id

    def get_token(self):
        body = "{\"operationName\":\"WebSocketInfoQuery\"," \
               "\"variables\":{\"liveStreamId\":\"%s\"}," \
               "\"query\":\"query WebSocketInfoQuery($liveStreamId: String) " \
               "{\\n  webSocketInfo(liveStreamId: $liveStreamId) " \
               "{\\n    token\\n    webSocketUrls\\n    __typename\\n  }\\n}\\n\"}" % self.stream_id
        print(body)
        url = 'https://live.kuaishou.com/m_graphql '
        resp = requests.post(url, headers=headers, data=body)
        if resp.status_code != 200:
            return
        data = resp.json()
        token = data.get('data', {}).get('webSocketInfo', {}).get('token')
        return token

    def run(self):
        self.stream_id = self.get_stream_id()
        # self.token = self.get_token()  # 还是去浏览器复制吧
        self.token = 'QySqAXx92qxhCFbpr8XvKQYwxIsGTMNVEzjQW1ISr5dsVAcNT/jmkQPG4uY/T/YGAO2V5wYp/7bmKylYYO/Om9naz4ileC3LBVF+6O3i62Dvarwf2lF2vIzwWNYdDskjUC2JHIPfkOKbg482EGQajQ=='
        self.client(wss_url, self.stream_id, self.token).start()


if __name__ == '__main__':
    # https://live.kuaishou.com/u/xiaochang666666  输入快手id
    spider = Spider('xiaochang666666', Client)
    spider.run()
