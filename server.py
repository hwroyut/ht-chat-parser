import os
import sys
from scapy.all import sniff, IP, TCP
from threading import Thread
import time
from collections import deque
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio

app = FastAPI()

TARGET_IP = "8.213.133.1"
TARGET_PORT = 30031

time_detailed = time.strftime("%Y-%m-%d_%I-%M-%S")


connected_clients = set()


# it needed?
class MessageReceiver:
    def __init__(self):
        self.queue = deque()

    def add_message(self, message):
        self.queue.append(message)

    def get_message(self):
        if self.queue:
            return self.queue.popleft()
        return None


message_receiver = MessageReceiver()


async def broadcast_message(message: str):
    dead_clients = set()
    for client in connected_clients:
        try:
            await client.send_text(message)
        except Exception as e:
            print(f"client err: {e}")
            dead_clients.add(client)
    connected_clients.difference_update(dead_clients)


def log_message(message, time, type=0, user=""):
    type_str = ["", "월드", "길드", "팀", "귓속말", "협력", "모집", "에러"]
    payload = f"[{time}] <{type_str[type]}> {user}{': ' if user != "" else ""}{message}"
    if type == 7:
        # error
        pass
    else:
        # chat
        pass
    print(payload)
    asyncio.run(broadcast_message(payload))


def packet_handler(packet):
    if packet.haslayer(IP) and packet.haslayer(TCP):
        ip_src = packet[IP].src
        tcp_src_port = packet[TCP].sport
        tcp_dst_port = packet[TCP].dport

        time_now = time.strftime("%X")

        if ip_src == TARGET_IP and tcp_src_port == TARGET_PORT:
            if packet[TCP].payload:
                payload = bytes(packet[TCP].payload)
                # is human?
                if (payload.find(b"chat_qipao") == -1) and (
                    payload.find(b"Default") == -1
                ):
                    return

                # parse payload
                data = payload
                datalist = []
                end = False
                while True:
                    if data.find(b"\x00") == -1:
                        break
                    data = data[data.find(b"\x00") + 1 :]
                    if data.find(b"\x00") == -1:
                        end = True
                        break
                    if data[:1] != b"\x00":
                        datalist.append(data[: data.find(b"\x00")])
                    if end:
                        break
                pure_datalist = datalist
                # chat type
                chat_type = -1
                try:
                    for _ in range(2):
                        datalist = datalist[datalist.index(b"\x18") + 1 :]
                        chat_data = datalist[1]
                        whisper_data = datalist[2]
                        at_data = datalist[7]

                        if chat_data == b"\x01" or at_data == b"\x01":
                            chat_type = 1  # world
                            break
                        elif chat_data == b"\x08" or at_data == b"\x08":
                            chat_type = 2  # guild
                            break
                        elif chat_data == b"\x03" or at_data == b"\x03":
                            chat_type = 3  # team
                            break
                        elif whisper_data == b"\x10" or at_data == b"\x10":
                            chat_type = 4  # whisper
                            break
                        elif chat_data == b"\t" or at_data == b"\t":
                            chat_type = 5  # coop
                            break
                        elif chat_data == b"\x07":
                            chat_type = 6  # recruit
                            break

                    if chat_type == -1:
                        return

                    # parse text
                    if chat_type != 4:
                        text_data = datalist[: datalist.index(b"\x1e")]
                        text_data = list(reversed(text_data))
                        text_data = text_data[4]
                    else:
                        text_data = datalist[15]

                    # get username
                    for ballon, data in enumerate(datalist):
                        if b"Default" in data or b"chat_qipao" in data:
                            break

                    # trash not valid data
                    if ballon == len(datalist) - 1:
                        return
                    name_data = datalist[ballon:]
                    name_data = name_data[4]

                except Exception as e:
                    log_message(f"{e}", time=time_now, type=7)
                    return

                try:
                    text = text_data.decode("utf-8", errors="replace")
                    name = name_data.decode("utf-8", errors="replace")
                except Exception as e:
                    log_message(f"{e}", time=time_now, type=7)
                    return

                log_message(time=time_now, type=chat_type, user=name, message=text)


def start_sniffing():
    sniff(
        prn=packet_handler,
        filter=f"ip src {TARGET_IP} and tcp port {TARGET_PORT}",
        store=0,
    )


thread = Thread(target=start_sniffing)
thread.daemon = True
thread.start()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return FileResponse("index.html")


@app.get("/static/style.css")
def read_style():
    return FileResponse("style.css")


@app.get("/static/script.js")
def read_script():
    return FileResponse("script.js")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connected_clients.discard(websocket)


# python -m uvicorn server:app --reload
