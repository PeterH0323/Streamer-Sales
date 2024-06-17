import base64
from datetime import datetime
import hashlib
import json
import os
from typing import Optional, Type

import jionlp as jio
import requests
from lagent.actions.base_action import BaseAction, tool_api
from lagent.actions.parser import BaseParser, JsonParser
from lagent.schema import ActionReturn, ActionStatusCode

from utils.web_configs import WEB_CONFIGS


class DeliveryTimeQueryAction(BaseAction):
    """快递时效查询插件，用于根据用户提出的收货地址查询到达期限"""

    def __init__(
        self,
        departure_place: str,
        delivery_company_name: str,
        description: Optional[dict] = None,
        parser: Type[BaseParser] = JsonParser,
        enable: bool = True,
    ) -> None:
        super().__init__(description, parser, enable)
        self.departure_place = departure_place  # 发货地

        # 天气查询
        self.weather_query_handler = WeatherQuery(departure_place, WEB_CONFIGS.AGENT_WEATHER_API_KEY)
        self.delivery_time_handler = DeliveryTimeQuery(delivery_company_name, WEB_CONFIGS.AGENT_DELIVERY_TIME_API_KEY)

    @tool_api
    def run(self, query: str) -> ActionReturn:
        """一个到货时间查询API。可以根据城市名查询到货时间信息。

        Args:
            query (:class:`str`): 需要查询的城市名。
        """

        # 获取文本中收货地，发货地后台设置
        # 防止 LLM 将城市识别错误，进行兜底
        city_info = jio.parse_location(query, town_village=True)
        city_name = city_info["city"]

        # 获取收货地代号 -> 天气
        destination_weather = self.weather_query_handler(city_name)

        # 获取发货地代号 -> 天气
        departure_weather = self.weather_query_handler(self.departure_place)

        # 获取到达时间
        delivery_time = self.delivery_time_handler(self.departure_place, city_name)

        final_str = (
            f"今天日期：{datetime.now().strftime('%m月%d日')}\n"
            f"收货地天气：{destination_weather.result[0]['content']}\n"
            f"发货地天气：{departure_weather.result[0]['content']}\n"
            f"物流信息：{delivery_time.result[0]['content']}\n"
            "回答突出“预计送达时间”和“收货地天气”，如果收货地或者发货地遇到暴雨暴雪等极端天气，须告知用户快递到达时间会有所增加。"
        )

        tool_return = ActionReturn(type=self.name)
        tool_return.result = [dict(type="text", content=final_str)]
        return tool_return


class WeatherQuery:
    """快递时效查询插件，用于根据用户提出的收货地址查询到达期限"""

    def __init__(
        self,
        departure_place: str,
        api_key: Optional[str] = None,
    ) -> None:
        self.departure_place = departure_place  # 发货地

        # 天气查询
        # api_key = os.environ.get("WEATHER_API_KEY", key)
        if api_key is None:
            raise ValueError("Please set Weather API key either in the environment as WEATHER_API_KEY")
        self.api_key = api_key
        self.location_query_url = "https://geoapi.qweather.com/v2/city/lookup"
        self.weather_query_url = "https://devapi.qweather.com/v7/weather/now"

    def parse_results(self, city_name: str, results: dict) -> str:
        """解析 API 返回的信息

        Args:
            results (dict): JSON 格式的 API 报文。

        Returns:
            str: 解析后的结果。
        """
        now = results["now"]
        data = (
            # f'数据观测时间: {now["obsTime"]}；'
            f"城市名: {city_name}；"
            f'温度: {now["temp"]}°C；'
            f'体感温度: {now["feelsLike"]}°C；'
            f'天气: {now["text"]}；'
            # f'风向: {now["windDir"]}，角度为 {now["wind360"]}°；'
            f'风力等级: {now["windScale"]}，风速为 {now["windSpeed"]} km/h；'
            f'相对湿度: {now["humidity"]}；'
            f'当前小时累计降水量: {now["precip"]} mm；'
            # f'大气压强: {now["pressure"]} 百帕；'
            f'能见度: {now["vis"]} km。'
        )
        return data

    def __call__(self, query):
        tool_return = ActionReturn()
        status_code, response = self.search_weather_with_city(query)
        if status_code == -1:
            tool_return.errmsg = response
            tool_return.state = ActionStatusCode.HTTP_ERROR
        elif status_code == 200:
            parsed_res = self.parse_results(query, response)
            tool_return.result = [dict(type="text", content=str(parsed_res))]
            tool_return.state = ActionStatusCode.SUCCESS
        else:
            tool_return.errmsg = str(status_code)
            tool_return.state = ActionStatusCode.API_ERROR
        return tool_return

    def search_weather_with_city(self, query: str):
        """根据城市名获取城市代号，然后进行天气查询

        Args:
            query (str): 城市名

        Returns:
            int: 天气接口调用状态码
            dict: 天气接口返回信息
        """

        # 获取城市代号
        try:
            city_code_response = requests.get(self.location_query_url, params={"key": self.api_key, "location": query})
        except Exception as e:
            return -1, str(e)

        if city_code_response.status_code != 200:
            return city_code_response.status_code, city_code_response.json()
        city_code_response = city_code_response.json()
        if len(city_code_response["location"]) == 0:
            return -1, "未查询到城市"
        city_code = city_code_response["location"][0]["id"]

        # 获取天气
        try:
            weather_response = requests.get(self.weather_query_url, params={"key": self.api_key, "location": city_code})
        except Exception as e:
            return -1, str(e)
        return weather_response.status_code, weather_response.json()


