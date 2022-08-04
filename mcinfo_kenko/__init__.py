import socket

from assets.simple_plugin import SimplePlugin
from module.client_api import ClientApi
from module.gocq_api import GocqApi
from module.server_api import ServerApi

from .motd import get_mcbe, get_mcje

error_msg = """参数不匹配，你是否想执行：
/mcinfo <host> <port>"""


class Mcinfo(SimplePlugin):

    def __init__(self, api: GocqApi, client: ClientApi, server: ServerApi):
        super().__init__(api, client, server)
        self.api = api
        self.client = client
        self.server = server
        self.name = 'Minecraft Information'
        self.description = 'Minecraft Information'
        self.version = '1.0.0'

    def on_message(self, message: dict):
        if message['post_type'] == 'message':
            msg: str = message['raw_message']
            if msg.startswith('/mcinfo'):
                msg = msg.removeprefix('/mcinfo').strip()
                msg_list = msg.split()
                if len(msg_list) != 2:
                    msg_list = msg.split(':')
                try:
                    recv_data = get_mcbe(msg_list[0], int(msg_list[1]))
                    send_data = ''
                    send_data += f'Motd: {recv_data.motd}' + '\n'
                    send_data += f'协议版本: {recv_data.protocol_version}' + '\n'
                    send_data += f'服务器版本: {recv_data.server_version}' + '\n'
                    send_data += f'在线人数: {recv_data.current_players_count}/{recv_data.max_players_count}' + '\n'
                    send_data += f'UniqueID: {recv_data.unique_id}' + '\n'
                    send_data += f'世界名称: {recv_data.world_name}' + '\n'
                    send_data += f'游戏模式: {recv_data.game_mode}' + '\n'
                    send_data += f'监听端口: {recv_data.port_ipv4}/{recv_data.port_ipv6}' + '\n'
                    send_data += f'延迟: {recv_data.delay}ms'
                    message['message'] = send_data
                except Exception:
                    try:
                        recv_data = get_mcje(msg_list[0], int(msg_list[1]))
                        send_data = ''
                        send_data += f'服务器名称: {recv_data.description}' + '\n'
                        send_data += f'协议版本: {recv_data.protocol_version}' + '\n'
                        send_data += f'服务器版本: {recv_data.server_version}' + '\n'
                        send_data += f'在线人数: {recv_data.current_players_count}/{recv_data.max_players_count}' + '\n'
                        send_data += f'延迟: {recv_data.delay}ms'
                        message['message'] = send_data
                    except (socket.timeout, socket.gaierror, ConnectionRefusedError):
                        message['message'] = '获取 Minecraft 信息失败'
                    except Exception:
                        message['message'] = error_msg
                self.api.send_msg(message)
                return False
        return True
