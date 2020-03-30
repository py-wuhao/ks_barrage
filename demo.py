import random

import websocket

from barrage import MessageDecode

try:
    import thread
except ImportError:
    import _thread as thread
import time


def get_page_id():
    charset = "bjectSymhasOwnProp-0123456789ABCDEFGHIJKLMNQRTUVWXYZ_dfgiklquvxz"
    page_id = ''
    for _ in range(0, 16):
        page_id += random.choice(charset)
    page_id += "_"
    page_id += str(int(time.time() * 1000))
    return page_id


def on_message(ws, message):
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


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    part1 = [0x08, 0xC8, 0x01, 0x1A, 0x87, 0x01, 0x0A, 0x58]  # 不变的头
    token = "oobhv8gqySwoX93lhC+54lnNGE82yNFqH0BIy+Qe/HMMwettAiCOFwLEwkHQzv/Khhxtm5MNOpR0syxixhAyag=="
    part2 = [ord(c) for c in token]
    part3 = [0x12, 0x0B]  #
    stream_id = "7ph0KDj3QsE"
    part4 = [ord(c) for c in stream_id]
    part5 = [0x3A, 0x1E]
    page_id = get_page_id()
    part6 = [ord(c) for c in page_id]

    d = part1 + part2 + part3 + part4 + part5 + part6
    ws.send(d, websocket.ABNF.OPCODE_BINARY)

    def run():
        while True:
            time.sleep(20)
            # 发送心跳-当前时间戳-毫秒
            head = [0x08, 0x01, 0x1A, 0x07, 0x08]
            timestamp = int(time.time() * 1000)
            time_arr = MessageDecode.hex_(timestamp)
            heartbeat = head + time_arr
            ws.send(heartbeat, websocket.ABNF.OPCODE_BINARY)

    thread.start_new_thread(run, ())



if __name__ == "__main__":
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp("wss://live-ws-pg.kuaishou.com/websocket",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(skip_utf8_validation=True)