class DeliveryTimeQuery:
    def __init__(
        self,
        delivery_company_name: Optional[str] = "中通",
        api_key: Optional[str] = None,
    ) -> None:

        # 快递时效查询
        # api_key = os.environ.get("DELIVERY_TIME_API_KEY", key)
        if api_key is None or "," not in api_key:
            raise ValueError(
                'Please set Delivery time API key either in the environment as DELIVERY_TIME_API_KEY="${e_business_id},${api_key}"'
            )
        self.e_business_id = api_key.split(",")[0]
        self.api_key = api_key.split(",")[1]
        self.api_url = "http://api.kdniao.com/api/dist"  # 快递鸟
        self.china_location = jio.china_location_loader()
        # 快递鸟对应的
        DELIVERY_COMPANY_MAP = {
            "德邦": "DBL",
            "邮政": "EMS",
            "京东": "JD",
            "极兔速递": "JTSD",
            "顺丰": "SF",
            "申通": "STO",
            "韵达": "YD",
            "圆通": "YTO",
            "中通": "ZTO",
        }
        self.delivery_company_name = delivery_company_name
        self.delivery_company_id = DELIVERY_COMPANY_MAP[delivery_company_name]

    @staticmethod
    def data_md5(n):
        # md5加密
        md5 = hashlib.md5()
        md5.update(str(n).encode("utf-8"))
        return md5.hexdigest()

    def get_data_sign(self, n):
        # 签名
        md5Data = self.data_md5(json.dumps(n) + self.api_key)
        res = str(base64.b64encode(md5Data.encode("utf-8")), "utf-8")
        return res

    def get_city_detail(self, name):
        # 如果是城市名，使用第一个区名
        city_info = jio.parse_location(name, town_village=True)
        # china_location = jio.china_location_loader()

        county_name = ""
        for i in self.china_location[city_info["province"]][city_info["city"]].keys():
            if "区" == i[-1]:
                county_name = i
                break

        return {
            "province": city_info["province"],
            "city": city_info["city"],
            "county": county_name,
        }

    def get_params(self, send_city, receive_city):

        # 根据市查出省份和区名称
        send_city_info = self.get_city_detail(send_city)
        receive_city_info = self.get_city_detail(receive_city)

        # 预计送达时间接口文档；https://www.yuque.com/kdnjishuzhichi/dfcrg1/ynkmts0e5owsnpvu
        # 请求接口指令
        RequestType = "6004"
        # 组装应用级参数
        RequestData = {
            "ShipperCode": self.delivery_company_id,
            "ReceiveArea": receive_city_info["county"],
            "ReceiveCity": receive_city_info["city"],
            "ReceiveProvince": receive_city_info["province"],
            "SendArea": send_city_info["county"],
            "SendCity": send_city_info["city"],
            "SendProvince": send_city_info["province"],
        }
        # 组装系统级参数
        data = {
            "RequestData": json.dumps(RequestData),
            "RequestType": RequestType,
            "EBusinessID": self.e_business_id,
            "DataSign": self.get_data_sign(RequestData),
            "DataType": 2,
        }
        return data

    def parse_results(self, response):

        # 返回例子：
        # {
        # "EBusinessID" : "1000000",
        # "Data" : {
        #     "DeliveryTime" : "06月15日下午可达",
        #     "SendAddress" : null,
        #     "ReceiveArea" : "芙蓉区",
        #     "SendProvince" : "广东省",
        #     "ReceiveProvince" : "湖南省",
        #     "ShipperCode" : "DBL",
        #     "Hour" : "52h",
        #     "SendArea" : "白云区",
        #     "ReceiveAddress" : null,
        #     "SendCity" : "广州市",
        #     "ReceiveCity" : "长沙市"
        # },
        # "ResultCode" : "100",
        # "Success" : true
        # }

        response = response["Data"]
        data = (
            f'发货地点: {response["SendProvince"]} {response["SendCity"]}；'
            f'收货地点: {response["ReceiveProvince"]} {response["ReceiveCity"]}；'
            f'预计送达时间: {response["DeliveryTime"]}；'
            f"快递公司: {self.delivery_company_name}；"
            f'预计时效: {response["Hour"]}。'
        )
        return data

    def __call__(self, send_city, receive_city):
        tool_return = ActionReturn()
        try:
            res = requests.post(self.api_url, self.get_params(send_city, receive_city))
            status_code = res.status_code
            response = res.json()
        except Exception as e:
            tool_return.errmsg = str(e)
            tool_return.state = ActionStatusCode.API_ERROR
            return tool_return

        if status_code == 200:
            parsed_res = self.parse_results(response)
            tool_return.result = [dict(type="text", content=str(parsed_res))]
            tool_return.state = ActionStatusCode.SUCCESS
        else:
            tool_return.errmsg = str(status_code)
            tool_return.state = ActionStatusCode.API_ERROR
        return tool_return
