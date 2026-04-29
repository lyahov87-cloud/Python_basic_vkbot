import os
from dotenv import load_dotenv
import vk_api
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll

load_dotenv()

VK_TOKEN = os.getenv('VK_TOKEN')
KP_TOKEN = os.getenv('KP_TOKEN')
KP_HEADERS = {'X-API-KEY': KP_TOKEN, 'Accept': 'application/json'}

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)
upload = VkUpload(vk_session)
