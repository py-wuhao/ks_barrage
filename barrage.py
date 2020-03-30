# -*- coding: utf-8 -*-


"""
            101: "SC_HEARTBEAT_ACK",
            103: "SC_ERROR",
            105: "SC_INFO",
            300: "SC_ENTER_ROOM_ACK",
            310: "SC_FEED_PUSH",
            330: "SC_RED_PACK_FEED",
            340: "SC_LIVE_WATCHING_LIST",
            370: "SC_GUESS_OPENED",
            371: "SC_GUESS_CLOSED",
            412: "SC_RIDE_CHANGED",
            441: "SC_BET_CHANGED",
            442: "SC_BET_CLOSED"
"""


class MessageDecode:
    def __init__(self, buf):
        self.buf = buf
        self.pos = 0
        self.message = {}

    def __len__(self):
        return len(self.buf)

    def int_(self):
        res = 0
        i = 0
        while self.buf[self.pos] >= 128:
            res = res | (127 & self.buf[self.pos]) << 7 * i
            self.pos += 1
            i += 1
        res = res | self.buf[self.pos] << 7 * i
        self.pos += 1
        return res

    @staticmethod
    def hex_(n):
        res = []
        while n > 128:
            res.append(int((n & 127) | 128))
            n = n >> 7
        res.append(int(n))
        return res

    def bytes(self):
        e = self.int_()
        if e + self.pos > len(self.buf):
            raise Exception('长度不匹配')
        res = self.buf[self.pos:e + self.pos]
        self.pos += e
        return res

    def skip(self, e=None):
        """跳过多少字节"""
        if e is None:
            while self.pos < len(self.buf):
                if 128 & self.buf[self.pos] == 0:
                    self.pos += 1
                    return
                self.pos += 1
            return
        self.pos += e
        if self.pos >= len(self.buf):
            self.pos -= 1

    def skipType(self, e):
        if e == 0:
            self.skip()
        elif e == 1:
            self.skip(8)
        elif e == 2:
            self.skip(self.int_())
        elif e == 3:
            while True:
                e = 7 & self.int_()
                if 4 != e:
                    self.skipType(e)
        elif e == 5:
            self.skip(4)
        else:
            raise Exception('跳过类型错误')

    def decode(self):
        """只处理弹幕"""
        length = len(self)
        while self.pos < length:
            t = self.int_()
            tt = t >> 3
            if tt == 1:
                self.message['payloadType'] = self.int_()
                if self.message['payloadType'] != 310:  # 非弹幕
                    return False
            elif tt == 2:
                self.message['compressionType'] = self.int_()
            elif tt == 3:
                self.message['payload'] = self.bytes()
            else:
                self.skipType(t & 7)
        return True

    def string(self):
        e = self.bytes()
        n = len(e)
        if n < 1:
            return ""
        s = []
        t = 0
        while t < n:
            r = e[t]
            t += 1
            if r < 128:
                s.append(r)
            elif 191 < r < 224:
                s.append((31 & r) << 6 | 63 & e[t])
                t += 1
            elif 239 < r < 365:
                x = (7 & r) << 18 | (63 & e[t]) << 12
                t += 1
                y = (63 & e[t]) << 6
                t += 1
                z = 63 & e[t]
                t += 1
                r = (x | y | z) - 65536
                s.append(55296 + (r >> 10))
                s.append(56320 + (1023 & r))
            else:
                x = (15 & r) << 12
                y = (63 & e[t]) << 6
                t += 1
                z = 63 & e[t]
                t += 1
                s.append(x | y | z)
        string = ''
        for w in s:
            try:
                string += unichr(w)  # python2
            except:
                string += chr(w)  # python3
        return string

    def user_info_decode(self, r, l):
        c = self.pos + l
        m = {}
        while self.pos < c:
            t = self.int_()
            tt = t >> 3
            if tt == 1:
                m['principalId'] = self.string()
            elif tt == 2:
                m['userName'] = self.string()
            elif tt == 3:
                m['headUrl'] = self.string()
            else:
                self.skipType(t & 7)
        return m

    def web_like_feed_decode(self, r, l):
        c = self.pos + l
        m = {}
        while self.pos < c:
            t = self.int_()
            tt = t >> 3
            if tt == 1:
                m['id'] = self.string()
            elif tt == 2:
                m['user'] = self.user_info_decode(self.buf, self.int_())
            elif tt == 3:
                m['sortRank'] = self.int_()
            elif tt == 4:
                m['deviceHash'] = self.string()
            else:
                self.skipType(t & 7)
        return m

    def comment_decode(self, r, l):
        c = self.pos + l
        m = {}
        while self.pos < c:
            t = self.int_()
            tt = t >> 3
            if tt == 1:
                m['id'] = self.string()
            elif tt == 2:
                m['user'] = self.user_info_decode(self.buf, self.int_())
            elif tt == 3:
                m['content'] = self.string()
            elif tt == 4:
                m['deviceHash'] = self.string()
            elif tt == 5:
                m['sortRank'] = self.int_()
            elif tt == 6:
                m['color'] = self.string()
            elif tt ==7:
                m['showType']=self.int_()
            else:
                self.skipType(t & 7)
        return m

    def gift_decode(self, r, l):
        c = self.pos + l
        m = {}
        while self.pos < c:
            t = self.int_()
            tt = t >> 3
            if tt == 1:
                m['id'] = self.string()
            elif tt == 2:
                m['user'] = self.user_info_decode(self.buf, self.int_())
            elif tt == 3:
                m['time'] = self.int_()
            elif tt == 4:
                m['giftId'] = self.int_()
            elif tt == 5:
                m['sortRank'] = self.int_()
            elif tt == 6:
                m['mergeKey'] = self.string()
            elif tt == 7:
                m['batchSize'] = self.int_()
            elif tt == 8:
                m['comboCount'] = self.int_()
            elif tt == 9:
                m['rank'] = self.int_()
            elif tt == 10:
                m['expireDuration'] = self.int_()
            elif tt == 11:
                m['clientTimestamp'] = self.int_()
            elif tt == 12:
                m['slotDisplayDuration'] = self.int_()
            elif tt == 13:
                m['starLevel'] = self.int_()
            elif tt == 14:
                m['styleType'] = self.int_()
            elif tt == 15:
                m['liveAssistantType'] = self.int_()
            elif tt == 16:
                m['deviceHash'] = self.string()
            elif tt == 17:
                m['danmakuDisplay'] = self.bool()
            else:
                self.skipType(t & 7)
        return m

    def feed_decode(self):
        self.pos = 0
        self.buf = self.message['payload']
        length = len(self.buf)
        while self.pos < length:
            t = self.int_()
            tt = t >> 3
            if tt == 1:
                self.message['displayWatchingCount'] = self.string()
                # print("观看人数：" + self.message['displayWatchingCount'])
            elif tt == 2:
                self.message['displayLikeCount'] = self.string()
                # print("点赞数：" + self.message['displayLikeCount'])
            elif tt == 5:
                if not self.message.get('user'):
                    self.message['user'] = []
                self.message['user'].append(self.comment_decode(self.buf, self.int_()))

            elif tt==6:
                self.string()
            elif tt==8:
                self.web_like_feed_decode(self.buf, self.int_())

            elif tt == 9:  # 礼物
                if not self.message.get('gift'):
                    self.message['gift'] = []
                self.message['gift'].append(self.gift_decode(self.buf, self.int_()))


